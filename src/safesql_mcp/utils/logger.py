"""
日志工具模块
"""

import logging
import sys
import json
from typing import Optional, Any, Dict
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            str: 格式化后的日志
        """
        # 构建日志数据
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


class JSONFormatter(logging.Formatter):
    """JSON 日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            str: JSON 格式的日志
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


class SafeSQLLogger:
    """SafeSQL 日志记录器"""
    
    def __init__(self, name: str = "safesql", level: str = "INFO", 
                 log_format: Optional[str] = None, log_file: Optional[str] = None,
                 structured: bool = False):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
            log_format: 日志格式
            log_file: 日志文件路径
            structured: 是否使用结构化日志
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # 设置日志级别
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 设置日志格式
            if structured:
                formatter = StructuredFormatter()
            elif log_format:
                formatter = logging.Formatter(log_format)
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            
            # 添加控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # 添加文件处理器（如果指定）
            if log_file:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        记录调试日志
        
        Args:
            message: 日志消息
            extra: 额外数据
        """
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        记录信息日志
        
        Args:
            message: 日志消息
            extra: 额外数据
        """
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        记录警告日志
        
        Args:
            message: 日志消息
            extra: 额外数据
        """
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, 
              exc_info: Optional[Exception] = None) -> None:
        """
        记录错误日志
        
        Args:
            message: 日志消息
            extra: 额外数据
            exc_info: 异常信息
        """
        self._log(logging.ERROR, message, extra, exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None,
                 exc_info: Optional[Exception] = None) -> None:
        """
        记录严重错误日志
        
        Args:
            message: 日志消息
            extra: 额外数据
            exc_info: 异常信息
        """
        self._log(logging.CRITICAL, message, extra, exc_info)
    
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None,
             exc_info: Optional[Exception] = None) -> None:
        """
        记录日志
        
        Args:
            level: 日志级别
            message: 日志消息
            extra: 额外数据
            exc_info: 异常信息
        """
        # 创建日志记录
        record = self.logger.makeRecord(
            name=self.name,
            level=level,
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        
        # 添加额外数据
        if extra:
            record.extra_data = extra
        
        # 添加异常信息
        if exc_info:
            record.exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
        
        # 处理日志记录
        self.logger.handle(record)
    
    def log_query(self, database: str, sql: str, duration: float, 
                  risk_level: str, success: bool) -> None:
        """
        记录查询日志
        
        Args:
            database: 数据库名称
            sql: SQL 语句
            duration: 执行时间
            risk_level: 风险等级
            success: 是否成功
        """
        extra = {
            "database": database,
            "sql": sql,
            "duration": duration,
            "risk_level": risk_level,
            "success": success
        }
        
        if success:
            self.info(f"Query executed successfully on {database}", extra)
        else:
            self.error(f"Query failed on {database}", extra)
    
    def log_connection(self, database: str, action: str, success: bool,
                       error: Optional[str] = None) -> None:
        """
        记录连接日志
        
        Args:
            database: 数据库名称
            action: 操作类型 (connect, disconnect, test)
            success: 是否成功
            error: 错误信息
        """
        extra = {
            "database": database,
            "action": action,
            "success": success
        }
        
        if error:
            extra["error"] = error
        
        if success:
            self.info(f"Database {action} successful: {database}", extra)
        else:
            self.error(f"Database {action} failed: {database}", extra)
    
    def log_risk_assessment(self, sql: str, risk_level: str, 
                           message: str, blocked: bool) -> None:
        """
        记录风险评估日志
        
        Args:
            sql: SQL 语句
            risk_level: 风险等级
            message: 风险消息
            blocked: 是否被阻止
        """
        extra = {
            "sql": sql,
            "risk_level": risk_level,
            "message": message,
            "blocked": blocked
        }
        
        if blocked:
            self.warning(f"High risk SQL blocked: {message}", extra)
        elif risk_level == "medium":
            self.warning(f"Medium risk SQL warning: {message}", extra)
        else:
            self.info(f"SQL risk assessment: {risk_level}", extra)
    
    def log_cache(self, action: str, key: str, hit: bool) -> None:
        """
        记录缓存日志
        
        Args:
            action: 操作类型 (get, set, invalidate)
            key: 缓存键
            hit: 是否命中
        """
        extra = {
            "action": action,
            "key": key,
            "hit": hit
        }
        
        if action == "get":
            if hit:
                self.debug(f"Cache hit: {key}", extra)
            else:
                self.debug(f"Cache miss: {key}", extra)
        else:
            self.debug(f"Cache {action}: {key}", extra)


def setup_logger(
    name: str = "safesql",
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    structured: bool = False
) -> SafeSQLLogger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_format: 日志格式
        log_file: 日志文件路径
        structured: 是否使用结构化日志
        
    Returns:
        SafeSQLLogger: 日志记录器
    """
    return SafeSQLLogger(name, level, log_format, log_file, structured)


def get_logger(name: str = "safesql") -> SafeSQLLogger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        SafeSQLLogger: 日志记录器
    """
    return SafeSQLLogger(name)