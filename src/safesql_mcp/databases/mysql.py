"""
MySQL 数据库连接器
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

import pymysql
import pymysql.cursors

from .base import DatabaseBase, DatabaseConfig, QueryResult


class MySQLDatabase(DatabaseBase):
    """MySQL 数据库连接器"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化 MySQL 连接器
        
        Args:
            config: 数据库配置
        """
        super().__init__(config)
        self._connection = None
        self._cursor = None
    
    async def connect(self) -> None:
        """建立 MySQL 连接"""
        try:
            # 构建连接参数
            conn_params = {
                "host": self.config.host,
                "port": self.config.port,
                "database": self.config.database,
                "user": self.config.user,
                "password": self.config.password,
                "charset": "utf8mb4",
                "cursorclass": pymysql.cursors.DictCursor,
            }
            
            # 添加额外选项
            if self.config.options:
                conn_params.update(self.config.options)
            
            # 建立连接
            self._connection = pymysql.connect(**conn_params)
            self._cursor = self._connection.cursor()
            self._is_connected = True
            
        except pymysql.Error as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}")
    
    async def disconnect(self) -> None:
        """关闭 MySQL 连接"""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        
        if self._connection:
            self._connection.close()
            self._connection = None
        
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
        if not self._is_connected:
            await self.connect()
        
        start_time = time.time()
        
        try:
            # 执行查询
            if params:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)
            
            # 获取结果
            if self._cursor.description:
                # SELECT 查询
                columns = [desc[0] for desc in self._cursor.description]
                rows = self._cursor.fetchall()
                
                # 转换为元组列表
                if rows and isinstance(rows[0], dict):
                    rows = [tuple(row.values()) for row in rows]
                
                row_count = len(rows)
            else:
                # 非 SELECT 查询
                columns = []
                rows = []
                row_count = self._cursor.rowcount
            
            execution_time = time.time() - start_time
            
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
        if not self._is_connected:
            await self.connect()
        
        try:
            # 构建 EXPLAIN 语句
            explain_sql = f"EXPLAIN"
            if analyze:
                explain_sql += " ANALYZE"
            explain_sql += f" {sql}"
            
            # 执行 EXPLAIN
            self._cursor.execute(explain_sql)
            result = self._cursor.fetchall()
            
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
            
        except pymysql.Error as e:
            return f"Failed to generate explain plan: {e}"
    
    async def get_schema(self) -> Dict[str, Any]:
        """
        获取数据库 schema 信息
        
        Returns:
            Dict: 数据库 schema 信息
        """
        if not self._is_connected:
            await self.connect()
        
        try:
            # 获取数据库信息
            self._cursor.execute("SELECT DATABASE(), USER(), VERSION()")
            db_info = self._cursor.fetchone()
            
            # 获取所有表
            self._cursor.execute("""
                SELECT table_name, table_type, engine, table_rows
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                ORDER BY table_name
            """)
            tables = []
            for row in self._cursor.fetchall():
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
            
        except pymysql.Error as e:
            return {"error": f"Failed to get schema: {e}"}
    
    async def get_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            List[str]: 表名列表
        """
        if not self._is_connected:
            await self.connect()
        
        try:
            self._cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                ORDER BY table_name
            """)
            return [row["table_name"] for row in self._cursor.fetchall()]
            
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
        if not self._is_connected:
            await self.connect()
        
        try:
            # 获取列信息
            self._cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default, column_key
                FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = []
            for row in self._cursor.fetchall():
                columns.append({
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                    "key": row["column_key"]
                })
            
            # 获取索引信息
            self._cursor.execute("""
                SELECT index_name, group_concat(column_name order by seq_in_index) as columns, non_unique
                FROM information_schema.statistics
                WHERE table_schema = DATABASE() AND table_name = %s
                GROUP BY index_name, non_unique
            """, (table_name,))
            
            indexes = []
            for row in self._cursor.fetchall():
                indexes.append({
                    "name": row["index_name"],
                    "columns": row["columns"].split(","),
                    "unique": row["non_unique"] == 0
                })
            
            # 获取约束信息
            self._cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_schema = DATABASE() AND table_name = %s
            """, (table_name,))
            
            constraints = []
            for row in self._cursor.fetchall():
                constraints.append({
                    "name": row["constraint_name"],
                    "type": row["constraint_type"]
                })
            
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
            if not self._is_connected:
                await self.connect()
            
            # 执行简单查询测试连接
            self._cursor.execute("SELECT 1")
            result = self._cursor.fetchone()
            
            return result["1"] == 1
            
        except Exception:
            return False
    
    async def _rollback(self) -> None:
        """回滚事务"""
        if self._connection:
            self._connection.rollback()
    
    async def _commit(self) -> None:
        """提交事务"""
        if self._connection:
            self._connection.commit()