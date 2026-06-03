"""
SQL 风险审查引擎
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .rules import RiskLevel, RiskRule, RiskAssessment, DefaultRiskRules
from .analyzer import SQLAnalyzer
from .injection import SQLInjectionDetector, InjectionRiskLevel


class RiskEngine:
    """SQL 风险审查引擎"""
    
    def __init__(self, custom_rules: Optional[List[RiskRule]] = None, enable_injection_detection: bool = True):
        """
        初始化风险引擎
        
        Args:
            custom_rules: 自定义规则列表，如果为 None 则使用默认规则
            enable_injection_detection: 是否启用注入检测
        """
        self.analyzer = SQLAnalyzer()
        
        # 加载规则
        if custom_rules is not None:
            self.rules = custom_rules
        else:
            self.rules = DefaultRiskRules.get_all_rules()
        
        # 按风险等级分组规则
        self._rules_by_level: Dict[RiskLevel, List[RiskRule]] = {
            RiskLevel.HIGH: [],
            RiskLevel.MEDIUM: [],
            RiskLevel.LOW: [],
            RiskLevel.SAFE: [],
        }
        
        for rule in self.rules:
            self._rules_by_level[rule.level].append(rule)
        
        # 初始化注入检测器
        self.injection_detector = SQLInjectionDetector() if enable_injection_detection else None
    
    def add_rule(self, rule: RiskRule) -> None:
        """添加单个规则"""
        self.rules.append(rule)
        self._rules_by_level[rule.level].append(rule)
    
    def add_rules(self, rules: List[RiskRule]) -> None:
        """批量添加规则"""
        for rule in rules:
            self.add_rule(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除规则"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                self._rules_by_level[rule.level].remove(rule)
                return True
        return False
    
    def assess_sql(self, sql: str, database_type: str = "postgresql") -> RiskAssessment:
        """
        评估 SQL 语句的风险等级
        
        Args:
            sql: SQL 语句
            database_type: 数据库类型 (postgresql, mysql)
            
        Returns:
            RiskAssessment: 风险评估结果
        """
        # 预处理 SQL
        cleaned_sql = self._preprocess_sql(sql)
        
        # 检查白名单
        for rule in self._rules_by_level[RiskLevel.SAFE]:
            if rule.matches(cleaned_sql):
                return RiskAssessment(
                    sql=sql,
                    risk_level=RiskLevel.SAFE,
                    message=rule.message,
                    matched_rule=rule,
                    suggestions=[],
                    explain_plan=None,
                    performance_warnings=[]
                )
        
        # 检查高风险规则
        for rule in self._rules_by_level[RiskLevel.HIGH]:
            if rule.matches(cleaned_sql):
                return RiskAssessment(
                    sql=sql,
                    risk_level=RiskLevel.HIGH,
                    message=rule.message,
                    matched_rule=rule,
                    suggestions=[self._get_suggestion(rule)],
                    explain_plan=None,
                    performance_warnings=[]
                )
        
        # 检查注入风险
        if self.injection_detector:
            injection_risks = self.injection_detector.detect(sql)
            if injection_risks:
                # 获取最高风险等级
                highest_risk = self.injection_detector.get_highest_risk_level(sql)
                
                # 映射到风险等级
                risk_level_mapping = {
                    InjectionRiskLevel.LOW: RiskLevel.LOW,
                    InjectionRiskLevel.MEDIUM: RiskLevel.MEDIUM,
                    InjectionRiskLevel.HIGH: RiskLevel.HIGH,
                    InjectionRiskLevel.CRITICAL: RiskLevel.HIGH,
                }
                
                risk_level = risk_level_mapping.get(highest_risk, RiskLevel.MEDIUM)
                
                # 构建消息
                messages = [risk["message"] for risk in injection_risks]
                message = "注入风险检测: " + "; ".join(messages)
                
                # 构建建议
                suggestions = [
                    "使用参数化查询替代字符串拼接",
                    "对用户输入进行严格的验证和过滤",
                    "使用最小权限原则配置数据库用户"
                ]
                
                return RiskAssessment(
                    sql=sql,
                    risk_level=risk_level,
                    message=message,
                    matched_rule=None,
                    suggestions=suggestions,
                    explain_plan=None,
                    performance_warnings=[]
                )
        
        # 检查中风险规则
        medium_risk_messages = []
        medium_risk_suggestions = []
        for rule in self._rules_by_level[RiskLevel.MEDIUM]:
            if rule.matches(cleaned_sql):
                medium_risk_messages.append(rule.message)
                medium_risk_suggestions.append(self._get_suggestion(rule))
        
        if medium_risk_messages:
            return RiskAssessment(
                sql=sql,
                risk_level=RiskLevel.MEDIUM,
                message="; ".join(medium_risk_messages),
                matched_rule=None,
                suggestions=medium_risk_suggestions,
                explain_plan=None,
                performance_warnings=[]
            )
        
        # 检查低风险规则
        for rule in self._rules_by_level[RiskLevel.LOW]:
            if rule.matches(cleaned_sql):
                return RiskAssessment(
                    sql=sql,
                    risk_level=RiskLevel.LOW,
                    message=rule.message,
                    matched_rule=rule,
                    suggestions=[],
                    explain_plan=None,
                    performance_warnings=[]
                )
        
        # 如果没有匹配任何规则，进行深度分析
        return self._deep_analysis(sql, database_type)
    
    def _preprocess_sql(self, sql: str) -> str:
        """预处理 SQL 语句"""
        # 去除注释
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # 标准化空白字符
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        # 去除末尾分号
        sql = sql.rstrip(';').strip()
        
        return sql
    
    def _deep_analysis(self, sql: str, database_type: str) -> RiskAssessment:
        """深度 SQL 分析"""
        analysis = self.analyzer.analyze(sql, database_type)
        
        # 基于分析结果评估风险
        risk_level = RiskLevel.LOW
        message = "安全查询"
        suggestions = []
        performance_warnings = []
        
        # 检查性能问题
        if analysis.has_performance_issues:
            risk_level = RiskLevel.MEDIUM
            message = "查询可能存在性能问题"
            performance_warnings = analysis.performance_warnings
            suggestions = analysis.optimization_suggestions
        
        # 检查语法问题
        if analysis.has_syntax_issues:
            risk_level = RiskLevel.MEDIUM
            message = "SQL 语法可能存在问题"
            suggestions.extend(analysis.syntax_suggestions)
        
        return RiskAssessment(
            sql=sql,
            risk_level=risk_level,
            message=message,
            matched_rule=None,
            suggestions=suggestions,
            explain_plan=None,
            performance_warnings=performance_warnings
        )
    
    def _get_suggestion(self, rule: RiskRule) -> str:
        """根据规则生成优化建议"""
        suggestions = {
            "select_all": "建议明确指定需要的列名，而不是使用 SELECT *",
            "insert_without_columns": "建议在 INSERT 语句中明确指定列名",
            "like_prefix_wildcard": "考虑使用全文索引或其他搜索方案替代前缀通配符",
            "multiple_joins": "考虑优化 JOIN 条件，确保有合适的索引",
            "subquery_in_where": "考虑使用 JOIN 或临时表替代子查询",
            "or_conditions": "考虑使用 IN 或 UNION 替代多个 OR 条件",
            "not_indexed_where": "确保 WHERE 条件中的列有合适的索引",
            "drop_table": "如果需要删除表，请确保已备份数据并获得授权",
            "drop_database": "数据库删除操作极其危险，请确认并获得管理员授权",
            "truncate_table": "如果需要清空表，请考虑使用 DELETE 并添加 WHERE 条件",
            "delete_without_where": "添加 WHERE 条件以限制删除范围",
            "update_without_where": "添加 WHERE 条件以限制更新范围",
        }
        
        return suggestions.get(rule.name, rule.description or "请检查 SQL 语句的安全性")
    
    def validate_rules(self) -> List[Dict[str, Any]]:
        """验证所有规则的有效性"""
        issues = []
        
        for rule in self.rules:
            try:
                # 测试正则表达式是否有效
                re.compile(rule.pattern, re.IGNORECASE)
            except re.error as e:
                issues.append({
                    "rule": rule.name,
                    "issue": f"Invalid regex pattern: {e}",
                    "pattern": rule.pattern
                })
        
        return issues
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """获取规则摘要"""
        summary = {
            "total_rules": len(self.rules),
            "by_level": {
                "high": len(self._rules_by_level[RiskLevel.HIGH]),
                "medium": len(self._rules_by_level[RiskLevel.MEDIUM]),
                "low": len(self._rules_by_level[RiskLevel.LOW]),
                "safe": len(self._rules_by_level[RiskLevel.SAFE]),
            },
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "disabled_rules": sum(1 for r in self.rules if not r.enabled),
        }
        
        # 添加注入检测统计
        if self.injection_detector:
            summary["injection_detection"] = self.injection_detector.get_stats()
        
        return summary
    
    def export_rules(self, format: str = "yaml") -> str:
        """导出规则配置"""
        if format == "yaml":
            return self._export_yaml()
        elif format == "json":
            return self._export_json()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_yaml(self) -> str:
        """导出为 YAML 格式"""
        import yaml
        
        rules_dict = {
            "risk_rules": {
                "high_risk": [],
                "medium_risk": [],
                "low_risk": [],
                "whitelist": []
            }
        }
        
        for rule in self.rules:
            rule_dict = {
                "name": rule.name,
                "pattern": rule.pattern,
                "message": rule.message,
                "description": rule.description,
                "enabled": rule.enabled
            }
            
            if rule.level == RiskLevel.HIGH:
                rules_dict["risk_rules"]["high_risk"].append(rule_dict)
            elif rule.level == RiskLevel.MEDIUM:
                rules_dict["risk_rules"]["medium_risk"].append(rule_dict)
            elif rule.level == RiskLevel.LOW:
                rules_dict["risk_rules"]["low_risk"].append(rule_dict)
            elif rule.level == RiskLevel.SAFE:
                rules_dict["risk_rules"]["whitelist"].append(rule_dict)
        
        return yaml.dump(rules_dict, default_flow_style=False)
    
    def _export_json(self) -> str:
        """导出为 JSON 格式"""
        import json
        
        rules_dict = {
            "risk_rules": {
                "high_risk": [],
                "medium_risk": [],
                "low_risk": [],
                "whitelist": []
            }
        }
        
        for rule in self.rules:
            rule_dict = {
                "name": rule.name,
                "pattern": rule.pattern,
                "message": rule.message,
                "description": rule.description,
                "enabled": rule.enabled
            }
            
            if rule.level == RiskLevel.HIGH:
                rules_dict["risk_rules"]["high_risk"].append(rule_dict)
            elif rule.level == RiskLevel.MEDIUM:
                rules_dict["risk_rules"]["medium_risk"].append(rule_dict)
            elif rule.level == RiskLevel.LOW:
                rules_dict["risk_rules"]["low_risk"].append(rule_dict)
            elif rule.level == RiskLevel.SAFE:
                rules_dict["risk_rules"]["whitelist"].append(rule_dict)
        
        return json.dumps(rules_dict, indent=2)