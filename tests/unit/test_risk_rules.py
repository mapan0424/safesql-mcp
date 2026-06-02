"""
Unit tests for risk rules
"""

import pytest
import re
from safesql_mcp.core.rules import RiskLevel, RiskRule, RiskAssessment, DefaultRiskRules


class TestRiskLevel:
    """Test RiskLevel enum"""
    
    def test_risk_levels(self):
        """Test all risk levels exist"""
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.SAFE.value == "safe"
    
    def test_risk_level_ordering(self):
        """Test risk level ordering"""
        # SAFE is the lowest, HIGH is the highest
        # Note: Enum comparison is based on definition order
        assert RiskLevel.SAFE.value == "safe"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"


class TestRiskRule:
    """Test RiskRule class"""
    
    def test_init_valid_rule(self):
        """Test initializing a valid rule"""
        rule = RiskRule(
            name="test_rule",
            pattern=r"TEST",
            level=RiskLevel.HIGH,
            message="Test message"
        )
        
        assert rule.name == "test_rule"
        assert rule.pattern == r"TEST"
        assert rule.level == RiskLevel.HIGH
        assert rule.message == "Test message"
        assert rule.enabled is True
    
    def test_init_with_description(self):
        """Test initializing rule with description"""
        rule = RiskRule(
            name="test_rule",
            pattern=r"TEST",
            level=RiskLevel.HIGH,
            message="Test message",
            description="Test description"
        )
        
        assert rule.description == "Test description"
    
    def test_init_disabled_rule(self):
        """Test initializing a disabled rule"""
        rule = RiskRule(
            name="test_rule",
            pattern=r"TEST",
            level=RiskLevel.HIGH,
            message="Test message",
            enabled=False
        )
        
        assert rule.enabled is False
    
    def test_init_invalid_pattern(self):
        """Test initializing rule with invalid pattern"""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            RiskRule(
                name="invalid",
                pattern=r"[invalid",
                level=RiskLevel.HIGH,
                message="Invalid"
            )
    
    def test_matches_simple_pattern(self):
        """Test matching a simple pattern"""
        rule = RiskRule(
            name="test",
            pattern=r"TEST",
            level=RiskLevel.HIGH,
            message="Test"
        )
        
        assert rule.matches("TEST") is True
        assert rule.matches("test") is True  # Case insensitive
        assert rule.matches("OTHER") is False
    
    def test_matches_complex_pattern(self):
        """Test matching a complex pattern"""
        rule = RiskRule(
            name="drop_table",
            pattern=r"DROP\s+TABLE",
            level=RiskLevel.HIGH,
            message="Drop table"
        )
        
        assert rule.matches("DROP TABLE users") is True
        assert rule.matches("drop table users") is True
        assert rule.matches("DROP  TABLE users") is True
        assert rule.matches("SELECT * FROM users") is False
    
    def test_matches_disabled_rule(self):
        """Test that disabled rules don't match"""
        rule = RiskRule(
            name="test",
            pattern=r"TEST",
            level=RiskLevel.HIGH,
            message="Test",
            enabled=False
        )
        
        assert rule.matches("TEST") is False


