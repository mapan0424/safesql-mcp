"""
错误处理模块测试
"""

import pytest

from safesql_mcp.utils.errors import (
    ErrorCode, SafeSQLError, DatabaseError, SQLInjectionError,
    HighRiskSQLError, ConfigurationError, RuleError, CacheError,
    MCPError, ErrorHandler
)


class TestErrorCode:
    """ErrorCode 测试"""
    
    def test_error_codes(self):
        """测试错误代码"""
        # 数据库错误
        assert ErrorCode.DB_CONNECTION_FAILED.value == "DB_CONNECTION_FAILED"
        assert ErrorCode.DB_QUERY_FAILED.value == "DB_QUERY_FAILED"
        assert ErrorCode.DB_TIMEOUT.value == "DB_TIMEOUT"
        
        # SQL 错误
        assert ErrorCode.SQL_SYNTAX_ERROR.value == "SQL_SYNTAX_ERROR"
        assert ErrorCode.SQL_INJECTION_DETECTED.value == "SQL_INJECTION_DETECTED"
        assert ErrorCode.SQL_HIGH_RISK.value == "SQL_HIGH_RISK"
        
        # 配置错误
        assert ErrorCode.CONFIG_NOT_FOUND.value == "CONFIG_NOT_FOUND"
        assert ErrorCode.CONFIG_INVALID.value == "CONFIG_INVALID"
        
        # 规则错误
        assert ErrorCode.RULE_NOT_FOUND.value == "RULE_NOT_FOUND"
        assert ErrorCode.RULE_INVALID_PATTERN.value == "RULE_INVALID_PATTERN"
        
        # 缓存错误
        assert ErrorCode.CACHE_KEY_NOT_FOUND.value == "CACHE_KEY_NOT_FOUND"
        assert ErrorCode.CACHE_FULL.value == "CACHE_FULL"
        
        # MCP 错误
        assert ErrorCode.MCP_TOOL_NOT_FOUND.value == "MCP_TOOL_NOT_FOUND"
        assert ErrorCode.MCP_INVALID_PARAMS.value == "MCP_INVALID_PARAMS"


