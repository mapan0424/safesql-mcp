# 基础使用示例

SafeSQL MCP 常见使用场景示例。

## 📋 示例目录

1. [命令行使用](#命令行使用)
2. [Python API 使用](#python-api-使用)
3. [MCP 集成](#mcp-集成)
4. [GitHub Action 集成](#github-action-集成)

---

## 命令行使用

### 示例 1：验证单条 SQL

```bash
# 验证安全 SQL
$ safesql-review --sql "SELECT id, name FROM users WHERE id = 1"
✅ Risk Level: low
   Message: 安全查询
   Executable: true

# 验证高风险 SQL
$ safesql-review --sql "DROP TABLE users"
🔴 Risk Level: high
   Message: DROP TABLE 操作被禁止
   Executable: false

# 验证中风险 SQL
$ safesql-review --sql "SELECT * FROM users"
🟡 Risk Level: medium
   Message: 建议避免使用 SELECT *，请指定具体列
   Executable: true
```

### 示例 2：审查 SQL 文件

```bash
# 审查单个文件
$ safesql-review --file queries.sql

# 审查目录中的所有 SQL 文件
$ safesql-review --directory ./sql

# 输出 JSON 格式
$ safesql-review --file queries.sql --format json

# 高风险时返回非零退出码（用于 CI）
$ safesql-review --file queries.sql --fail-on-high-risk
```

### 示例 3：查看风险规则

```bash
# 查看所有规则
$ safesql-review --show-rules

# 输出 YAML 格式
$ safesql-review --show-rules --format yaml

# 输出 JSON 格式
$ safesql-review --show-rules --format json
```

### 示例 4：测试数据库连接

```bash
# 测试配置文件中的数据库连接
$ safesql-review --config safesql.yaml --test-connection

# 输出：
# ✅ postgres_main: Connection successful
# ✅ mysql_analytics: Connection successful
```

---

## Python API 使用

### 示例 1：基础风险评估

```python
from safesql_mcp.core.engine import RiskEngine

# 创建风险引擎（使用默认规则）
engine = RiskEngine()

# 评估 SQL
def check_sql(sql: str):
    assessment = engine.assess_sql(sql)
    
    print(f"SQL: {sql}")
    print(f"风险等级: {assessment.risk_level.value}")
    print(f"消息: {assessment.message}")
    print(f"可执行: {assessment.is_executable}")
    
    if assessment.suggestions:
        print("建议:")
        for suggestion in assessment.suggestions:
            print(f"  - {suggestion}")
    
    print()

# 测试不同 SQL
check_sql("SELECT id, name FROM users WHERE id = 1")
check_sql("SELECT * FROM users")
check_sql("DROP TABLE users")
check_sql("DELETE FROM orders")
```

输出：
```
SQL: SELECT id, name FROM users WHERE id = 1
风险等级: low
消息: 安全查询
可执行: True

SQL: SELECT * FROM users
风险等级: medium
消息: 建议避免使用 SELECT *，请指定具体列
可执行: True
建议:
  - 明确指定需要的列名，而不是使用 SELECT *

SQL: DROP TABLE users
风险等级: high
消息: DROP TABLE 操作被禁止
可执行: False

SQL: DELETE FROM orders
风险等级: high
消息: DELETE 操作缺少 WHERE 条件
可执行: False
```

### 示例 2：自定义风险规则

```python
from safesql_mcp.core.engine import RiskEngine
from safesql_mcp.core.rules import RiskLevel, RiskRule

# 定义自定义规则
custom_rules = [
    RiskRule(
        name="block_write_operations",
        pattern=r"(INSERT|UPDATE|DELETE|DROP|TRUNCATE)\s+",
        level=RiskLevel.HIGH,
        message="生产环境禁止写操作",
        description="只允许 SELECT 查询"
    ),
    RiskRule(
        name="limit_result_size",
        pattern=r"SELECT\s+.*(?<!LIMIT\s+\d+)$",
        level=RiskLevel.MEDIUM,
        message="建议添加 LIMIT 限制结果集大小",
        description="防止返回过多数据"
    ),
    RiskRule(
        name="allow_health_check",
        pattern=r"SELECT\s+1",
        level=RiskLevel.SAFE,
        message="健康检查查询",
        description="允许健康检查"
    )
]

# 创建自定义引擎
engine = RiskEngine(custom_rules=custom_rules)

# 测试
assessment = engine.assess_sql("INSERT INTO users (name) VALUES ('test')")
print(f"风险等级: {assessment.risk_level.value}")  # high
print(f"消息: {assessment.message}")  # 生产环境禁止写操作
```

### 示例 3：批量 SQL 审查

```python
from safesql_mcp.core.engine import RiskEngine
from pathlib import Path
import json

def audit_sql_files(directory: str, output_file: str = None):
    """审查目录中的所有 SQL 文件"""
    engine = RiskEngine()
    results = []
    
    # 查找所有 SQL 文件
    sql_files = Path(directory).glob("**/*.sql")
    
    for sql_file in sql_files:
        with open(sql_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 分割 SQL 语句
        statements = [s.strip() for s in content.split(";") if s.strip()]
        
        file_results = []
        for sql in statements:
            assessment = engine.assess_sql(sql)
            file_results.append({
                "sql": sql[:100] + "..." if len(sql) > 100 else sql,
                "risk_level": assessment.risk_level.value,
                "message": assessment.message,
                "executable": assessment.is_executable
            })
        
        results.append({
            "file": str(sql_file),
            "statements": file_results
        })
    
    # 输出结果
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"结果已保存到 {output_file}")
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))

# 使用
audit_sql_files("./sql", "audit_report.json")
```

### 示例 4：SQL 分析器

```python
from safesql_mcp.core.analyzer import SQLAnalyzer

analyzer = SQLAnalyzer()

sql = """
SELECT u.name, u.email, o.total, p.name as product_name
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN products p ON o.product_id = p.id
WHERE u.status = 'active'
AND o.created_at > '2024-01-01'
ORDER BY o.total DESC
LIMIT 100
"""

analysis = analyzer.analyze(sql)

print(f"SQL 类型: {analysis.sql_type.value}")
print(f"涉及表: {analysis.tables}")
print(f"涉及列: {analysis.columns}")
print(f"有 WHERE: {analysis.has_where}")
print(f"有 ORDER BY: {analysis.has_order_by}")
print(f"有 LIMIT: {analysis.has_limit}")
print(f"复杂度分数: {analysis.complexity_score}")
print(f"有性能问题: {analysis.has_performance_issues}")

if analysis.performance_warnings:
    print("性能警告:")
    for warning in analysis.performance_warnings:
        print(f"  - {warning}")

if analysis.optimization_suggestions:
    print("优化建议:")
    for suggestion in analysis.optimization_suggestions:
        print(f"  - {suggestion}")
```

输出：
```
SQL 类型: SELECT
涉及表: ['users', 'orders', 'products']
涉及列: ['name', 'email', 'total', 'product_name']
有 WHERE: True
有 ORDER BY: True
有 LIMIT: True
复杂度分数: 12
有性能问题: False
```

### 示例 5：数据库查询（带风险审查）

```python
import asyncio
from safesql_mcp.core.engine import RiskEngine
from safesql_mcp.databases.postgresql import PostgreSQLDatabase
from safesql_mcp.databases.base import DatabaseConfig

async def safe_query():
    """安全查询示例"""
    
    # 创建风险引擎
    engine = RiskEngine()
    
    # 创建数据库连接
    config = DatabaseConfig(
        type="postgresql",
        host="localhost",
        port=5432,
        database="mydb",
        user="readonly_user",
        password="password"
    )
    db = PostgreSQLDatabase(config)
    
    try:
        # 连接数据库
        await db.connect()
        
        # 要执行的 SQL
        sql = "SELECT * FROM users WHERE id = 1"
        
        # 风险评估
        assessment = engine.assess_sql(sql)
        
        if not assessment.is_executable:
            print(f"❌ 高风险 SQL 被拦截: {assessment.message}")
            return
        
        if assessment.requires_warning:
            print(f"⚠️ 中风险警告: {assessment.message}")
        
        # 执行查询
        result = await db.execute(sql)
        
        # 生成 EXPLAIN
        explain_plan = await db.explain(sql)
        
        print(f"查询结果: {result.rows}")
        print(f"执行计划:\n{explain_plan}")
        
    finally:
        await db.disconnect()

# 运行
asyncio.run(safe_query())
```

---

## MCP 集成

### 示例 1：在 Claude Desktop 中使用

**配置文件** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "safesql": {
      "command": "safesql-mcp",
      "args": ["--config", "/path/to/safesql.yaml"]
    }
  }
}
```

**使用示例**：

在 Claude Desktop 中：
```
请查询数据库中所有活跃用户的信息
```

Claude 会自动调用 SafeSQL MCP 工具执行安全查询。

### 示例 2：Python MCP 客户端

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 连接到 SafeSQL MCP Server
    server_params = StdioServerParameters(
        command="safesql-mcp",
        args=["--config", "safesql.yaml"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化
            await session.initialize()
            
            # 列出可用工具
            tools = await session.list_tools()
            print("可用工具:", [t.name for t in tools.tools])
            
            # 执行查询
            result = await session.call_tool(
                "query",
                arguments={
                    "database": "my_postgres",
                    "sql": "SELECT id, name FROM users WHERE id = 1",
                    "explain": True
                }
            )
            print("查询结果:", result)
            
            # 验证 SQL
            validation = await session.call_tool(
                "validate",
                arguments={
                    "sql": "DROP TABLE users"
                }
            )
            print("验证结果:", validation)
            
            # 获取数据库 schema
            schema = await session.call_tool(
                "schema",
                arguments={
                    "database": "my_postgres"
                }
            )
            print("数据库 Schema:", schema)

asyncio.run(main())
```

### 示例 3：自定义 MCP Server

```python
from mcp.server import Server
from safesql_mcp.core.engine import RiskEngine
from safesql_mcp.mcp.tools import SafeSQLTools

# 创建 MCP Server
server = Server("my-custom-safesql")

# 创建风险引擎（自定义规则）
engine = RiskEngine(custom_rules=[...])

# 创建数据库连接
databases = {...}

# 注册工具
tools = SafeSQLTools(server, engine, databases)

# 运行服务器
if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def run():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())
    
    asyncio.run(run())
```

---

## GitHub Action 集成

### 示例 1：PR SQL 审查

```yaml
# .github/workflows/sql-review.yml
name: SQL Risk Review

on:
  pull_request:
    paths:
      - '**/*.sql'
      - '**/migrations/**'

jobs:
  sql-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install SafeSQL
        run: pip install safesql-mcp
      
      - name: Review SQL files
        run: |
          safesql-review --directory . --fail-on-high-risk --format json > review.json
        continue-on-error: true
      
      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = JSON.parse(fs.readFileSync('review.json', 'utf8'));
            
            let body = '## ⚠️ SQL 风险审查报告\n\n';
            for (const file of review) {
              for (const stmt of file.statements) {
                if (stmt.risk_level === 'high') {
                  body += `🔴 **高风险** in \`${file.file}\`\n`;
                  body += `> ${stmt.message}\n\n`;
                }
              }
            }
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
      
      - name: Fail on high risk
        if: failure()
        run: exit 1
```

### 示例 2：数据库迁移审查

```yaml
name: Migration Review

on:
  pull_request:
    paths:
      - 'migrations/**'

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Review migrations
        run: |
          pip install safesql-mcp
          
          # 审查所有迁移文件
          for file in migrations/*.sql; do
            echo "审查: $file"
            safesql-review --file "$file" --format text
          done
```

---

## 📚 更多示例

- [高级示例](advanced-examples.md) - 高级用法和集成
- [最佳实践](best-practices.md) - 生产环境最佳实践
- [故障排除](../guides/troubleshooting.md) - 常见问题解答