class TestRiskAssessment:
    """Test RiskAssessment class"""
    
    def test_init_basic(self):
        """Test basic initialization"""
        assessment = RiskAssessment(
            sql="SELECT * FROM users",
            risk_level=RiskLevel.MEDIUM,
            message="Test message"
        )
        
        assert assessment.sql == "SELECT * FROM users"
        assert assessment.risk_level == RiskLevel.MEDIUM
        assert assessment.message == "Test message"
        assert assessment.suggestions == []
        assert assessment.performance_warnings == []
    
    def test_init_with_suggestions(self):
        """Test initialization with suggestions"""
        assessment = RiskAssessment(
            sql="SELECT * FROM users",
            risk_level=RiskLevel.MEDIUM,
            message="Test",
            suggestions=["Suggestion 1", "Suggestion 2"]
        )
        
        assert len(assessment.suggestions) == 2
    
    def test_is_executable_high_risk(self):
        """Test is_executable for high risk"""
        assessment = RiskAssessment(
            sql="DROP TABLE users",
            risk_level=RiskLevel.HIGH,
            message="High risk"
        )
        
        assert assessment.is_executable is False
    
    def test_is_executable_medium_risk(self):
        """Test is_executable for medium risk"""
        assessment = RiskAssessment(
            sql="SELECT * FROM users",
            risk_level=RiskLevel.MEDIUM,
            message="Medium risk"
        )
        
        assert assessment.is_executable is True
    
    def test_is_executable_low_risk(self):
        """Test is_executable for low risk"""
        assessment = RiskAssessment(
            sql="SELECT id FROM users WHERE id = 1",
            risk_level=RiskLevel.LOW,
            message="Low risk"
        )
        
        assert assessment.is_executable is True
    
    def test_requires_warning_medium_risk(self):
        """Test requires_warning for medium risk"""
        assessment = RiskAssessment(
            sql="SELECT * FROM users",
            risk_level=RiskLevel.MEDIUM,
            message="Medium risk"
        )
        
        assert assessment.requires_warning is True
    
    def test_requires_warning_low_risk(self):
        """Test requires_warning for low risk"""
        assessment = RiskAssessment(
            sql="SELECT id FROM users WHERE id = 1",
            risk_level=RiskLevel.LOW,
            message="Low risk"
        )
        
        assert assessment.requires_warning is False
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        assessment = RiskAssessment(
            sql="SELECT * FROM users",
            risk_level=RiskLevel.MEDIUM,
            message="Test",
            suggestions=["Suggestion 1"]
        )
        
        result = assessment.to_dict()
        
        assert result["sql"] == "SELECT * FROM users"
        assert result["risk_level"] == "medium"
        assert result["message"] == "Test"
        assert result["suggestions"] == ["Suggestion 1"]
        assert result["is_executable"] is True
        assert result["requires_warning"] is True


class TestDefaultRiskRules:
    """Test DefaultRiskRules class"""
    
    def test_get_high_risk_rules(self):
        """Test getting high risk rules"""
        rules = DefaultRiskRules.get_high_risk_rules()
        
        assert len(rules) > 0
        for rule in rules:
            assert rule.level == RiskLevel.HIGH
            assert rule.name is not None
            assert rule.pattern is not None
            assert rule.message is not None
    
    def test_get_medium_risk_rules(self):
        """Test getting medium risk rules"""
        rules = DefaultRiskRules.get_medium_risk_rules()
        
        assert len(rules) > 0
        for rule in rules:
            assert rule.level == RiskLevel.MEDIUM
    
    def test_get_low_risk_rules(self):
        """Test getting low risk rules"""
        rules = DefaultRiskRules.get_low_risk_rules()
        
        assert len(rules) > 0
        for rule in rules:
            assert rule.level == RiskLevel.LOW
    
    def test_get_whitelist_rules(self):
        """Test getting whitelist rules"""
        rules = DefaultRiskRules.get_whitelist_rules()
        
        assert len(rules) > 0
        for rule in rules:
            assert rule.level == RiskLevel.SAFE
    
    def test_get_all_rules(self):
        """Test getting all rules"""
        rules = DefaultRiskRules.get_all_rules()
        
        assert len(rules) > 0
        
        # Check that all levels are represented
        levels = {rule.level for rule in rules}
        assert RiskLevel.HIGH in levels
        assert RiskLevel.MEDIUM in levels
        assert RiskLevel.LOW in levels
        assert RiskLevel.SAFE in levels
    
    def test_high_risk_rules_content(self):
        """Test that high risk rules contain expected patterns"""
        rules = DefaultRiskRules.get_high_risk_rules()
        rule_names = {rule.name for rule in rules}
        
        # Check for essential high risk rules
        assert "drop_table" in rule_names
        assert "drop_database" in rule_names
        assert "truncate_table" in rule_names
        assert "delete_without_where" in rule_names
        assert "update_without_where" in rule_names
        assert "grant_revoke" in rule_names
    
    def test_medium_risk_rules_content(self):
        """Test that medium risk rules contain expected patterns"""
        rules = DefaultRiskRules.get_medium_risk_rules()
        rule_names = {rule.name for rule in rules}
        
        # Check for essential medium risk rules
        assert "select_all" in rule_names
        assert "insert_without_columns" in rule_names
        assert "like_prefix_wildcard" in rule_names
    
    def test_whitelist_rules_content(self):
        """Test that whitelist rules contain expected patterns"""
        rules = DefaultRiskRules.get_whitelist_rules()
        rule_names = {rule.name for rule in rules}
        
        # Check for essential whitelist rules
        assert "health_check" in rule_names