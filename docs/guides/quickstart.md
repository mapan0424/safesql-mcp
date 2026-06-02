# 快速开始指南

5 分钟上手 SafeSQL MCP！

## 📋 前置条件

- Python 3.10+
- PostgreSQL 或 MySQL 数据库
- （可选）MCP 客户端（如 Claude Desktop）

## 🚀 安装

### 方式一：从 PyPI 安装（推荐）

```bash
pip install safesql-mcp
```

### 方式二：从源码安装

```bash
git clone https://github.com/mapan0424/safesql-mcp.git
cd safesql-mcp
pip install -e .
```

## ⚡ 快速配置

### 1. 创建配置文件

创建 `safesql.yaml`：

```yaml
# 数据库连接
databases:
  my_postgres:
    type: postgresql
    host: localhost
    port: 5432
    database: mydb
    user: readonly_user
    password: your_password

# 风险规则（使用默认规则即可）
risk_rules: {}

# MCP Server 配置
mcp_server:
  name: safesql
  version: "1.0.0"
```

### 2. 测试连接

```bash
# 测试数据库连接
safesql-review --config safesql.yaml --test-connection
```

### 3. 启动 MCP Server

```bash
# 启动服务器
safesql-mcp --config safesql.yaml
```

## 🔍 基础使用

### 验证 SQL 风险

```bash
# 验证单条 SQL
safesql-review --sql "SELECT * FROM users"

# 输出：
# Risk Level: medium
# Message: 建议避免使用 SELECT *，请指定具体列
# Executable: true
```

### 审查 SQL 文件

```bash
# 审查目录中的所有 SQL 文件
safesql-review --directory ./sql

# 输出：
# Found 5 SQL files
# 🟡 MEDIUM RISK in ./sql/queries.sql: 建议避免使用 SELECT *
# Review Summary:
#   Files reviewed: 5
#   High risk: 0
#   Medium risk: 1
```

### 使用 Python API

```python
from safesql_mcp.core.engine import RiskEngine

# 创建风险引擎
engine = RiskEngine()

# 评估 SQL
assessment = engine.assess_sql("SELECT * FROM users")

print(f"风险等级: {assessment.risk_level.value}")
print(f"消息: {assessment.message}")
print(f"可执行: {assessment.is_executable}")
```

## 🔌 MCP 集成

### 在 Claude Desktop 中使用

1. 编辑 Claude Desktop 配置文件：

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

2. 重启 Claude Desktop

3. 现在可以安全地查询数据库了！

### 使用 MCP 工具

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 连接到 SafeSQL MCP Server
server_params = StdioServerParameters(
    command="safesql-mcp",
    args=["--config", "safesql.yaml"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # 初始化
        await session.initialize()
        
        # 执行安全查询
        result = await session.call_tool(
            "query",
            arguments={
                "database": "my_postgres",
                "sql": "SELECT id, name FROM users WHERE id = 1",
                "explain": True
            }
        )
        
        print(result)
```

## 🛡️ 风险等级说明

| 等级 | 说明 | 行为 |
|------|------|------|
| 🔴 **HIGH** | 高风险操作 | 自动拦截，不允许执行 |
| 🟡 **MEDIUM** | 中风险操作 | 警告但允许执行 |
| 🟢 **LOW** | 低风险操作 | 直接执行 |
| ✅ **SAFE** | 安全操作 | 忽略检查 |

### 高风险示例

```sql
-- 🔴 拦截
DROP TABLE users;
DELETE FROM orders;
UPDATE users SET status = 'inactive';
GRANT ALL PRIVILEGES ON DATABASE mydb TO public;
```

### 中风险示例

```sql
-- ⚠️ 警告
SELECT * FROM users;
INSERT INTO logs VALUES (1, 'error', '2024-01-01');
SELECT * FROM products WHERE name LIKE '%phone%';
```

### 低风险示例

```sql
-- ✅ 允许
SELECT id, name FROM users WHERE id = 1;
INSERT INTO orders (user_id, product_id) VALUES (1, 100);
UPDATE products SET stock = stock - 1 WHERE id = 100 AND stock > 0;
```

## 📝 下一步

- [基础使用指南](guides/basic-usage.md) - 更详细的使用教程
- [配置指南](guides/risk-rules.md) - 自定义风险规则
- [MCP Server 配置](guides/mcp-server.md) - 详细服务器配置
- [示例代码](examples/basic-examples.md) - 更多实际场景

## ❓ 常见问题

### Q: 如何只允许 SELECT 查询？

A: 在配置文件中添加高风险规则：

```yaml
risk_rules:
  high_risk:
    - name: block_insert
      pattern: 'INSERT\s+'
      message: 'INSERT 操作被禁止'
    - name: block_update
      pattern: 'UPDATE\s+'
      message: 'UPDATE 操作被禁止'
    - name: block_delete
      pattern: 'DELETE\s+'
      message: 'DELETE 操作被禁止'
```

### Q: 如何连接多个数据库？

A: 在配置文件中添加多个数据库：

```yaml
databases:
  postgres_main:
    type: postgresql
    host: localhost
    port: 5432
    database: maindb
    user: readonly_user
    password: ${POSTGRES_PASSWORD}
    
  mysql_analytics:
    type: mysql
    host: localhost
    port: 3306
    database: analytics
    user: readonly_user
    password: ${MYSQL_PASSWORD}
```

### Q: 如何查看 EXPLAIN 执行计划？

A: 使用 `explain` 参数：

```python
result = await session.call_tool(
    "query",
    arguments={
        "database": "my_postgres",
        "sql": "SELECT * FROM users WHERE id = 1",
        "explain": True  # 启用 EXPLAIN
    }
)
```

### Q: 如何自定义风险消息？

A: 在配置文件中定义规则的 `message` 字段：

```yaml
risk_rules:
  high_risk:
    - name: custom_rule
      pattern: 'CUSTOM_PATTERN'
      message: '自定义的风险提示消息'
      description: '详细说明为什么这是高风险操作'
```