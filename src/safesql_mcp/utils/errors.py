"""
错误处理模块
"""

import traceback
from typing import Any, Dict, Optional, Type
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class ErrorCode(Enum):
    """错误代码"""
    # 数据库错误
    DB_CONNECTION_FAILED = "DB_CONNECTION_FAILED"
    DB_QUERY_FAILED = "DB_QUERY_FAILED"
    DB_TIMEOUT = "DB_TIMEOUT"
    DB_POOL_EXHAUSTED = "DB_POOL_EXHAUSTED"
    
    # SQL 错误
    SQL_SYNTAX_ERROR = "SQL_SYNTAX_ERROR"
    SQL_INJECTION_DETECTED = "SQL_INJECTION_DETECTED"
    SQL_HIGH_RISK = "SQL_HIGH_RISK"
    SQL_MEDIUM_RISK = "SQL_MEDIUM_RISK"
    
    # 配置错误
    CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"
    CONFIG_INVALID = "CONFIG_INVALID"
    CONFIG_MISSING_REQUIRED = "CONFIG_MISSING_REQUIRED"
    
    # 规则错误
    RULE_NOT_FOUND = "RULE_NOT_FOUND"
    RULE_INVALID_PATTERN = "RULE_INVALID_PATTERN"
    RULE_CONFLICT = "RULE_CONFLICT"
    
    # 缓存错误
    CACHE_KEY_NOT_FOUND = "CACHE_KEY_NOT_FOUND"
    CACHE_FULL = "CACHE_FULL"
    CACHE_SERIALIZATION_ERROR = "CACHE_SERIALIZATION_ERROR"
    
    # MCP 错误
    MCP_TOOL_NOT_FOUND = "MCP_TOOL_NOT_FOUND"
    MCP_INVALID_PARAMS = "MCP_INVALID_PARAMS"
    MCP_EXECUTION_FAILED = "MCP_EXECUTION_FAILED"
    
    # 通用错误
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"


@dataclass
class SafeSQLError(Exception):
    """SafeSQL 错误基类"""
    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    original_error: Optional[Exception] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "code": self.code.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.details:
            result["details"] = self.details
        
        if self.original_error:
            result["original_error"] = {
                "type": type(self.original_error).__name__,
                "message": str(self.original_error)
            }
        
        return result
    
    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"


class DatabaseError(SafeSQLError):
    """数据库错误"""
    pass


class SQLInjectionError(SafeSQLError):
    """SQL 注入错误"""
    pass


class HighRiskSQLError(SafeSQLError):
    """高风险 SQL 错误"""
    pass


class ConfigurationError(SafeSQLError):
    """配置错误"""
    pass


class RuleError(SafeSQLError):
    """规则错误"""
    pass


class CacheError(SafeSQLError):
    """缓存错误"""
    pass


