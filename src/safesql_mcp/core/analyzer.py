"""
SQL 分析器：深度分析 SQL 语句的结构和性能特征
"""

import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class SQLType(Enum):
    """SQL 语句类型"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    TRUNCATE = "TRUNCATE"
    GRANT = "GRANT"
    REVOKE = "REVOKE"
    UNKNOWN = "UNKNOWN"


@dataclass
class SQLAnalysis:
    """SQL 分析结果"""
    sql: str
    sql_type: SQLType
    tables: List[str]
    columns: List[str]
    conditions: List[str]
    joins: List[Dict[str, Any]]
    subqueries: List[str]
    has_where: bool
    has_order_by: bool
    has_group_by: bool
    has_having: bool
    has_limit: bool
    has_offset: bool
    is_read_only: bool
    is_write_operation: bool
    complexity_score: int
    has_performance_issues: bool
    performance_warnings: List[str]
    has_syntax_issues: bool
    syntax_suggestions: List[str]
    optimization_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sql": self.sql,
            "sql_type": self.sql_type.value,
            "tables": self.tables,
            "columns": self.columns,
            "conditions": self.conditions,
            "joins": self.joins,
            "subqueries": self.subqueries,
            "has_where": self.has_where,
            "has_order_by": self.has_order_by,
            "has_group_by": self.has_group_by,
            "has_having": self.has_having,
            "has_limit": self.has_limit,
            "has_offset": self.has_offset,
            "is_read_only": self.is_read_only,
            "is_write_operation": self.is_write_operation,
            "complexity_score": self.complexity_score,
            "has_performance_issues": self.has_performance_issues,
            "performance_warnings": self.performance_warnings,
            "has_syntax_issues": self.has_syntax_issues,
            "syntax_suggestions": self.syntax_suggestions,
            "optimization_suggestions": self.optimization_suggestions,
        }


class SQLAnalyzer:
    """SQL 分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # SQL 关键字模式
        self._select_pattern = re.compile(r'^\s*SELECT\s+', re.IGNORECASE)
        self._insert_pattern = re.compile(r'^\s*INSERT\s+INTO\s+', re.IGNORECASE)
        self._update_pattern = re.compile(r'^\s*UPDATE\s+', re.IGNORECASE)
        self._delete_pattern = re.compile(r'^\s*DELETE\s+FROM\s+', re.IGNORECASE)
        self._create_pattern = re.compile(r'^\s*CREATE\s+', re.IGNORECASE)
        self._alter_pattern = re.compile(r'^\s*ALTER\s+', re.IGNORECASE)
        self._drop_pattern = re.compile(r'^\s*DROP\s+', re.IGNORECASE)
        self._truncate_pattern = re.compile(r'^\s*TRUNCATE\s+', re.IGNORECASE)
        self._grant_pattern = re.compile(r'^\s*GRANT\s+', re.IGNORECASE)
        self._revoke_pattern = re.compile(r'^\s*REVOKE\s+', re.IGNORECASE)
        
        # 表名提取模式
        self._from_pattern = re.compile(r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE)
        self._join_pattern = re.compile(r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE)
        self._into_pattern = re.compile(r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE)
        self._update_table_pattern = re.compile(r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.IGNORECASE)
        
        # 列名提取模式
        self._select_columns_pattern = re.compile(r'SELECT\s+(.*?)\s+FROM', re.IGNORECASE | re.DOTALL)
        self._set_columns_pattern = re.compile(r'SET\s+(.*?)\s+WHERE', re.IGNORECASE | re.DOTALL)
        
        # 条件提取模式
        self._where_pattern = re.compile(r'WHERE\s+(.*?)(?:ORDER|GROUP|LIMIT|$)', re.IGNORECASE | re.DOTALL)
        
        # JOIN 提取模式
        self._join_detail_pattern = re.compile(
            r'(INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+ON\s+(.*?)(?=(?:INNER|LEFT|RIGHT|FULL|CROSS|WHERE|ORDER|GROUP|LIMIT|$))',
            re.IGNORECASE | re.DOTALL
        )
        
        # 子查询模式
        self._subquery_pattern = re.compile(r'\(\s*SELECT\s+', re.IGNORECASE)
        
        # 性能问题模式
        self._performance_patterns = {
            "select_star": re.compile(r'SELECT\s+\*\s+FROM', re.IGNORECASE),
            "like_wildcard": re.compile(r"LIKE\s+'%", re.IGNORECASE),
            "or_conditions": re.compile(r'WHERE\s+.*?\s+OR\s+.*?\s+OR\s+', re.IGNORECASE),
            "not_in_subquery": re.compile(r'NOT\s+IN\s*\(\s*SELECT', re.IGNORECASE),
            "function_on_column": re.compile(r'WHERE\s+\w+\([^)]*\)\s*=', re.IGNORECASE),
            "implicit_conversion": re.compile(r"WHERE\s+\w+\s*=\s*'[^']*'", re.IGNORECASE),
        }
        
        # 语法问题模式
        self._syntax_patterns = {
            "missing_table_alias": re.compile(r'FROM\s+[a-zA-Z_][a-zA-Z0-9_]*\s+(?!AS\s+)(?!ON\s+)(?!WHERE\s+)(?!ORDER\s+)(?!GROUP\s+)(?!LIMIT\s+)(?!$)', re.IGNORECASE),
            "ambiguous_column": re.compile(r'SELECT\s+\w+\.\*\s+FROM', re.IGNORECASE),
            "unnecessary_parentheses": re.compile(r'\(\s*\(\s*SELECT', re.IGNORECASE),
        }
    
    def analyze(self, sql: str, database_type: str = "postgresql") -> SQLAnalysis:
        """
        分析 SQL 语句
        
        Args:
            sql: SQL 语句
            database_type: 数据库类型
            
        Returns:
            SQLAnalysis: 分析结果
        """
        # 清理 SQL
        cleaned_sql = self._clean_sql(sql)
        
        # 确定 SQL 类型
        sql_type = self._get_sql_type(cleaned_sql)
        
        # 提取表名
        tables = self._extract_tables(cleaned_sql)
        
        # 提取列名
        columns = self._extract_columns(cleaned_sql)
        
        # 提取条件
        conditions = self._extract_conditions(cleaned_sql)
        
        # 提取 JOIN 信息
        joins = self._extract_joins(cleaned_sql)
        
        # 检测子查询
        subqueries = self._extract_subqueries(cleaned_sql)
        
        # 检查 SQL 特征
        has_where = bool(self._where_pattern.search(cleaned_sql))
        has_order_by = bool(re.search(r'ORDER\s+BY', cleaned_sql, re.IGNORECASE))
        has_group_by = bool(re.search(r'GROUP\s+BY', cleaned_sql, re.IGNORECASE))
        has_having = bool(re.search(r'HAVING\s+', cleaned_sql, re.IGNORECASE))
        has_limit = bool(re.search(r'LIMIT\s+', cleaned_sql, re.IGNORECASE))
        has_offset = bool(re.search(r'OFFSET\s+', cleaned_sql, re.IGNORECASE))
        
        # 判断是否为只读操作
        is_read_only = sql_type in [SQLType.SELECT]
        
        # 判断是否为写操作
        is_write_operation = sql_type in [
            SQLType.INSERT, SQLType.UPDATE, SQLType.DELETE,
            SQLType.CREATE, SQLType.ALTER, SQLType.DROP, SQLType.TRUNCATE
        ]
        
        # 计算复杂度分数
        complexity_score = self._calculate_complexity(
            cleaned_sql, tables, joins, subqueries, has_where, has_order_by, has_group_by
        )
        
        # 检测性能问题
        performance_warnings = self._detect_performance_issues(cleaned_sql, tables, joins)
        has_performance_issues = len(performance_warnings) > 0
        
        # 检测语法问题
        syntax_suggestions = self._detect_syntax_issues(cleaned_sql)
        has_syntax_issues = len(syntax_suggestions) > 0
        
        # 生成优化建议
        optimization_suggestions = self._generate_optimization_suggestions(
            cleaned_sql, tables, joins, performance_warnings, syntax_suggestions
        )
        
        return SQLAnalysis(
            sql=sql,
            sql_type=sql_type,
            tables=tables,
            columns=columns,
            conditions=conditions,
            joins=joins,
            subqueries=subqueries,
            has_where=has_where,
            has_order_by=has_order_by,
            has_group_by=has_group_by,
            has_having=has_having,
            has_limit=has_limit,
            has_offset=has_offset,
            is_read_only=is_read_only,
            is_write_operation=is_write_operation,
            complexity_score=complexity_score,
            has_performance_issues=has_performance_issues,
            performance_warnings=performance_warnings,
            has_syntax_issues=has_syntax_issues,
            syntax_suggestions=syntax_suggestions,
            optimization_suggestions=optimization_suggestions
        )
    
    def _clean_sql(self, sql: str) -> str:
        """清理 SQL 语句"""
        # 去除注释
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # 标准化空白字符
        sql = re.sub(r'\s+', ' ', sql).strip()
        
        # 去除末尾分号
        sql = sql.rstrip(';').strip()
        
        return sql
    
    def _get_sql_type(self, sql: str) -> SQLType:
        """确定 SQL 类型"""
        if self._select_pattern.search(sql):
            return SQLType.SELECT
        elif self._insert_pattern.search(sql):
            return SQLType.INSERT
        elif self._update_pattern.search(sql):
            return SQLType.UPDATE
        elif self._delete_pattern.search(sql):
            return SQLType.DELETE
        elif self._create_pattern.search(sql):
            return SQLType.CREATE
        elif self._alter_pattern.search(sql):
            return SQLType.ALTER
        elif self._drop_pattern.search(sql):
            return SQLType.DROP
        elif self._truncate_pattern.search(sql):
            return SQLType.TRUNCATE
        elif self._grant_pattern.search(sql):
            return SQLType.GRANT
        elif self._revoke_pattern.search(sql):
            return SQLType.REVOKE
        else:
            return SQLType.UNKNOWN
    
    def _extract_tables(self, sql: str) -> List[str]:
        """提取表名"""
        tables = []
        
        # FROM 子句中的表
        from_matches = self._from_pattern.findall(sql)
        tables.extend(from_matches)
        
        # JOIN 子句中的表
        join_matches = self._join_pattern.findall(sql)
        tables.extend(join_matches)
        
        # INTO 子句中的表
        into_matches = self._into_pattern.findall(sql)
        tables.extend(into_matches)
        
        # UPDATE 子句中的表
        update_matches = self._update_table_pattern.findall(sql)
        tables.extend(update_matches)
        
        # 去重并返回
        return list(set(tables))
    
    def _extract_columns(self, sql: str) -> List[str]:
        """提取列名"""
        columns = []
        
        # SELECT 子句中的列
        select_match = self._select_columns_pattern.search(sql)
        if select_match:
            columns_str = select_match.group(1)
            # 简单分割，不处理复杂表达式
            for col in columns_str.split(','):
                col = col.strip()
                if col and col != '*':
                    # 提取别名
                    if ' AS ' in col.upper():
                        col = col.split(' AS ')[0].strip()
                    # 提取表别名
                    if '.' in col:
                        col = col.split('.')[-1].strip()
                    columns.append(col)
        
        # SET 子句中的列
        set_match = self._set_columns_pattern.search(sql)
        if set_match:
            set_str = set_match.group(1)
            for assignment in set_str.split(','):
                if '=' in assignment:
                    col = assignment.split('=')[0].strip()
                    if '.' in col:
                        col = col.split('.')[-1].strip()
                    columns.append(col)
        
        return columns
    
    def _extract_conditions(self, sql: str) -> List[str]:
        """提取 WHERE 条件"""
        conditions = []
        
        where_match = self._where_pattern.search(sql)
        if where_match:
            where_clause = where_match.group(1)
            # 简单分割，不处理嵌套括号
            for condition in re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE):
                condition = condition.strip()
                if condition:
                    conditions.append(condition)
        
        return conditions
    
    def _extract_joins(self, sql: str) -> List[Dict[str, Any]]:
        """提取 JOIN 信息"""
        joins = []
        
        join_matches = self._join_detail_pattern.findall(sql)
        for join_type, table, condition in join_matches:
            join_type = join_type.upper() if join_type else "INNER"
            joins.append({
                "type": join_type,
                "table": table,
                "condition": condition.strip()
            })
        
        return joins
    
    def _extract_subqueries(self, sql: str) -> List[str]:
        """提取子查询"""
        subqueries = []
        
        # 简单的子查询检测
        matches = self._subquery_pattern.finditer(sql)
        for match in matches:
            start = match.start()
            # 找到匹配的右括号
            depth = 1
            pos = match.end()
            while pos < len(sql) and depth > 0:
                if sql[pos] == '(':
                    depth += 1
                elif sql[pos] == ')':
                    depth -= 1
                pos += 1
            
            if depth == 0:
                subquery = sql[start:pos]
                subqueries.append(subquery)
        
        return subqueries
    
    def _calculate_complexity(
        self, sql: str, tables: List[str], joins: List[Dict[str, Any]],
        subqueries: List[str], has_where: bool, has_order_by: bool, has_group_by: bool
    ) -> int:
        """计算 SQL 复杂度分数"""
        score = 0
        
        # 表数量
        score += len(tables) * 2
        
        # JOIN 数量
        score += len(joins) * 3
        
        # 子查询数量
        score += len(subqueries) * 4
        
        # 特征
        if has_where:
            score += 1
        if has_order_by:
            score += 1
        if has_group_by:
            score += 2
        
        # SQL 长度
        score += len(sql) // 100
        
        return score
    
    def _detect_performance_issues(
        self, sql: str, tables: List[str], joins: List[Dict[str, Any]]
    ) -> List[str]:
        """检测性能问题"""
        warnings = []
        
        # 检查 SELECT *
        if self._performance_patterns["select_star"].search(sql):
            warnings.append("使用 SELECT * 会返回所有列，可能影响性能")
        
        # 检查前缀通配符
        if self._performance_patterns["like_wildcard"].search(sql):
            warnings.append("前缀通配符 LIKE '%...' 无法使用索引")
        
        # 检查多个 OR 条件
        if self._performance_patterns["or_conditions"].search(sql):
            warnings.append("多个 OR 条件可能影响索引使用")
        
        # 检查 NOT IN 子查询
        if self._performance_patterns["not_in_subquery"].search(sql):
            warnings.append("NOT IN 子查询可能性能较差，考虑使用 LEFT JOIN + IS NULL")
        
        # 检查函数应用在列上
        if self._performance_patterns["function_on_column"].search(sql):
            warnings.append("WHERE 条件中的函数可能导致索引失效")
        
        # 检查隐式类型转换
        if self._performance_patterns["implicit_conversion"].search(sql):
            warnings.append("可能存在隐式类型转换，影响索引使用")
        
        # 检查多表 JOIN
        if len(joins) > 3:
            warnings.append(f"多表 JOIN ({len(joins)} 个) 可能影响查询性能")
        
        return warnings
    
    def _detect_syntax_issues(self, sql: str) -> List[str]:
        """检测语法问题"""
        suggestions = []
        
        # 检查缺少表别名
        if self._syntax_patterns["missing_table_alias"].search(sql):
            suggestions.append("建议为表添加别名以提高可读性")
        
        # 检查模糊列名
        if self._syntax_patterns["ambiguous_column"].search(sql):
            suggestions.append("使用 表别名.* 时请确保表别名明确")
        
        # 检查不必要的括号
        if self._syntax_patterns["unnecessary_parentheses"].search(sql):
            suggestions.append("检查是否有多余的括号")
        
        return suggestions
    
    def _generate_optimization_suggestions(
        self, sql: str, tables: List[str], joins: List[Dict[str, Any]],
        performance_warnings: List[str], syntax_suggestions: List[str]
    ) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 基于性能警告生成建议
        if "使用 SELECT * 会返回所有列，可能影响性能" in performance_warnings:
            suggestions.append("明确指定需要的列名，而不是使用 SELECT *")
        
        if "前缀通配符 LIKE '%...' 无法使用索引" in performance_warnings:
            suggestions.append("考虑使用全文索引或其他搜索方案")
        
        if "多个 OR 条件可能影响索引使用" in performance_warnings:
            suggestions.append("考虑使用 IN 或 UNION 替代多个 OR 条件")
        
        if "NOT IN 子查询可能性能较差，考虑使用 LEFT JOIN + IS NULL" in performance_warnings:
            suggestions.append("使用 LEFT JOIN + IS NULL 替代 NOT IN 子查询")
        
        if "WHERE 条件中的函数可能导致索引失效" in performance_warnings:
            suggestions.append("考虑将函数应用移到查询外部，或使用函数索引")
        
        # 基于 JOIN 数量生成建议
        if len(joins) > 3:
            suggestions.append("考虑优化 JOIN 顺序，确保有合适的索引")
            suggestions.append("检查是否所有 JOIN 都是必要的")
        
        # 基于表数量生成建议
        if len(tables) > 5:
            suggestions.append("考虑是否可以通过反规范化减少表连接")
        
        return suggestions