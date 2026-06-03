"""
MySQL 数据库连接器（带连接池支持）
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

import pymysql
import pymysql.cursors

from .base import DatabaseBase, DatabaseConfig, QueryResult
from .pool import ConnectionPool, PoolConfig


class MySQLConnectionPool(ConnectionPool):
    """MySQL 连接池"""
    
    def __init__(self, config: DatabaseConfig, pool_config: Optional[PoolConfig] = None):
        super().__init__(pool_config or PoolConfig())
        self.db_config = config
    
    async def _create_connection(self) -> Any:
        """创建 MySQL 连接"""
        conn_params = {
            "host": self.db_config.host,
            "port": self.db_config.port,
            "database": self.db_config.database,
            "user": self.db_config.user,
            "password": self.db_config.password,
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
        }
        
        if self.db_config.options:
            conn_params.update(self.db_config.options)
        
        # 在异步上下文中运行同步操作
        loop = asyncio.get_event_loop()
        conn = await loop.run_in_executor(None, lambda: pymysql.connect(**conn_params))
        
        return conn
    
    async def _close_connection(self, conn: Any) -> None:
        """关闭 MySQL 连接"""
        try:
            conn.close()
        except Exception:
            pass
    
    async def _validate_connection(self, conn: Any) -> bool:
        """验证 MySQL 连接"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return result["1"] == 1
        except Exception:
            return False


class MySQLDatabase(DatabaseBase):
    """MySQL 数据库连接器（带连接池）"""
    
    def __init__(self, config: DatabaseConfig, pool_config: Optional[PoolConfig] = None):
        """
        初始化 MySQL 连接器
        
        Args:
            config: 数据库配置
            pool_config: 连接池配置
        """
        super().__init__(config)
        self._pool = MySQLConnectionPool(config, pool_config)
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
                # 创建游标
                cursor = conn.cursor()
                
                # 执行查询
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # 获取结果
                if cursor.description:
                    # SELECT 查询
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    # 转换为元组列表
                    if rows and isinstance(rows[0], dict):
                        rows = [tuple(row.values()) for row in rows]
                    
                    row_count = len(rows)
                else:
                    # 非 SELECT 查询
                    columns = []
                    rows = []
                    row_count = cursor.rowcount
                
                execution_time = time.time() - start_time
                cursor.close()
                
                return QueryResult(
                    columns=columns,
                    rows=rows,
                    row_count=row_count,
                    execution_time=execution_time
                )
                
            except pymysql.Error as e:
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
                cursor = conn.cursor()
                
                # 构建 EXPLAIN 语句
                explain_sql = f"EXPLAIN"
                if analyze:
                    explain_sql += " ANALYZE"
                explain_sql += f" {sql}"
                
                # 执行 EXPLAIN
                cursor.execute(explain_sql)
                result = cursor.fetchall()
                
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
                    
                    cursor.close()
                    return "\n".join(lines)
                else:
                    cursor.close()
                    return "No explain plan available"
                
            except pymysql.Error as e:
                return f"Failed to generate explain plan: {e}"
    
    async def get_schema(self) -> Dict[str, Any]:
        """
        获取数据库 schema 信息
        
        Returns:
            Dict: 数据库 schema 信息
        """
        async with self._pool.connection() as conn:
            try:
                cursor = conn.cursor()
                
                # 获取数据库信息
                cursor.execute("SELECT DATABASE(), USER(), VERSION()")
                db_info = cursor.fetchone()
                
                # 获取所有表
                cursor.execute("""
                    SELECT table_name, table_type, engine, table_rows
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                    ORDER BY table_name
                """)
                tables = []
                for row in cursor.fetchall():
                    tables.append({
                        "name": row["table_name"],
                        "type": row["table_type"],
                        "engine": row["engine"],
                        "rows": row["table_rows"]
                    })
                
                cursor.close()
                
                return {
                    "database": db_info["DATABASE()"],
                    "user": db_info["USER()"],
                    "version": db_info["VERSION()"],
                    "tables": tables
                }
                
            except pymysql.Error as e:
                return {"error": f"Failed to get schema: {e}"}
    
    async def get_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            List[str]: 表名列表
        """
        async with self._pool.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TABLE_NAME
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                    ORDER BY TABLE_NAME
                """)
                tables = [row["TABLE_NAME"] for row in cursor.fetchall()]
                cursor.close()
                return tables
                
            except pymysql.Error as e:
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
                cursor = conn.cursor()
                
                # 获取列信息
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE() AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "name": row["COLUMN_NAME"],
                        "type": row["DATA_TYPE"],
                        "nullable": row["IS_NULLABLE"] == "YES",
                        "default": row["COLUMN_DEFAULT"],
                        "key": row["COLUMN_KEY"]
                    })
                
                # 获取索引信息
                cursor.execute("""
                    SELECT INDEX_NAME, group_concat(COLUMN_NAME order by SEQ_IN_INDEX) as columns, NON_UNIQUE
                    FROM information_schema.statistics
                    WHERE table_schema = DATABASE() AND table_name = %s
                    GROUP BY INDEX_NAME, NON_UNIQUE
                """, (table_name,))
                
                indexes = []
                for row in cursor.fetchall():
                    indexes.append({
                        "name": row["INDEX_NAME"],
                        "columns": row["columns"].split(","),
                        "unique": row["NON_UNIQUE"] == 0
                    })
                
                # 获取约束信息
                cursor.execute("""
                    SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
                    FROM information_schema.table_constraints
                    WHERE table_schema = DATABASE() AND table_name = %s
                """, (table_name,))
                
                constraints = []
                for row in cursor.fetchall():
                    constraints.append({
                        "name": row["CONSTRAINT_NAME"],
                        "type": row["CONSTRAINT_TYPE"]
                    })
                
                cursor.close()
                
                return {
                    "table": table_name,
                    "columns": columns,
                    "indexes": indexes,
                    "constraints": constraints
                }
                
            except pymysql.Error as e:
                return {"error": f"Failed to get table schema: {e}"}
    
    async def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            async with self._pool.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                return result["1"] == 1
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