class TestSafeSQLError:
    """SafeSQLError 测试"""
    
    def test_error_creation(self):
        """测试错误创建"""
        error = SafeSQLError(
            code=ErrorCode.UNKNOWN_ERROR,
            message="Test error message"
        )
        
        assert error.code == ErrorCode.UNKNOWN_ERROR
        assert error.message == "Test error message"
        assert error.details is None
        assert error.original_error is None
        assert error.timestamp is not None
    
    def test_error_with_details(self):
        """测试带详情的错误"""
        details = {"key": "value", "number": 42}
        error = SafeSQLError(
            code=ErrorCode.UNKNOWN_ERROR,
            message="Test error message",
            details=details
        )
        
        assert error.details == details
    
    def test_error_with_original_error(self):
        """测试带原始错误的错误"""
        original = ValueError("Original error")
        error = SafeSQLError(
            code=ErrorCode.UNKNOWN_ERROR,
            message="Test error message",
            original_error=original
        )
        
        assert error.original_error == original
    
    def test_error_to_dict(self):
        """测试错误转换为字典"""
        error = SafeSQLError(
            code=ErrorCode.UNKNOWN_ERROR,
            message="Test error message",
            details={"key": "value"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["code"] == "UNKNOWN_ERROR"
        assert error_dict["message"] == "Test error message"
        assert error_dict["details"] == {"key": "value"}
        assert "timestamp" in error_dict
    
    def test_error_str(self):
        """测试错误字符串表示"""
        error = SafeSQLError(
            code=ErrorCode.UNKNOWN_ERROR,
            message="Test error message"
        )
        
        assert str(error) == "[UNKNOWN_ERROR] Test error message"


class TestDatabaseError:
    """DatabaseError 测试"""
    
    def test_database_error(self):
        """测试数据库错误"""
        error = DatabaseError(
            code=ErrorCode.DB_CONNECTION_FAILED,
            message="Connection failed"
        )
        
        assert error.code == ErrorCode.DB_CONNECTION_FAILED
        assert error.message == "Connection failed"
        assert isinstance(error, SafeSQLError)


class TestSQLInjectionError:
    """SQLInjectionError 测试"""
    
    def test_sql_injection_error(self):
        """测试 SQL 注入错误"""
        error = SQLInjectionError(
            code=ErrorCode.SQL_INJECTION_DETECTED,
            message="Injection detected"
        )
        
        assert error.code == ErrorCode.SQL_INJECTION_DETECTED
        assert error.message == "Injection detected"
        assert isinstance(error, SafeSQLError)


class TestHighRiskSQLError:
    """HighRiskSQLError 测试"""
    
    def test_high_risk_sql_error(self):
        """测试高风险 SQL 错误"""
        error = HighRiskSQLError(
            code=ErrorCode.SQL_HIGH_RISK,
            message="High risk SQL"
        )
        
        assert error.code == ErrorCode.SQL_HIGH_RISK
        assert error.message == "High risk SQL"
        assert isinstance(error, SafeSQLError)


class TestConfigurationError:
    """ConfigurationError 测试"""
    
    def test_configuration_error(self):
        """测试配置错误"""
        error = ConfigurationError(
            code=ErrorCode.CONFIG_INVALID,
            message="Invalid configuration"
        )
        
        assert error.code == ErrorCode.CONFIG_INVALID
        assert error.message == "Invalid configuration"
        assert isinstance(error, SafeSQLError)


class TestRuleError:
    """RuleError 测试"""
    
    def test_rule_error(self):
        """测试规则错误"""
        error = RuleError(
            code=ErrorCode.RULE_NOT_FOUND,
            message="Rule not found"
        )
        
        assert error.code == ErrorCode.RULE_NOT_FOUND
        assert error.message == "Rule not found"
        assert isinstance(error, SafeSQLError)


class TestCacheError:
    """CacheError 测试"""
    
    def test_cache_error(self):
        """测试缓存错误"""
        error = CacheError(
            code=ErrorCode.CACHE_KEY_NOT_FOUND,
            message="Key not found"
        )
        
        assert error.code == ErrorCode.CACHE_KEY_NOT_FOUND
        assert error.message == "Key not found"
        assert isinstance(error, SafeSQLError)


class TestMCPError:
    """MCPError 测试"""
    
    def test_mcp_error(self):
        """测试 MCP 错误"""
        error = MCPError(
            code=ErrorCode.MCP_TOOL_NOT_FOUND,
            message="Tool not found"
        )
        
        assert error.code == ErrorCode.MCP_TOOL_NOT_FOUND
        assert error.message == "Tool not found"
        assert isinstance(error, SafeSQLError)


class TestErrorHandler:
    """ErrorHandler 测试"""
    
    def test_handler_init(self):
        """测试处理器初始化"""
        handler = ErrorHandler()
        
        assert handler.logger is None
        assert len(handler._error_handlers) == 0
    
    def test_register_handler(self):
        """测试注册处理器"""
        handler = ErrorHandler()
        
        def test_handler(error):
            pass
        
        handler.register_handler(ErrorCode.UNKNOWN_ERROR, test_handler)
        
        assert ErrorCode.UNKNOWN_ERROR in handler._error_handlers
        assert handler._error_handlers[ErrorCode.UNKNOWN_ERROR] == test_handler
    
    def test_handle_safesql_error(self):
        """测试处理 SafeSQL 错误"""
        handler = ErrorHandler()
        
        error = SafeSQLError(
            code=ErrorCode.UNKNOWN_ERROR,
            message="Test error"
        )
        
        result = handler.handle_error(error)
        
        assert result == error
    
    def test_handle_generic_error(self):
        """测试处理通用错误"""
        handler = ErrorHandler()
        
        error = ValueError("Test error")
        result = handler.handle_error(error)
        
        assert isinstance(result, SafeSQLError)
        assert result.code == ErrorCode.UNKNOWN_ERROR
        assert "Test error" in result.message
    
    def test_handle_connection_error(self):
        """测试处理连接错误"""
        handler = ErrorHandler()
        
        error = ConnectionError("Connection refused")
        result = handler.handle_error(error)
        
        assert isinstance(result, DatabaseError)
        assert result.code == ErrorCode.DB_CONNECTION_FAILED
    
    def test_handle_timeout_error(self):
        """测试处理超时错误"""
        handler = ErrorHandler()
        
        error = TimeoutError("Operation timed out")
        result = handler.handle_error(error)
        
        assert isinstance(result, DatabaseError)
        assert result.code == ErrorCode.DB_TIMEOUT
    
    def test_create_error(self):
        """测试创建错误"""
        handler = ErrorHandler()
        
        error = handler.create_error(
            code=ErrorCode.DB_CONNECTION_FAILED,
            message="Connection failed",
            details={"host": "localhost"}
        )
        
        assert isinstance(error, DatabaseError)
        assert error.code == ErrorCode.DB_CONNECTION_FAILED
        assert error.message == "Connection failed"
        assert error.details == {"host": "localhost"}
    
    def test_create_error_with_original(self):
        """测试创建带原始错误的错误"""
        handler = ErrorHandler()
        
        original = ValueError("Original error")
        error = handler.create_error(
            code=ErrorCode.UNKNOWN_ERROR,
            message="Unknown error",
            original_error=original
        )
        
        assert isinstance(error, SafeSQLError)
        assert error.original_error == original