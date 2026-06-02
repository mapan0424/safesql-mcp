"""
风险规则定义和风险等级评估
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Pattern
import re


class RiskLevel(Enum):
    """SQL 风险等级"""
    HIGH = "high"      # 高风险：自动拦截
    MEDIUM = "medium"  # 中风险：警告但允许执行
    LOW = "low"        # 低风险：直接执行
    SAFE = "safe"      # 安全：白名单，忽略检查


@dataclass
class RiskRule:
    """风险规则定义"""
    name: str
    pattern: str
    level: RiskLevel
    message: str
    description: Optional[str] = None
    enabled: bool = True
    
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
        return bool(self._compiled_pattern.search(sql))


@dataclass
class RiskAssessment:
    """SQL 风险评估结果"""
    sql: str
    risk_level: RiskLevel
    message: str
    matched_rule: Optional[RiskRule] = None
    suggestions: List[str] = None
    explain_plan: Optional[str] = None
    performance_warnings: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.performance_warnings is None:
            self.performance_warnings = []
    
    @property
    def is_executable(self) -> bool:
        """是否可以执行（非高风险）"""
        return self.risk_level != RiskLevel.HIGH
    
    @property
    def requires_warning(self) -> bool:
        """是否需要警告（中风险）"""
        return self.risk_level == RiskLevel.MEDIUM
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "sql": self.sql,
            "risk_level": self.risk_level.value,
            "message": self.message,
            "matched_rule": self.matched_rule.name if self.matched_rule else None,
            "suggestions": self.suggestions,
            "explain_plan": self.explain_plan,
            "performance_warnings": self.performance_warnings,
            "is_executable": self.is_executable,
            "requires_warning": self.requires_warning,
        }


class DefaultRiskRules:
    """默认风险规则集"""
    
    @staticmethod
    def get_high_risk_rules() -> List[RiskRule]:
        """获取高风险规则"""
        return [
            RiskRule(
                name="drop_table",
                pattern=r"DROP\s+TABLE",
                level=RiskLevel.HIGH,
                message="DROP TABLE 操作被禁止",
                description="删除表操作可能导致数据丢失"
            ),
            RiskRule(
                name="drop_database",
                pattern=r"DROP\s+DATABASE",
                level=RiskLevel.HIGH,
                message="DROP DATABASE 操作被禁止",
                description="删除数据库操作极其危险"
            ),
            RiskRule(
                name="drop_index",
                pattern=r"DROP\s+INDEX",
                level=RiskLevel.HIGH,
                message="DROP INDEX 操作被禁止",
                description="删除索引可能影响查询性能"
            ),
            RiskRule(
                name="truncate_table",
                pattern=r"TRUNCATE\s+TABLE",
                level=RiskLevel.HIGH,
                message="TRUNCATE TABLE 操作被禁止",
                description="清空表操作不可恢复"
            ),
            RiskRule(
                name="delete_without_where",
                pattern=r"DELETE\s+FROM\s+\S+\s*$",
                level=RiskLevel.HIGH,
                message="DELETE 操作缺少 WHERE 条件",
                description="无条件删除将影响所有行"
            ),
            RiskRule(
                name="update_without_where",
                pattern=r"UPDATE\s+\S+\s+SET\s+(?!.*WHERE\s+).*$",
                level=RiskLevel.HIGH,
                message="UPDATE 操作缺少 WHERE 条件",
                description="无条件更新将影响所有行"
            ),
            RiskRule(
                name="grant_revoke",
                pattern=r"(GRANT|REVOKE)\s+",
                level=RiskLevel.HIGH,
                message="权限操作被禁止",
                description="权限修改需要管理员授权"
            ),
            RiskRule(
                name="alter_table_drop_column",
                pattern=r"ALTER\s+TABLE\s+.*\s+DROP\s+COLUMN",
                level=RiskLevel.HIGH,
                message="删除列操作被禁止",
                description="删除列可能导致数据丢失"
            ),
            RiskRule(
                name="system_tables",
                pattern=r"SELECT\s+.*\s+FROM\s+(information_schema|pg_catalog|mysql\.|sys\.)",
                level=RiskLevel.HIGH,
                message="系统表访问被禁止",
                description="禁止访问系统表以保护元数据安全"
            ),
            RiskRule(
                name="stored_procedures",
                pattern=r"(EXEC|EXECUTE|CALL)\s+",
                level=RiskLevel.HIGH,
                message="存储过程执行被禁止",
                description="存储过程可能包含危险操作"
            ),
        ]
    
    @staticmethod
    def get_medium_risk_rules() -> List[RiskRule]:
        """获取中风险规则"""
        return [
            RiskRule(
                name="select_all",
                pattern=r"SELECT\s+\*\s+FROM",
                level=RiskLevel.MEDIUM,
                message="建议避免使用 SELECT *，请指定具体列",
                description="SELECT * 会返回所有列，可能影响性能"
            ),
            RiskRule(
                name="insert_without_columns",
                pattern=r"INSERT\s+INTO\s+[^\s(]+\s+VALUES",
                level=RiskLevel.MEDIUM,
                message="建议使用 INSERT INTO ... (columns) VALUES 语法",
                description="显式指定列名可以提高可维护性"
            ),
            RiskRule(
                name="like_prefix_wildcard",
                pattern=r"LIKE\s+'%",
                level=RiskLevel.MEDIUM,
                message="前缀通配符 LIKE '%...' 可能导致全表扫描",
                description="前缀通配符无法使用索引"
            ),
            RiskRule(
                name="multiple_joins",
                pattern=r"(JOIN\s+.*\s+ON.*){3,}",
                level=RiskLevel.MEDIUM,
                message="多表 JOIN 可能影响查询性能",
                description="复杂的多表连接需要优化"
            ),
            RiskRule(
                name="subquery_in_where",
                pattern=r"WHERE\s+.*\s+IN\s*\(\s*SELECT",
                level=RiskLevel.MEDIUM,
                message="WHERE 子查询可能影响性能",
                description="考虑使用 JOIN 替代子查询"
            ),
            RiskRule(
                name="or_conditions",
                pattern=r"WHERE\s+.*\s+OR\s+.*\s+OR\s+.*\s+OR",
                level=RiskLevel.MEDIUM,
                message="多个 OR 条件可能影响索引使用",
                description="考虑使用 IN 或 UNION 替代多个 OR"
            ),
            RiskRule(
                name="not_indexed_where",
                pattern=r"WHERE\s+.*\s+LIKE\s+'[^%]",
                level=RiskLevel.MEDIUM,
                message="LIKE 查询可能无法使用索引",
                description="确保 LIKE 查询的列有合适的索引"
            ),
        ]
    
    @staticmethod
    def get_low_risk_rules() -> List[RiskRule]:
        """获取低风险规则"""
        return [
            RiskRule(
                name="safe_select",
                pattern=r"SELECT\s+.*\s+FROM\s+.*\s+WHERE",
                level=RiskLevel.LOW,
                message="安全查询",
                description="带 WHERE 条件的 SELECT 查询"
            ),
            RiskRule(
                name="safe_insert",
                pattern=r"INSERT\s+INTO\s+.*\s+\([^)]+\)\s+VALUES",
                level=RiskLevel.LOW,
                message="安全插入",
                description="指定列名的 INSERT 操作"
            ),
            RiskRule(
                name="safe_update",
                pattern=r"UPDATE\s+.*\s+SET\s+.*\s+WHERE\s+",
                level=RiskLevel.LOW,
                message="安全更新",
                description="带 WHERE 条件的 UPDATE 操作"
            ),
            RiskRule(
                name="safe_delete",
                pattern=r"DELETE\s+FROM\s+.*\s+WHERE\s+",
                level=RiskLevel.LOW,
                message="安全删除",
                description="带 WHERE 条件的 DELETE 操作"
            ),
        ]
    
    @staticmethod
    def get_whitelist_rules() -> List[RiskRule]:
        """获取白名单规则（忽略风险检查）"""
        return [
            RiskRule(
                name="health_check",
                pattern=r"SELECT\s+1",
                level=RiskLevel.SAFE,
                message="健康检查查询",
                description="数据库健康检查查询"
            ),
            RiskRule(
                name="version_check",
                pattern=r"SELECT\s+version\(\)",
                level=RiskLevel.SAFE,
                message="版本查询",
                description="数据库版本查询"
            ),
            RiskRule(
                name="current_time",
                pattern=r"SELECT\s+(NOW\(\)|CURRENT_TIMESTAMP|CURRENT_DATE)",
                level=RiskLevel.SAFE,
                message="时间查询",
                description="获取当前时间"
            ),
        ]
    
    @classmethod
    def get_all_rules(cls) -> List[RiskRule]:
        """获取所有默认规则"""
        rules = []
        rules.extend(cls.get_high_risk_rules())
        rules.extend(cls.get_medium_risk_rules())
        rules.extend(cls.get_low_risk_rules())
        rules.extend(cls.get_whitelist_rules())
        return rules