"""
SQL 注入检测模块
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class InjectionRiskLevel(Enum):
    """注入风险等级"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class InjectionPattern:
    """注入模式定义"""
    name: str
    pattern: str
    risk_level: InjectionRiskLevel
    message: str
    description: str
    enabled: bool = True


class SQLInjectionDetector:
    """SQL 注入检测器"""
    
    def __init__(self):
        """初始化注入检测器"""
        self.patterns = self._load_default_patterns()
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        
        # 预编译所有模式
        for pattern in self.patterns:
            try:
                self._compiled_patterns[pattern.name] = re.compile(
                    pattern.pattern, 
                    re.IGNORECASE | re.DOTALL
                )
            except re.error:
                # 忽略无效的正则表达式
                pass
    
    def _load_default_patterns(self) -> List[InjectionPattern]:
        """加载默认注入模式"""
        return [
            # 基于注释的注入
            InjectionPattern(
                name="comment_injection",
                pattern=r"(--|#|/\*|\*/)",
                risk_level=InjectionRiskLevel.MEDIUM,
                message="检测到 SQL 注释，可能存在注入风险",
                description="SQL 注释可用于绕过安全检查"
            ),
            
            # 基于 UNION 的注入
            InjectionPattern(
                name="union_injection",
                pattern=r"UNION\s+(ALL\s+)?SELECT",
                risk_level=InjectionRiskLevel.HIGH,
                message="检测到 UNION SELECT，可能存在注入攻击",
                description="UNION SELECT 可用于获取其他表的数据"
            ),
            
            # 基于布尔的注入
            InjectionPattern(
                name="boolean_injection",
                pattern=r"(AND|OR)\s+\d+\s*=\s*\d+",
                risk_level=InjectionRiskLevel.MEDIUM,
                message="检测到布尔条件，可能存在盲注",
                description="布尔条件可用于盲注攻击"
            ),
            
            # 基于时间的注入
            InjectionPattern(
                name="time_based_injection",
                pattern=r"(SLEEP|BENCHMARK|WAITFOR|DELAY|pg_sleep)\s*\(",
                risk_level=InjectionRiskLevel.HIGH,
                message="检测到时间延迟函数，可能存在时间盲注",
                description="时间延迟函数可用于时间盲注攻击"
            ),
            
            # 基于错误的注入
            InjectionPattern(
                name="error_based_injection",
                pattern=r"(EXTRACTVALUE|UPDATEXML|EXP|FLOOR|RAND|COUNT|GROUP\s+BY)\s*\(",
                risk_level=InjectionRiskLevel.MEDIUM,
                message="检测到错误处理函数，可能存在报错注入",
                description="错误处理函数可用于报错注入攻击"
            ),
            
            # 堆叠查询注入
            InjectionPattern(
                name="stacked_queries",
                pattern=r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC)",
                risk_level=InjectionRiskLevel.CRITICAL,
                message="检测到堆叠查询，可能存在严重注入攻击",
                description="堆叠查询可执行任意 SQL 语句"
            ),
            
            # 基于 LOAD_FILE 的注入
            InjectionPattern(
                name="load_file_injection",
                pattern=r"LOAD_FILE\s*\(",
                risk_level=InjectionRiskLevel.HIGH,
                message="检测到 LOAD_FILE 函数，可能存在文件读取注入",
                description="LOAD_FILE 可用于读取服务器文件"
            ),
            
            # 基于 INTO OUTFILE 的注入
            InjectionPattern(
                name="into_outfile_injection",
                pattern=r"INTO\s+(OUTFILE|DUMPFILE)",
                risk_level=InjectionRiskLevel.CRITICAL,
                message="检测到 INTO OUTFILE，可能存在文件写入注入",
                description="INTO OUTFILE 可用于写入服务器文件"
            ),
            
            # 基于系统命令的注入
            InjectionPattern(
                name="system_command_injection",
                pattern=r"(xp_cmdshell|system\(|exec\(|eval\(|passthru\(|shell_exec\()",
                risk_level=InjectionRiskLevel.CRITICAL,
                message="检测到系统命令执行，可能存在命令注入",
                description="系统命令执行可完全控制服务器"
            ),
            
            # 基于十六进制的注入
            InjectionPattern(
                name="hex_injection",
                pattern=r"0x[0-9a-fA-F]+",
                risk_level=InjectionRiskLevel.LOW,
                message="检测到十六进制值，可能存在编码绕过",
                description="十六进制编码可用于绕过输入过滤"
            ),
            
            # 基于注释的绕过
            InjectionPattern(
                name="comment_bypass",
                pattern=r"/\*!.*?\*/",
                risk_level=InjectionRiskLevel.MEDIUM,
                message="检测到 MySQL 特殊注释，可能存在绕过",
                description="MySQL 特殊注释可用于绕过 WAF"
            ),
            
            # 基于引号的注入
            InjectionPattern(
                name="quote_injection",
                pattern=r"['\"](\s*)(OR|AND)(\s*)['\"]",
                risk_level=InjectionRiskLevel.HIGH,
                message="检测到引号闭合，可能存在注入攻击",
                description="引号闭合是 SQL 注入的常见技术"
            ),
            
            # 基于括号的注入
            InjectionPattern(
                name="parenthesis_injection",
                pattern=r"\)\s*(OR|AND|UNION|SELECT)",
                risk_level=InjectionRiskLevel.MEDIUM,
                message="检测到括号闭合，可能存在注入攻击",
                description="括号闭合可用于绕过语法检查"
            ),
            
            # 基于编码的注入
            InjectionPattern(
                name="encoding_injection",
                pattern=r"(CHAR|CHR|CONCAT|CONCAT_WS)\s*\(",
                risk_level=InjectionRiskLevel.LOW,
                message="检测到字符函数，可能存在编码绕过",
                description="字符函数可用于绕过输入过滤"
            ),
        ]
    
    def detect(self, sql: str) -> List[Dict[str, Any]]:
        """
        检测 SQL 注入
        
        Args:
            sql: SQL 语句
            
        Returns:
            List[Dict]: 检测到的注入风险列表
        """
        risks = []
        
        for pattern in self.patterns:
            if not pattern.enabled:
                continue
            
            compiled_pattern = self._compiled_patterns.get(pattern.name)
            if compiled_pattern and compiled_pattern.search(sql):
                risks.append({
                    "name": pattern.name,
                    "risk_level": pattern.risk_level.value,
                    "message": pattern.message,
                    "description": pattern.description,
                    "pattern": pattern.pattern
                })
        
        return risks
    
    def get_highest_risk_level(self, sql: str) -> InjectionRiskLevel:
        """
        获取最高风险等级
        
        Args:
            sql: SQL 语句
            
        Returns:
            InjectionRiskLevel: 最高风险等级
        """
        risks = self.detect(sql)
        
        if not risks:
            return InjectionRiskLevel.NONE
        
        # 风险等级优先级
        risk_priority = {
            InjectionRiskLevel.NONE: 0,
            InjectionRiskLevel.LOW: 1,
            InjectionRiskLevel.MEDIUM: 2,
            InjectionRiskLevel.HIGH: 3,
            InjectionRiskLevel.CRITICAL: 4
        }
        
        highest_risk = InjectionRiskLevel.NONE
        highest_priority = 0
        
        for risk in risks:
            risk_level = InjectionRiskLevel(risk["risk_level"])
            priority = risk_priority.get(risk_level, 0)
            
            if priority > highest_priority:
                highest_priority = priority
                highest_risk = risk_level
        
        return highest_risk
    
    def is_safe(self, sql: str) -> bool:
        """
        检查 SQL 是否安全
        
        Args:
            sql: SQL 语句
            
        Returns:
            bool: 是否安全
        """
        highest_risk = self.get_highest_risk_level(sql)
        
        # 只有 LOW 和 NONE 认为是安全的
        return highest_risk in [InjectionRiskLevel.NONE, InjectionRiskLevel.LOW]
    
    def add_pattern(self, pattern: InjectionPattern) -> None:
        """
        添加自定义模式
        
        Args:
            pattern: 注入模式
        """
        self.patterns.append(pattern)
        
        # 编译新模式
        try:
            self._compiled_patterns[pattern.name] = re.compile(
                pattern.pattern, 
                re.IGNORECASE | re.DOTALL
            )
        except re.error:
            # 忽略无效的正则表达式
            pass
    
    def remove_pattern(self, pattern_name: str) -> bool:
        """
        移除模式
        
        Args:
            pattern_name: 模式名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, pattern in enumerate(self.patterns):
            if pattern.name == pattern_name:
                self.patterns.pop(i)
                if pattern_name in self._compiled_patterns:
                    del self._compiled_patterns[pattern_name]
                return True
        
        return False
    
    def enable_pattern(self, pattern_name: str) -> bool:
        """
        启用模式
        
        Args:
            pattern_name: 模式名称
            
        Returns:
            bool: 是否成功启用
        """
        for pattern in self.patterns:
            if pattern.name == pattern_name:
                pattern.enabled = True
                return True
        
        return False
    
    def disable_pattern(self, pattern_name: str) -> bool:
        """
        禁用模式
        
        Args:
            pattern_name: 模式名称
            
        Returns:
            bool: 是否成功禁用
        """
        for pattern in self.patterns:
            if pattern.name == pattern_name:
                pattern.enabled = False
                return True
        
        return False
    
    def get_patterns(self) -> List[Dict[str, Any]]:
        """
        获取所有模式
        
        Returns:
            List[Dict]: 模式列表
        """
        return [
            {
                "name": pattern.name,
                "pattern": pattern.pattern,
                "risk_level": pattern.risk_level.value,
                "message": pattern.message,
                "description": pattern.description,
                "enabled": pattern.enabled
            }
            for pattern in self.patterns
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        enabled_count = sum(1 for p in self.patterns if p.enabled)
        disabled_count = len(self.patterns) - enabled_count
        
        risk_level_counts = {}
        for pattern in self.patterns:
            level = pattern.risk_level.value
            risk_level_counts[level] = risk_level_counts.get(level, 0) + 1
        
        return {
            "total_patterns": len(self.patterns),
            "enabled_patterns": enabled_count,
            "disabled_patterns": disabled_count,
            "risk_level_counts": risk_level_counts
        }