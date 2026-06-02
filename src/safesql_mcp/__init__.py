"""
SafeSQL MCP: AI Agent 安全数据库访问 MCP Server + SQL 风险审查工具
"""

__version__ = "1.1.0"
__author__ = "Panda"
__email__ = "315337987@qq.com"

from .server import SafeSQLServer
from .core.engine import RiskEngine
from .core.rules import RiskLevel

__all__ = [
    "SafeSQLServer",
    "RiskEngine",
    "RiskLevel",
]