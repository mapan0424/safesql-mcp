"""
增强的规则引擎模块
"""

import re
import time
from typing import List, Dict, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading


class RulePriority(Enum):
    """规则优先级"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4


class RuleCategory(Enum):
    """规则类别"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    SYNTAX = "syntax"
    BEST_PRACTICE = "best_practice"
    CUSTOM = "custom"


@dataclass
class EnhancedRule:
    """增强的规则定义"""
    name: str
    pattern: str
    level: str  # high, medium, low, safe
    message: str
    description: Optional[str] = None
    enabled: bool = True
    priority: RulePriority = RulePriority.MEDIUM
    category: RuleCategory = RuleCategory.CUSTOM
    tags: Set[str] = field(default_factory=set)
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 规则组合
    requires: List[str] = field(default_factory=list)  # 依赖的规则
    conflicts_with: List[str] = field(default_factory=list)  # 冲突的规则
    
    # 动态规则
    is_dynamic: bool = False
    dynamic_checker: Optional[Callable] = None
    
    # 编译后的正则表达式
    _compiled_pattern: Optional[re.Pattern] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """编译正则表达式"""
        try:
            self._compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{self.pattern}': {e}")
    
    def matches(self, sql: str) -> bool:
        """检查 SQL 是否匹配此规则"""
        if not self.enabled:
            return False
        
        # 动态规则检查
        if self.is_dynamic and self.dynamic_checker:
            return self.dynamic_checker(sql)
        
        # 正则表达式匹配
        if self._compiled_pattern:
            return bool(self._compiled_pattern.search(sql))
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "pattern": self.pattern,
            "level": self.level,
            "message": self.message,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority.value,
            "category": self.category.value,
            "tags": list(self.tags),
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "requires": self.requires,
            "conflicts_with": self.conflicts_with,
            "is_dynamic": self.is_dynamic
        }


class RuleGroup:
    """规则组"""
    
    def __init__(self, name: str, description: str = ""):
        """
        初始化规则组
        
        Args:
            name: 组名称
            description: 组描述
        """
        self.name = name
        self.description = description
        self.rules: List[EnhancedRule] = []
        self.enabled = True
    
    def add_rule(self, rule: EnhancedRule) -> None:
        """添加规则到组"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str) -> bool:
        """从组中移除规则"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False
    
    def get_enabled_rules(self) -> List[EnhancedRule]:
        """获取启用的规则"""
        if not self.enabled:
            return []
        return [rule for rule in self.rules if rule.enabled]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "rules": [rule.to_dict() for rule in self.rules]
        }


