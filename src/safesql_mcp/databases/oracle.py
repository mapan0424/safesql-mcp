"""
Oracle 数据库连接器
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

import oracledb

from .base import DatabaseBase, DatabaseConfig, QueryResult


class OracleDatabase(DatabaseBase):
    """Oracle 数据库连接器"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化 Oracle 连接器
        
        Args:
            config: 数据库配置
        """
        super().__init__(config)
        self._connection = None
        self._cursor = None
        
        # Oracle 特定配置
        self._dsn = config.options.get("dsn") if config.options else None
        self._service_name = config.options.get("service_name") if config.options else None
        self._sid = config.options.get("sid") if config.options else None
    
    def _build_dsn(self) -> str:
        """构建 DSN 连接字符串"""
        if self._dsn:
            return self._dsn
        
        # 使用 service_name 或 sid 构建 DSN
        if self._service_name:
            return f"{self.config.host}:{self.config.port}/{self._service_name}"
        elif self._sid:
            return f"{self.config.host}:{self.config.port}:{self._sid}"
        else:
            # 默认使用 service_name 格式
            return f"{self.config.host}:{self.config.port}/{self.config.database}"
    
    async def connect(self) -> None:
        """建立 Oracle 连接"""
        try:
            # 构建 DSN
            dsn = self._build_dsn()
            
            # 构建连接参数
            conn_params = {
                "user": self.config.user,
                "password": self.config.password,
                "dsn": dsn,
            }
            
            # 添加额外选项
            if self.config.options:
                # 过滤掉自定义选项
                standard_options = {
                    "mode", "events", "purity", "cclass",
                    "matchanytag", "tag", "stmtcachesize",
                    "edition", "appcontext", "shardingkey",
                    "supershardingkey", "tcp_connect_timeout"
                }
                for key, value in self.config.options.items():
                    if key.lower() in standard_options:
                        conn_params[key] = value
            
            # 建立连接
            self._connection = oracledb.connect(**conn_params)
            self._cursor = self._connection.cursor()
            self._is_connected = True
            
        except oracledb.Error as e:
            raise ConnectionError(f"Failed to connect to Oracle: {e}")
    
    async def disconnect(self) -> None:
        """关闭 Oracle 连接"""
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
            
        except oracledb.Error as e:
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
            # Oracle 使用 DBMS_XPLAN 获取执行计划
            # 首先解释 SQL
            explain_sql = f"EXPLAIN PLAN FOR {sql}"
            self._cursor.execute(explain_sql)
            
            # 获取执行计划
            if analyze:
                plan_sql = """
                    SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY(
                        NULL, NULL, 'ALLSTATS LAST'
                    ))
                """
            else:
                plan_sql = """
                    SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY(
                        NULL, NULL, 'TYPICAL'
                    ))
                """
            
            self._cursor.execute(plan_sql)
            result = self._cursor.fetchall()
            
            # 格式化结果
            plan_lines = [row[0] for row in result]
            return "\n".join(plan_lines)
            
        except oracledb.Error as e:
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
            self._cursor.execute("""
                SELECT 
                    SYS_CONTEXT('USERENV', 'DB_NAME') as db_name,
                    SYS_CONTEXT('USERENV', 'CURRENT_USER') as current_user,
                    BANNER as version
                FROM V$VERSION 
                WHERE ROWNUM = 1
            """)
            db_info = self._cursor.fetchone()
            
            # 获取所有 schema（用户）
            self._cursor.execute("""
                SELECT USERNAME 
                FROM DBA_USERS 
                WHERE ACCOUNT_STATUS = 'OPEN'
                ORDER BY USERNAME
            """)
            schemas = [row[0] for row in self._cursor.fetchall()]
            
            # 获取当前用户的表
            self._cursor.execute("""
                SELECT TABLE_NAME 
                FROM USER_TABLES 
                ORDER BY TABLE_NAME
            """)
            tables = [{"schema": db_info[1], "name": row[0], "type": "TABLE"} for row in self._cursor.fetchall()]
            
            # 获取视图
            self._cursor.execute("""
                SELECT VIEW_NAME 
                FROM USER_VIEWS 
                ORDER BY VIEW_NAME
            """)
            views = [{"schema": db_info[1], "name": row[0], "type": "VIEW"} for row in self._cursor.fetchall()]
            
            return {
                "database": db_info[0],
                "user": db_info[1],
                "version": db_info[2],
                "schemas": schemas,
                "tables": tables + views
            }
            
        except oracledb.Error as e:
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
                SELECT TABLE_NAME 
                FROM USER_TABLES 
                ORDER BY TABLE_NAME
            """)
            return [row[0] for row in self._cursor.fetchall()]
            
        except oracledb.Error as e:
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
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    NULLABLE,
                    DATA_DEFAULT,
                    DATA_LENGTH,
                    DATA_PRECISION,
                    DATA_SCALE
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = :table_name
                ORDER BY COLUMN_ID
            """, {"table_name": table_name})
            
            columns = []
            for row in self._cursor.fetchall():
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "Y",
                    "default": row[3],
                    "length": row[4],
                    "precision": row[5],
                    "scale": row[6]
                })
            
            # 获取索引信息
            self._cursor.execute("""
                SELECT 
                    INDEX_NAME,
                    UNIQUENESS
                FROM USER_INDEXES 
                WHERE TABLE_NAME = :table_name
                ORDER BY INDEX_NAME
            """, {"table_name": table_name})
            
            indexes = []
            for row in self._cursor.fetchall():
                # 获取索引列
                self._cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM USER_IND_COLUMNS
                    WHERE INDEX_NAME = :index_name
                    ORDER BY COLUMN_POSITION
                """, {"index_name": row[0]})
                
                index_columns = [col[0] for col in self._cursor.fetchall()]
                
                indexes.append({
                    "name": row[0],
                    "unique": row[1] == "UNIQUE",
                    "columns": index_columns
                })
            
            # 获取约束信息
            self._cursor.execute("""
                SELECT 
                    CONSTRAINT_NAME,
                    CONSTRAINT_TYPE
                FROM USER_CONSTRAINTS 
                WHERE TABLE_NAME = :table_name
                ORDER BY CONSTRAINT_NAME
            """, {"table_name": table_name})
            
            constraints = []
            for row in self._cursor.fetchall():
                constraints.append({
                    "name": row[0],
                    "type": row[1]
                })
            
            return {
                "table": table_name,
                "columns": columns,
                "indexes": indexes,
                "constraints": constraints
            }
            
        except oracledb.Error as e:
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
            self._cursor.execute("SELECT 1 FROM DUAL")
            result = self._cursor.fetchone()
            
            return result[0] == 1
            
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