"""
MySQL 异步数据库连接器（使用 aiomysql）
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

import aiomysql

from .base import DatabaseBase, DatabaseConfig, QueryResult
from .pool import ConnectionPool, PoolConfig


class AsyncMySQLConnectionPool(ConnectionPool):
    """MySQL 异步连接池"""
    
    def __init__(self, config: DatabaseConfig, pool_config: Optional[PoolConfig] = None):
        super().__init__(pool_config or PoolConfig())
        self.db_config = config
        self._async_pool: Optional[aiomysql.Pool] = None
    
    async def _create_connection(self) -> Any:
        """创建 MySQL 异步连接"""
        if self._async_pool is None:
            # 创建 aiomysql 连接池
            self._async_pool = await aiomysql.create_pool(
                host=self.db_config.host,
                port=self.db_config.port,
                db=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password,
                charset="utf8mb4",
                minsize=self.config.min_size,
                maxsize=self.config.max_size,
                connect_timeout=self.config.timeout,
                **(self.db_config.options or {})
            )
        
        # 从池中获取连接
        return await self._async_pool.acquire()
    
    async def _close_connection(self, conn: Any) -> None:
        """关闭 MySQL 异步连接"""
        if self._async_pool:
            self._async_pool.release(conn)
    
    async def _validate_connection(self, conn: Any) -> bool:
        """验证 MySQL 异步连接"""
        try:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                return result[0] == 1
        except Exception:
            return False
    
    async def close(self) -> None:
        """关闭连接池"""
        if self._async_pool:
            self._async_pool.close()
            await self._async_pool.wait_closed()
            self._async_pool = None


class AsyncMySQLDatabase(DatabaseBase):
    """MySQL 异步数据库连接器"""
    
    def __init__(self, config: DatabaseConfig, pool_config: Optional[PoolConfig] = None):
        """
        初始化 MySQL 异步连接器
        
        Args:
            config: 数据库配置
            pool_config: 连接池配置
        """
        super().__init__(config)
        self._pool = AsyncMySQLConnectionPool(config, pool_config)
        self._is_connected = True  # 连接池模式下始终为 True
    
    async def connect(self) -> None:
        """建立 MySQL 连接（连接池模式下为空操作）"""
        pass
    
    async def disconnect(self) -> None:
        """关闭 MySQL 连接"""
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
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # 执行查询
                    if params:
                        await cursor.execute(sql, params)
                    else:
                        await cursor.execute(sql)
                    
                    # 获取结果
                    if cursor.description:
                        # SELECT 查询
                        rows = await cursor.fetchall()
                        columns = list(rows[0].keys()) if rows else []
                        row_count = len(rows)
                        
                        # 转换为元组列表
                        rows = [tuple(row.values()) for row in rows]
                    else:
                        # 非 SELECT 查询
                        columns = []
                        rows = []
                        row_count = cursor.rowcount
                    
                    execution_time = time.time() - start_time
                    
                    return QueryResult(
                        columns=columns,
                        rows=rows,
                        row_count=row_count,
                        execution_time=execution_time
                    )
                
            except aiomysql.Error as e:
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
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # 构建 EXPLAIN 语句
                    explain_sql = f"EXPLAIN"
                    if analyze:
                        explain_sql += " ANALYZE"
                    explain_sql += f" {sql}"
                    
                    # 执行 EXPLAIN
                    await cursor.execute(explain_sql)
                    result = await cursor.fetchall()
                    
                    # 格式化结果
                    if result:
                        # 获取列名
                        columns = list(result[0].keys())
                        
                        # 构建表格
                        lines = []
                        lines.append(" | ".join(columns))
                        lines.append(" | ".join(["---"] * len(columns)))
                        
                        for row in result:
                            line = " | ".join(str(row[col]) for col in columns)
                            lines.append(line)
                        
                        return "\n".join(lines)
                    else:
                        return "No explain plan available"
                
            except aiomysql.Error as e:
                return f"Failed to generate explain plan: {e}"
    
    async def get_schema(self) -> Dict[str, Any]:
        """
        获取数据库 schema 信息
        
        Returns:
            Dict: 数据库 schema 信息
        """
        async with self._pool.connection() as conn:
            try:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # 获取数据库信息
                    await cursor.execute("SELECT DATABASE(), USER(), VERSION()")
                    db_info = await cursor.fetchone()
                    
                    # 获取所有表
                    await cursor.execute("""
                        SELECT table_name, table_type, engine, table_rows
                        FROM information_schema.tables
                        WHERE table_schema = DATABASE()
                        ORDER BY table_name
                    """)
                    tables = []
                    for row in await cursor.fetchall():
                        tables.append({
                            "name": row["table_name"],
                            "type": row["table_type"],
                            "engine": row["engine"],
                            "rows": row["table_rows"]
                        })
                    
                    return {
                        "database": db_info["DATABASE()"],
                        "user": db_info["USER()"],
                        "version": db_info["VERSION()"],
                        "tables": tables
                    }
                
            except aiomysql.Error as e:
                return {"error": f"Failed to get schema: {e}"}
    
    async def get_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            List[str]: 表名列表
        """
        async with self._pool.connection() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        SELECT TABLE_NAME
                        FROM information_schema.tables
                        WHERE table_schema = DATABASE()
                        ORDER BY TABLE_NAME
                    """)
                    return [row[0] for row in await cursor.fetchall()]
                
            except aiomysql.Error as e:
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
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # 获取列信息
                    await cursor.execute("""
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY
                        FROM information_schema.columns
                        WHERE table_schema = DATABASE() AND table_name = %s
                        ORDER BY ordinal_position
                    """, (table_name,))
                    
                    columns = []
                    for row in await cursor.fetchall():
                        columns.append({
                            "name": row["COLUMN_NAME"],
                            "type": row["DATA_TYPE"],
                            "nullable": row["IS_NULLABLE"] == "YES",
                            "default": row["COLUMN_DEFAULT"],
                            "key": row["COLUMN_KEY"]
                        })
                    
                    # 获取索引信息
                    await cursor.execute("""
                        SELECT INDEX_NAME, group_concat(COLUMN_NAME order by SEQ_IN_INDEX) as columns, NON_UNIQUE
                        FROM information_schema.statistics
                        WHERE table_schema = DATABASE() AND table_name = %s
                        GROUP BY INDEX_NAME, NON_UNIQUE
                    """, (table_name,))
                    
                    indexes = []
                    for row in await cursor.fetchall():
                        indexes.append({
                            "name": row["INDEX_NAME"],
                            "columns": row["columns"].split(","),
                            "unique": row["NON_UNIQUE"] == 0
                        })
                    
                    # 获取约束信息
                    await cursor.execute("""
                        SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
                        FROM information_schema.table_constraints
                        WHERE table_schema = DATABASE() AND table_name = %s
                    """, (table_name,))
                    
                    constraints = []
                    for row in await cursor.fetchall():
                        constraints.append({
                            "name": row["CONSTRAINT_NAME"],
                            "type": row["CONSTRAINT_TYPE"]
                        })
                    
                    return {
                        "table": table_name,
                        "columns": columns,
                        "indexes": indexes,
                        "constraints": constraints
                    }
                
            except aiomysql.Error as e:
                return {"error": f"Failed to get table schema: {e}"}
    
    async def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            async with self._pool.connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    return result[0] == 1
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