class EnhancedRuleEngine:
    """增强的规则引擎"""
    
    def __init__(self):
        """初始化规则引擎"""
        self.rules: Dict[str, EnhancedRule] = {}
        self.rule_groups: Dict[str, RuleGroup] = {}
        self._lock = threading.RLock()
        
        # 规则索引
        self._rules_by_level: Dict[str, List[EnhancedRule]] = defaultdict(list)
        self._rules_by_category: Dict[RuleCategory, List[EnhancedRule]] = defaultdict(list)
        self._rules_by_priority: Dict[RulePriority, List[EnhancedRule]] = defaultdict(list)
        self._rules_by_tag: Dict[str, List[EnhancedRule]] = defaultdict(list)
        
        # 规则缓存
        self._rule_cache: Dict[str, List[EnhancedRule]] = {}
        self._cache_valid = False
        
        # 统计信息
        self._stats = {
            "total_rules": 0,
            "enabled_rules": 0,
            "disabled_rules": 0,
            "matches": 0,
            "last_match_time": None
        }
    
    def add_rule(self, rule: EnhancedRule) -> None:
        """
        添加规则
        
        Args:
            rule: 增强规则
        """
        with self._lock:
            # 检查规则冲突
            if self._has_conflicts(rule):
                raise ValueError(f"Rule '{rule.name}' conflicts with existing rules")
            
            # 添加规则
            self.rules[rule.name] = rule
            
            # 更新索引
            self._update_indexes(rule)
            
            # 使缓存失效
            self._cache_valid = False
            
            # 更新统计
            self._update_stats()
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        移除规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if rule_name not in self.rules:
                return False
            
            rule = self.rules[rule_name]
            
            # 检查是否有其他规则依赖此规则
            for other_rule in self.rules.values():
                if rule_name in other_rule.requires:
                    raise ValueError(f"Cannot remove rule '{rule_name}': it is required by '{other_rule.name}'")
            
            # 移除规则
            del self.rules[rule_name]
            
            # 更新索引
            self._remove_from_indexes(rule)
            
            # 使缓存失效
            self._cache_valid = False
            
            # 更新统计
            self._update_stats()
            
            return True
    
    def update_rule(self, rule_name: str, updates: Dict[str, Any]) -> bool:
        """
        更新规则
        
        Args:
            rule_name: 规则名称
            updates: 更新内容
            
        Returns:
            bool: 是否成功更新
        """
        with self._lock:
            if rule_name not in self.rules:
                return False
            
            rule = self.rules[rule_name]
            
            # 更新规则属性
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            # 更新时间戳
            rule.updated_at = time.time()
            
            # 重新编译正则表达式
            if "pattern" in updates:
                try:
                    rule._compiled_pattern = re.compile(rule.pattern, re.IGNORECASE)
                except re.error as e:
                    raise ValueError(f"Invalid regex pattern '{rule.pattern}': {e}")
            
            # 更新索引
            self._remove_from_indexes(rule)
            self._update_indexes(rule)
            
            # 使缓存失效
            self._cache_valid = False
            
            return True
    
    def enable_rule(self, rule_name: str) -> bool:
        """
        启用规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            bool: 是否成功启用
        """
        return self.update_rule(rule_name, {"enabled": True})
    
    def disable_rule(self, rule_name: str) -> bool:
        """
        禁用规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            bool: 是否成功禁用
        """
        return self.update_rule(rule_name, {"enabled": False})
    
    def add_rule_group(self, group: RuleGroup) -> None:
        """
        添加规则组
        
        Args:
            group: 规则组
        """
        with self._lock:
            self.rule_groups[group.name] = group
            
            # 添加组中的规则
            for rule in group.rules:
                if rule.name not in self.rules:
                    self.add_rule(rule)
    
    def remove_rule_group(self, group_name: str) -> bool:
        """
        移除规则组
        
        Args:
            group_name: 组名称
            
        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if group_name not in self.rule_groups:
                return False
            
            group = self.rule_groups[group_name]
            
            # 移除组中的规则
            for rule in group.rules:
                self.remove_rule(rule.name)
            
            # 移除组
            del self.rule_groups[group_name]
            
            return True
    
    def get_rules_for_sql(self, sql: str) -> List[EnhancedRule]:
        """
        获取匹配 SQL 的规则
        
        Args:
            sql: SQL 语句
            
        Returns:
            List[EnhancedRule]: 匹配的规则列表
        """
        with self._lock:
            # 检查缓存
            if self._cache_valid and sql in self._rule_cache:
                return self._rule_cache[sql]
            
            # 获取所有启用的规则
            enabled_rules = [rule for rule in self.rules.values() if rule.enabled]
            
            # 按优先级排序
            enabled_rules.sort(key=lambda r: r.priority.value)
            
            # 匹配规则
            matching_rules = []
            for rule in enabled_rules:
                if rule.matches(sql):
                    matching_rules.append(rule)
            
            # 更新缓存
            self._rule_cache[sql] = matching_rules
            self._cache_valid = True
            
            # 更新统计
            self._stats["matches"] += 1
            self._stats["last_match_time"] = time.time()
            
            return matching_rules
    
    def get_rules_by_level(self, level: str) -> List[EnhancedRule]:
        """
        获取指定风险等级的规则
        
        Args:
            level: 风险等级
            
        Returns:
            List[EnhancedRule]: 规则列表
        """
        with self._lock:
            return [rule for rule in self._rules_by_level.get(level, []) if rule.enabled]
    
    def get_rules_by_category(self, category: RuleCategory) -> List[EnhancedRule]:
        """
        获取指定类别的规则
        
        Args:
            category: 规则类别
            
        Returns:
            List[EnhancedRule]: 规则列表
        """
        with self._lock:
            return [rule for rule in self._rules_by_category.get(category, []) if rule.enabled]
    
    def get_rules_by_priority(self, priority: RulePriority) -> List[EnhancedRule]:
        """
        获取指定优先级的规则
        
        Args:
            priority: 规则优先级
            
        Returns:
            List[EnhancedRule]: 规则列表
        """
        with self._lock:
            return [rule for rule in self._rules_by_priority.get(priority, []) if rule.enabled]
    
    def get_rules_by_tag(self, tag: str) -> List[EnhancedRule]:
        """
        获取指定标签的规则
        
        Args:
            tag: 标签
            
        Returns:
            List[EnhancedRule]: 规则列表
        """
        with self._lock:
            return [rule for rule in self._rules_by_tag.get(tag, []) if rule.enabled]
    
    def validate_rules(self) -> List[Dict[str, Any]]:
        """
        验证所有规则
        
        Returns:
            List[Dict]: 验证结果
        """
        issues = []
        
        for rule in self.rules.values():
            # 检查正则表达式
            try:
                re.compile(rule.pattern, re.IGNORECASE)
            except re.error as e:
                issues.append({
                    "rule": rule.name,
                    "issue": f"Invalid regex pattern: {e}",
                    "pattern": rule.pattern
                })
            
            # 检查依赖规则是否存在
            for dep in rule.requires:
                if dep not in self.rules:
                    issues.append({
                        "rule": rule.name,
                        "issue": f"Missing dependency: {dep}",
                        "dependency": dep
                    })
        
        return issues
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        with self._lock:
            return {
                **self._stats,
                "total_rules": len(self.rules),
                "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
                "disabled_rules": sum(1 for r in self.rules.values() if not r.enabled),
                "rule_groups": len(self.rule_groups),
                "by_level": {
                    level: len(rules) 
                    for level, rules in self._rules_by_level.items()
                },
                "by_category": {
                    category.value: len(rules) 
                    for category, rules in self._rules_by_category.items()
                },
                "by_priority": {
                    priority.value: len(rules) 
                    for priority, rules in self._rules_by_priority.items()
                }
            }
    
    def export_rules(self, format: str = "yaml") -> str:
        """
        导出规则配置
        
        Args:
            format: 导出格式 (yaml, json)
            
        Returns:
            str: 规则配置
        """
        if format == "yaml":
            return self._export_yaml()
        elif format == "json":
            return self._export_json()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _has_conflicts(self, new_rule: EnhancedRule) -> bool:
        """检查规则冲突"""
        for existing_rule in self.rules.values():
            # 检查名称冲突
            if existing_rule.name == new_rule.name:
                return True
            
            # 检查显式冲突
            if new_rule.name in existing_rule.conflicts_with:
                return True
            if existing_rule.name in new_rule.conflicts_with:
                return True
        
        return False
    
    def _update_indexes(self, rule: EnhancedRule) -> None:
        """更新规则索引"""
        # 按等级索引
        self._rules_by_level[rule.level].append(rule)
        
        # 按类别索引
        self._rules_by_category[rule.category].append(rule)
        
        # 按优先级索引
        self._rules_by_priority[rule.priority].append(rule)
        
        # 按标签索引
        for tag in rule.tags:
            self._rules_by_tag[tag].append(rule)
    
    def _remove_from_indexes(self, rule: EnhancedRule) -> None:
        """从索引中移除规则"""
        # 按等级索引
        if rule.level in self._rules_by_level:
            self._rules_by_level[rule.level] = [
                r for r in self._rules_by_level[rule.level] if r.name != rule.name
            ]
        
        # 按类别索引
        if rule.category in self._rules_by_category:
            self._rules_by_category[rule.category] = [
                r for r in self._rules_by_category[rule.category] if r.name != rule.name
            ]
        
        # 按优先级索引
        if rule.priority in self._rules_by_priority:
            self._rules_by_priority[rule.priority] = [
                r for r in self._rules_by_priority[rule.priority] if r.name != rule.name
            ]
        
        # 按标签索引
        for tag in rule.tags:
            if tag in self._rules_by_tag:
                self._rules_by_tag[tag] = [
                    r for r in self._rules_by_tag[tag] if r.name != rule.name
                ]
    
    def _update_stats(self) -> None:
        """更新统计信息"""
        self._stats["total_rules"] = len(self.rules)
        self._stats["enabled_rules"] = sum(1 for r in self.rules.values() if r.enabled)
        self._stats["disabled_rules"] = sum(1 for r in self.rules.values() if not r.enabled)
    
    def _export_yaml(self) -> str:
        """导出为 YAML 格式"""
        import yaml
        
        rules_dict = {
            "rules": [rule.to_dict() for rule in self.rules.values()],
            "rule_groups": [group.to_dict() for group in self.rule_groups.values()]
        }
        
        return yaml.dump(rules_dict, default_flow_style=False)
    
    def _export_json(self) -> str:
        """导出为 JSON 格式"""
        import json
        
        rules_dict = {
            "rules": [rule.to_dict() for rule in self.rules.values()],
            "rule_groups": [group.to_dict() for group in self.rule_groups.values()]
        }
        
        return json.dumps(rules_dict, indent=2)