class MCPError(SafeSQLError):
    """MCP 错误"""
    pass


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger=None):
        """
        初始化错误处理器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self._error_handlers: Dict[ErrorCode, callable] = {}
    
    def register_handler(self, code: ErrorCode, handler: callable) -> None:
        """
        注册错误处理器
        
        Args:
            code: 错误代码
            handler: 处理函数
        """
        self._error_handlers[code] = handler
    
    def handle_error(self, error: Exception) -> SafeSQLError:
        """
        处理错误
        
        Args:
            error: 原始错误
            
        Returns:
            SafeSQLError: SafeSQL 错误
        """
        # 如果已经是 SafeSQL 错误，直接返回
        if isinstance(error, SafeSQLError):
            return error
        
        # 转换为 SafeSQL 错误
        safesql_error = self._convert_error(error)
        
        # 记录错误
        self._log_error(safesql_error)
        
        # 调用注册的处理器
        handler = self._error_handlers.get(safesql_error.code)
        if handler:
            try:
                handler(safesql_error)
            except Exception as e:
                # 处理器本身出错，记录但不抛出
                if self.logger:
                    self.logger.error(f"Error handler failed: {e}")
        
        return safesql_error
    
    def _convert_error(self, error: Exception) -> SafeSQLError:
        """
        转换错误
        
        Args:
            error: 原始错误
            
        Returns:
            SafeSQLError: SafeSQL 错误
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 数据库连接错误
        if "connection" in error_message.lower() or "connect" in error_message.lower():
            return DatabaseError(
                code=ErrorCode.DB_CONNECTION_FAILED,
                message=f"Database connection failed: {error_message}",
                original_error=error
            )
        
        # 数据库查询错误
        if "query" in error_message.lower() or "execute" in error_message.lower():
            return DatabaseError(
                code=ErrorCode.DB_QUERY_FAILED,
                message=f"Database query failed: {error_message}",
                original_error=error
            )
        
        # 超时错误
        if "timeout" in error_message.lower():
            return DatabaseError(
                code=ErrorCode.DB_TIMEOUT,
                message=f"Database operation timed out: {error_message}",
                original_error=error
            )
        
        # SQL 语法错误
        if "syntax" in error_message.lower() or "parse" in error_message.lower():
            return SafeSQLError(
                code=ErrorCode.SQL_SYNTAX_ERROR,
                message=f"SQL syntax error: {error_message}",
                original_error=error
            )
        
        # 配置错误
        if "config" in error_message.lower():
            return ConfigurationError(
                code=ErrorCode.CONFIG_INVALID,
                message=f"Configuration error: {error_message}",
                original_error=error
            )
        
        # 权限错误
        if "permission" in error_message.lower() or "access" in error_message.lower():
            return SafeSQLError(
                code=ErrorCode.PERMISSION_DENIED,
                message=f"Permission denied: {error_message}",
                original_error=error
            )
        
        # 未知错误
        return SafeSQLError(
            code=ErrorCode.UNKNOWN_ERROR,
            message=f"Unknown error: {error_message}",
            details={"error_type": error_type},
            original_error=error
        )
    
    def _log_error(self, error: SafeSQLError) -> None:
        """
        记录错误
        
        Args:
            error: SafeSQL 错误
        """
        if not self.logger:
            return
        
        # 根据错误代码选择日志级别
        if error.code in [
            ErrorCode.SQL_INJECTION_DETECTED,
            ErrorCode.SQL_HIGH_RISK,
            ErrorCode.PERMISSION_DENIED
        ]:
            self.logger.error(str(error))
        elif error.code in [
            ErrorCode.SQL_MEDIUM_RISK,
            ErrorCode.DB_TIMEOUT,
            ErrorCode.CONFIG_INVALID
        ]:
            self.logger.warning(str(error))
        else:
            self.logger.error(str(error))
        
        # 记录详细信息
        if error.details:
            self.logger.debug(f"Error details: {error.details}")
        
        if error.original_error:
            self.logger.debug(f"Original error: {traceback.format_exception(type(error.original_error), error.original_error, error.original_error.__traceback__)}")
    
    def create_error(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ) -> SafeSQLError:
        """
        创建错误
        
        Args:
            code: 错误代码
            message: 错误消息
            details: 错误详情
            original_error: 原始错误
            
        Returns:
            SafeSQLError: SafeSQL 错误
        """
        # 根据错误代码选择错误类型
        error_type_map = {
            ErrorCode.DB_CONNECTION_FAILED: DatabaseError,
            ErrorCode.DB_QUERY_FAILED: DatabaseError,
            ErrorCode.DB_TIMEOUT: DatabaseError,
            ErrorCode.DB_POOL_EXHAUSTED: DatabaseError,
            ErrorCode.SQL_INJECTION_DETECTED: SQLInjectionError,
            ErrorCode.SQL_HIGH_RISK: HighRiskSQLError,
            ErrorCode.CONFIG_NOT_FOUND: ConfigurationError,
            ErrorCode.CONFIG_INVALID: ConfigurationError,
            ErrorCode.CONFIG_MISSING_REQUIRED: ConfigurationError,
            ErrorCode.RULE_NOT_FOUND: RuleError,
            ErrorCode.RULE_INVALID_PATTERN: RuleError,
            ErrorCode.RULE_CONFLICT: RuleError,
            ErrorCode.CACHE_KEY_NOT_FOUND: CacheError,
            ErrorCode.CACHE_FULL: CacheError,
            ErrorCode.CACHE_SERIALIZATION_ERROR: CacheError,
            ErrorCode.MCP_TOOL_NOT_FOUND: MCPError,
            ErrorCode.MCP_INVALID_PARAMS: MCPError,
            ErrorCode.MCP_EXECUTION_FAILED: MCPError,
        }
        
        error_class = error_type_map.get(code, SafeSQLError)
        
        return error_class(
            code=code,
            message=message,
            details=details,
            original_error=original_error
        )


def handle_database_error(func):
    """
    数据库错误处理装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()
            raise error_handler.handle_error(e)
    
    return wrapper


def handle_sql_error(func):
    """
    SQL 错误处理装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()
            raise error_handler.handle_error(e)
    
    return wrapper


def handle_config_error(func):
    """
    配置错误处理装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()
            raise error_handler.handle_error(e)
    
    return wrapper