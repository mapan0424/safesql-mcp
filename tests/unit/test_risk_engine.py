"""
Unit tests for risk engine
"""

import pytest
from safesql_mcp.core.engine import RiskEngine
from safesql_mcp.core.rules import RiskLevel, RiskRule, RiskAssessment


class TestRiskEngine:
    """Test RiskEngine class"""
    
    def test_init_default_rules(self):
        """Test engine initialization with default rules"""
        engine = RiskEngine()
        assert len(engine.rules) > 0
        assert len(engine._rules_by_level[RiskLevel.HIGH]) > 0
        assert len(engine._rules_by_level[RiskLevel.MEDIUM]) > 0
        assert len(engine._rules_by_level[RiskLevel.LOW]) > 0
        assert len(engine._rules_by_level[RiskLevel.SAFE]) > 0
    
    def test_init_custom_rules(self):
        """Test engine initialization with custom rules"""
        custom_rules = [
            RiskRule(
                name="test_rule",
                pattern=r"TEST",
                level=RiskLevel.HIGH,
                message="Test rule"
            )
        ]
        engine = RiskEngine(custom_rules=custom_rules)
        assert len(engine.rules) == 1
        assert engine.rules[0].name == "test_rule"
    
    def test_add_rule(self):
        """Test adding a single rule"""
        engine = RiskEngine()
        initial_count = len(engine.rules)
        
        new_rule = RiskRule(
            name="new_rule",
            pattern=r"NEW",
            level=RiskLevel.MEDIUM,
            message="New rule"
        )
        engine.add_rule(new_rule)
        
        assert len(engine.rules) == initial_count + 1
        assert new_rule in engine.rules
    
    def test_add_rules(self):
        """Test adding multiple rules"""
        engine = RiskEngine()
        initial_count = len(engine.rules)
        
        new_rules = [
            RiskRule(name="rule1", pattern=r"RULE1", level=RiskLevel.HIGH, message="Rule 1"),
            RiskRule(name="rule2", pattern=r"RULE2", level=RiskLevel.LOW, message="Rule 2"),
        ]
        engine.add_rules(new_rules)
        
        assert len(engine.rules) == initial_count + 2
    
    def test_remove_rule(self):
        """Test removing a rule"""
        engine = RiskEngine()
        
        # Add a rule to remove
        rule_to_remove = RiskRule(
            name="remove_me",
            pattern=r"REMOVE",
            level=RiskLevel.HIGH,
            message="Remove me"
        )
        engine.add_rule(rule_to_remove)
        initial_count = len(engine.rules)
        
        # Remove the rule
        result = engine.remove_rule("remove_me")
        
        assert result is True
        assert len(engine.rules) == initial_count - 1
        assert rule_to_remove not in engine.rules
    
    def test_remove_nonexistent_rule(self):
        """Test removing a nonexistent rule"""
        engine = RiskEngine()
        result = engine.remove_rule("nonexistent")
        assert result is False
    
    def test_assess_sql_high_risk_drop_table(self):
        """Test assessing DROP TABLE as high risk"""
        engine = RiskEngine()
        assessment = engine.assess_sql("DROP TABLE users")
        
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.is_executable is False
        assert "DROP TABLE" in assessment.message
    
    def test_assess_sql_high_risk_delete_without_where(self):
        """Test assessing DELETE without WHERE as high risk"""
        engine = RiskEngine()
        assessment = engine.assess_sql("DELETE FROM users")
        
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.is_executable is False
    
    def test_assess_sql_high_risk_update_without_where(self):
        """Test assessing UPDATE without WHERE as high risk"""
        engine = RiskEngine()
        assessment = engine.assess_sql("UPDATE users SET status = 'inactive'")
        
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.is_executable is False
    
    def test_assess_sql_high_risk_truncate(self):
        """Test assessing TRUNCATE TABLE as high risk"""
        engine = RiskEngine()
        assessment = engine.assess_sql("TRUNCATE TABLE users")
        
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.is_executable is False
    
    def test_assess_sql_high_risk_grant(self):
        """Test assessing GRANT as high risk"""
        engine = RiskEngine()
        assessment = engine.assess_sql("GRANT ALL PRIVILEGES ON users TO public")
        
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.is_executable is False
    
    def test_assess_sql_medium_risk_select_star(self):
        """Test assessing SELECT * as medium risk"""
        engine = RiskEngine()
        assessment = engine.assess_sql("SELECT * FROM users")
        
        assert assessment.risk_level == RiskLevel.MEDIUM
        assert assessment.is_executable is True
        assert assessment.requires_warning is True
        assert "SELECT *" in assessment.message
    
    def test_assess_sql_medium_risk_like_wildcard(self):
        """Test assessing LIKE with prefix wildcard as medium risk"""
        engine = RiskEngine()
        assessment = engine.assess_sql("SELECT * FROM users WHERE name LIKE '%john%'")
        
        assert assessment.risk_level == RiskLevel.MEDIUM
        assert assessment.is_executable is True
    
    def test_assess_sql_low_risk_safe_select(self):
        """Test assessing safe SELECT as low risk"""
        engine = RiskEngine()
        assessment = engine.assess_sql("SELECT id, name FROM users WHERE id = 1")
        
        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.is_executable is True
        assert assessment.requires_warning is False
    
    def test_assess_sql_safe_health_check(self):
        """Test assessing health check as safe"""
        engine = RiskEngine()
        assessment = engine.assess_sql("SELECT 1")
        
        assert assessment.risk_level == RiskLevel.SAFE
        assert assessment.is_executable is True
    
    def test_assess_sql_case_insensitive(self):
        """Test that risk assessment is case insensitive"""
        engine = RiskEngine()
        
        # Test uppercase
        assessment1 = engine.assess_sql("DROP TABLE users")
        # Test lowercase
        assessment2 = engine.assess_sql("drop table users")
        # Test mixed case
        assessment3 = engine.assess_sql("Drop Table users")
        
        assert assessment1.risk_level == RiskLevel.HIGH
        assert assessment2.risk_level == RiskLevel.HIGH
        assert assessment3.risk_level == RiskLevel.HIGH
    
    def test_assess_sql_with_comments(self):
        """Test assessing SQL with comments"""
        engine = RiskEngine()
        sql = """
        -- This is a comment
        SELECT * FROM users
        /* Multi-line comment */
        WHERE id = 1
        """
        assessment = engine.assess_sql(sql)
        
        # Should still detect SELECT * even with comments
        assert assessment.risk_level == RiskLevel.MEDIUM
    
    def test_get_rules_summary(self):
        """Test getting rules summary"""
        engine = RiskEngine()
        summary = engine.get_rules_summary()
        
        assert "total_rules" in summary
        assert "by_level" in summary
        assert "enabled_rules" in summary
        assert "disabled_rules" in summary
        assert summary["total_rules"] > 0
    
    def test_validate_rules(self):
        """Test validating rules"""
        engine = RiskEngine()
        issues = engine.validate_rules()
        
        # Default rules should have no issues
        assert len(issues) == 0
    
    def test_validate_rules_invalid_pattern(self):
        """Test validating rules with invalid pattern"""
        # The invalid pattern should raise an error during initialization
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            invalid_rule = RiskRule(
                name="invalid",
                pattern=r"[invalid",
                level=RiskLevel.HIGH,
                message="Invalid"
            )
    
    def test_export_rules_yaml(self):
        """Test exporting rules as YAML"""
        engine = RiskEngine()
        yaml_str = engine.export_rules("yaml")
        
        assert "risk_rules" in yaml_str
        assert "high_risk" in yaml_str
        assert "medium_risk" in yaml_str
    
    def test_export_rules_json(self):
        """Test exporting rules as JSON"""
        engine = RiskEngine()
        json_str = engine.export_rules("json")
        
        import json
        data = json.loads(json_str)
        assert "risk_rules" in data
        assert "high_risk" in data["risk_rules"]
    
    def test_export_rules_invalid_format(self):
        """Test exporting rules with invalid format"""
        engine = RiskEngine()
        
        with pytest.raises(ValueError, match="Unsupported format"):
            engine.export_rules("xml")