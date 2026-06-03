"""
PostgreSQL 异步数据库连接器（使用 asyncpg）
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

import asyncpg

from .base import DatabaseBase, DatabaseConfig, QueryResult
from .pool import ConnectionPool, PoolConfig


class AsyncPostgreSQLConnectionPool(ConnectionPool):
    """PostgreSQL 异步连接池"""
    
    def __init__(self, config: DatabaseConfig, pool_config: Optional[PoolConfig] = None):
        super().__init__(pool_config or PoolConfig())
        self.db_config = config
        self._async_pool: Optional[asyncpg.Pool] = None
    
    async def _create_connection(self) -> Any:
        """创建 PostgreSQL 异步连接"""
        if self._async_pool is None:
            # 创建 asyncpg 连接池
            self._async_pool = await asyncpg.create_pool(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                command_timeout=self.config.timeout,
                **(self.db_config.options or {})
            )
        
        # 从池中获取连接
        return await self._async_pool.acquire()
    
    async def _close_connection(self, conn: Any) -> None:
        """关闭 PostgreSQL 异步连接"""
        if self._async_pool:
            await self._async_pool.release(conn)
    
    async def _validate_connection(self, conn: Any) -> bool:
        """验证 PostgreSQL 异步连接"""
        try:
            result = await conn.fetchval("SELECT 1")
            return result == 1
        except Exception:
            return False
    
    async def close(self) -> None:
        """关闭连接池"""
        if self._async_pool:
            await self._async_pool.close()
            self._async_pool = None


class AsyncPostgreSQLDatabase(DatabaseBase):
    """PostgreSQL 异步数据库连接器"""
    
    def __init__(self, config: DatabaseConfig, pool_config: Optional[PoolConfig] = None):
        """
        初始化 PostgreSQL 异步连接器
        
        Args:
            config: 数据库配置
            pool_config: 连接池配置
        """
        super().__init__(config)
        self._pool = AsyncPostgreSQLConnectionPool(config, pool_config)
        self._is_connected = True  # 连接池模式下始终为 True
    
    async def connect(self) -> None:
        """建立 PostgreSQL 连接（连接池模式下为空操作）"""
        pass
    
    async def disconnect(self) -> None:
        """关闭 PostgreSQL 连接"""
        await self._pool.close()
        self._is_connected = False
    
    async def execute(self, sql: str, params: Optional[Tuple] = None) -> QueryResult:
        """
        执行 SQL 查询
        
        Args:
            sql: SQL 语句
            params: 查询参数
            
        Returns:
            QueryResult: 查询结果
        """
        start_time = time.time()
        
        async with self._pool.connection() as conn:
            try:
                # 执行查询
                if params:
                    # 将参数转换为 asyncpg 格式
                    result = await conn.fetch(sql, *params)
                else:
                    result = await conn.fetch(sql)
                
                # 获取结果
                if result:
                    # SELECT 查询
                    columns = list(result[0].keys())
                    rows = [tuple(row.values()) for row in result]
                    row_count = len(rows)
                else:
                    # 非 SELECT 查询或空结果
                    columns = []
                    rows = []
                    row_count = 0
                
                execution_time = time.time() - start_time
                
                return QueryResult(
                    columns=columns,
                    rows=rows,
                    row_count=row_count,
                    execution_time=execution_time
                )
                
            except asyncpg.PostgresError as e:
                raise RuntimeError(f"Failed to execute SQL: {e}")
    
    async def explain(self, sql: str, analyze: bool = False) -> str:
        """
        生成 SQL 执行计划
        
        Args:
            sql: SQL 语句
            analyze: 是否包含实际执行统计
            
        Returns:
            str: EXPLAIN 执行计划
        """
        async with self._pool.connection() as conn:
            try:
                # 构建 EXPLAIN 语句
                explain_sql = f"EXPLAIN"
                if analyze:
                    explain_sql += " ANALYZE"
                explain_sql += f" {sql}"
                
                # 执行 EXPLAIN
                result = await conn.fetch(explain_sql)
                
                # 格式化结果
                plan_lines = [row[0] for row in result]
                return "\n".join(plan_lines)
                
            except asyncpg.PostgresError as e:
                return f"Failed to generate explain plan: {e}"
    
    async def get_schema(self) -> Dict[str, Any]:
        """
        获取数据库 schema 信息
        
        Returns:
            Dict: 数据库 schema 信息
        """
        async with self._pool.connection() as conn:
            try:
                # 获取所有 schema
                schemas = await conn.fetch("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY schema_name
                """)
                schema_list = [row[0] for row in schemas]
                
                # 获取所有表
                tables = await conn.fetch("""
                    SELECT table_schema, table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY table_schema, table_name
                """)
                table_list = []
                for row in tables:
                    table_list.append({
                        "schema": row[0],
                        "name": row[1],
                        "type": row[2]
                    })
                
                # 获取数据库信息
                db_info = await conn.fetchrow('SELECT current_database(), current_user, version()')
                
                return {
                    "database": db_info[0],
                    "user": db_info[1],
                    "version": db_info[2],
                    "schemas": schema_list,
                    "tables": table_list
                }
                
            except asyncpg.PostgresError as e:
                return {"error": f"Failed to get schema: {e}"}
    
    async def get_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            List[str]: 表名列表
        """
        async with self._pool.connection() as conn:
            try:
                result = await conn.fetch("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                return [row[0] for row in result]
                
            except asyncpg.PostgresError as e:
                return []
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            Dict: 表结构信息
        """
        async with self._pool.connection() as conn:
            try:
                # 获取列信息
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = $1
                    ORDER BY ordinal_position
                """, table_name)
                
                column_list = []
                for row in columns:
                    column_list.append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3]
                    })
                
                # 获取索引信息
                indexes = await conn.fetch("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public' AND tablename = $1
                """, table_name)
                
                index_list = []
                for row in indexes:
                    index_list.append({
                        "name": row[0],
                        "definition": row[1]
                    })
                
                # 获取约束信息
                constraints = await conn.fetch("""
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'public' AND table_name = $1
                """, table_name)
                
                constraint_list = []
                for row in constraints:
                    constraint_list.append({
                        "name": row[0],
                        "type": row[1]
                    })
                
                return {
                    "table": table_name,
                    "columns": column_list,
                    "indexes": index_list,
                    "constraints": constraint_list
                }
                
            except asyncpg.PostgresError as e:
                return {"error": f"Failed to get table schema: {e}"}
    
    async def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            async with self._pool.connection() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception:
            return False
    
    async def _rollback(self) -> None:
        """回滚事务（连接池模式下为空操作）"""
        pass
    
    async def _commit(self) -> None:
        """提交事务（连接池模式下为空操作）"""
        pass
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        return self._pool.stats()