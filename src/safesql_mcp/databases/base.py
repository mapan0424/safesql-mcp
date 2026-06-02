"""
数据库基类：定义数据库连接和操作的通用接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
import asyncio


@dataclass
class DatabaseConfig:
    """数据库配置"""
    type: str
    host: str
    port: int
    database: str
    user: str
    password: str
    options: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "options": self.options or {}
        }


@dataclass
class QueryResult:
    """查询结果"""
    columns: List[str]
    rows: List[Tuple[Any, ...]]
    row_count: int
    execution_time: float
    explain_plan: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "columns": self.columns,
            "rows": [list(row) for row in self.rows],
            "row_count": self.row_count,
            "execution_time": self.execution_time,
            "explain_plan": self.explain_plan
        }
    
    def to_markdown(self) -> str:
        """转换为 Markdown 表格"""
        if not self.rows:
            return "查询结果为空"
        
        # 构建表头
        header = "| " + " | ".join(self.columns) + " |"
        separator = "| " + " | ".join(["---"] * len(self.columns)) + " |"
        
        # 构建数据行
        rows = []
        for row in self.rows:
            row_str = "| " + " | ".join(str(cell) for cell in row) + " |"
            rows.append(row_str)
        
        # 组合表格
        table = "\n".join([header, separator] + rows)
        
        # 添加统计信息
        stats = f"\n\n**统计信息：**\n"
        stats += f"- 列数：{len(self.columns)}\n"
        stats += f"- 行数：{self.row_count}\n"
        stats += f"- 执行时间：{self.execution_time:.3f} 秒"
        
        if self.explain_plan:
            stats += f"\n\n**执行计划：**\n```\n{self.explain_plan}\n```"
        
        return table + stats


class DatabaseBase(ABC):
    """数据库基类"""
    
    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库连接
        
        Args:
            config: 数据库配置
        """
        self.config = config
        self._connection = None
        self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected
    
    @abstractmethod
    async def connect(self) -> None:
        """建立数据库连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """关闭数据库连接"""
        pass
    
    @abstractmethod
    async def execute(self, sql: str, params: Optional[Tuple] = None) -> QueryResult:
        """
        执行 SQL 查询
        
        Args:
            sql: SQL 语句
            params: 查询参数
            
        Returns:
            QueryResult: 查询结果
        """
        pass
    
    @abstractmethod
    async def explain(self, sql: str, analyze: bool = False) -> str:
        """
        生成 SQL 执行计划
        
        Args:
            sql: SQL 语句
            analyze: 是否包含实际执行统计
            
        Returns:
            str: EXPLAIN 执行计划
        """
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """
        获取数据库 schema 信息
        
        Returns:
            Dict: 数据库 schema 信息
        """
        pass
    
    @abstractmethod
    async def get_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            List[str]: 表名列表
        """
        pass
    
    @abstractmethod
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            Dict: 表结构信息
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @asynccontextmanager
    async def transaction(self):
        """事务上下文管理器"""
        if not self._is_connected:
            await self.connect()
        
        try:
            yield self
        except Exception as e:
            # 回滚事务
            await self._rollback()
            raise e
        else:
            # 提交事务
            await self._commit()
    
    @abstractmethod
    async def _rollback(self) -> None:
        """回滚事务"""
        pass
    
    @abstractmethod
    async def _commit(self) -> None:
        """提交事务"""
        pass
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(host={self.config.host}, port={self.config.port}, database={self.config.database})"