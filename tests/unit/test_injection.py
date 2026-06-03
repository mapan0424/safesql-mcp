"""
SQL 注入检测模块测试
"""

import pytest

from safesql_mcp.core.injection import SQLInjectionDetector, InjectionRiskLevel, InjectionPattern


class TestSQLInjectionDetector:
    """SQL 注入检测器测试"""
    
    def test_init_default_patterns(self):
        """测试初始化默认模式"""
        detector = SQLInjectionDetector()
        
        assert len(detector.patterns) > 0
        assert len(detector._compiled_patterns) > 0
    
    def test_detect_comment_injection(self):
        """测试检测注释注入"""
        detector = SQLInjectionDetector()
        
        # 单行注释
        risks = detector.detect("SELECT * FROM users -- WHERE id = 1")
        assert len(risks) > 0
        assert any(r["name"] == "comment_injection" for r in risks)
        
        # 多行注释
        risks = detector.detect("SELECT * FROM users /* WHERE id = 1 */")
        assert len(risks) > 0
        assert any(r["name"] == "comment_injection" for r in risks)
    
    def test_detect_union_injection(self):
        """测试检测 UNION 注入"""
        detector = SQLInjectionDetector()
        
        risks = detector.detect("SELECT * FROM users UNION SELECT * FROM passwords")
        assert len(risks) > 0
        assert any(r["name"] == "union_injection" for r in risks)
    
    def test_detect_boolean_injection(self):
        """测试检测布尔注入"""
        detector = SQLInjectionDetector()
        
        risks = detector.detect("SELECT * FROM users WHERE id = 1 AND 1=1")
        assert len(risks) > 0
        assert any(r["name"] == "boolean_injection" for r in risks)
    
    def test_detect_time_based_injection(self):
        """测试检测时间盲注"""
        detector = SQLInjectionDetector()
        
        risks = detector.detect("SELECT * FROM users WHERE id = 1 AND SLEEP(5)")
        assert len(risks) > 0
        assert any(r["name"] == "time_based_injection" for r in risks)
    
    def test_detect_stacked_queries(self):
        """测试检测堆叠查询"""
        detector = SQLInjectionDetector()
        
        risks = detector.detect("SELECT * FROM users; DROP TABLE users")
        assert len(risks) > 0
        assert any(r["name"] == "stacked_queries" for r in risks)
    
    def test_detect_system_command_injection(self):
        """测试检测系统命令注入"""
        detector = SQLInjectionDetector()
        
        risks = detector.detect("SELECT * FROM users WHERE id = 1; EXEC xp_cmdshell 'dir'")
        assert len(risks) > 0
        assert any(r["name"] == "system_command_injection" for r in risks)
    
    def test_detect_hex_injection(self):
        """测试检测十六进制注入"""
        detector = SQLInjectionDetector()
        
        risks = detector.detect("SELECT * FROM users WHERE name = 0x61646D696E")
        assert len(risks) > 0
        assert any(r["name"] == "hex_injection" for r in risks)
    
    def test_no_injection(self):
        """测试无注入"""
        detector = SQLInjectionDetector()
        
        risks = detector.detect("SELECT * FROM users WHERE id = 1")
        assert len(risks) == 0
    
    def test_get_highest_risk_level(self):
        """测试获取最高风险等级"""
        detector = SQLInjectionDetector()
        
        # 无注入
        risk_level = detector.get_highest_risk_level("SELECT * FROM users WHERE id = 1")
        assert risk_level == InjectionRiskLevel.NONE
        
        # 低风险
        risk_level = detector.get_highest_risk_level("SELECT * FROM users WHERE name = 0x61646D696E")
        assert risk_level == InjectionRiskLevel.LOW
        
        # 中风险
        risk_level = detector.get_highest_risk_level("SELECT * FROM users WHERE id = 1 AND 1=1")
        assert risk_level == InjectionRiskLevel.MEDIUM
        
        # 高风险
        risk_level = detector.get_highest_risk_level("SELECT * FROM users UNION SELECT * FROM passwords")
        assert risk_level == InjectionRiskLevel.HIGH
        
        # 严重风险
        risk_level = detector.get_highest_risk_level("SELECT * FROM users; DROP TABLE users")
        assert risk_level == InjectionRiskLevel.CRITICAL
    
    def test_is_safe(self):
        """测试安全性检查"""
        detector = SQLInjectionDetector()
        
        # 安全查询
        assert detector.is_safe("SELECT * FROM users WHERE id = 1") is True
        
        # 不安全查询
        assert detector.is_safe("SELECT * FROM users UNION SELECT * FROM passwords") is False
    
    def test_add_pattern(self):
        """测试添加模式"""
        detector = SQLInjectionDetector()
        initial_count = len(detector.patterns)
        
        # 添加新模式
        pattern = InjectionPattern(
            name="test_pattern",
            pattern=r"TEST_PATTERN",
            risk_level=InjectionRiskLevel.MEDIUM,
            message="Test pattern detected",
            description="Test pattern"
        )
        detector.add_pattern(pattern)
        
        assert len(detector.patterns) == initial_count + 1
        assert "test_pattern" in detector._compiled_patterns
    
    def test_remove_pattern(self):
        """测试移除模式"""
        detector = SQLInjectionDetector()
        
        # 添加模式
        pattern = InjectionPattern(
            name="test_pattern",
            pattern=r"TEST_PATTERN",
            risk_level=InjectionRiskLevel.MEDIUM,
            message="Test pattern detected",
            description="Test pattern"
        )
        detector.add_pattern(pattern)
        
        # 移除模式
        result = detector.remove_pattern("test_pattern")
        assert result is True
        assert "test_pattern" not in detector._compiled_patterns
    
    def test_enable_disable_pattern(self):
        """测试启用/禁用模式"""
        detector = SQLInjectionDetector()
        
        # 添加模式
        pattern = InjectionPattern(
            name="test_pattern",
            pattern=r"TEST_PATTERN",
            risk_level=InjectionRiskLevel.MEDIUM,
            message="Test pattern detected",
            description="Test pattern",
            enabled=False
        )
        detector.add_pattern(pattern)
        
        # 启用模式
        result = detector.enable_pattern("test_pattern")
        assert result is True
        assert pattern.enabled is True
        
        # 禁用模式
        result = detector.disable_pattern("test_pattern")
        assert result is True
        assert pattern.enabled is False
    
    def test_get_patterns(self):
        """测试获取模式列表"""
        detector = SQLInjectionDetector()
        
        patterns = detector.get_patterns()
        
        assert len(patterns) > 0
        assert all("name" in p for p in patterns)
        assert all("pattern" in p for p in patterns)
        assert all("risk_level" in p for p in patterns)
    
    def test_get_stats(self):
        """测试获取统计信息"""
        detector = SQLInjectionDetector()
        
        stats = detector.get_stats()
        
        assert "total_patterns" in stats
        assert "enabled_patterns" in stats
        assert "disabled_patterns" in stats
        assert "risk_level_counts" in stats
        assert stats["total_patterns"] > 0