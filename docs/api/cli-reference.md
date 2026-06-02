# CLI 命令参考

SafeSQL MCP 命令行工具详细说明。

## 📋 命令列表

| 命令 | 说明 |
|------|------|
| `safesql-mcp` | 启动 MCP Server |
| `safesql-review` | SQL 风险审查工具 |

---

## 🚀 safesql-mcp

启动 SafeSQL MCP Server。

### 用法

```bash
safesql-mcp [OPTIONS]
```

### 选项

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--config` | `-c` | 配置文件路径 | safesql.yaml |
| `--port` | `-p` | HTTP 端口（stdio 模式不需要） | - |
| `--host` | `-h` | HTTP 主机地址 | localhost |
| `--init` | - | 创建默认配置文件 | false |
| `--version` | `-v` | 显示版本号 | - |
| `--help` | - | 显示帮助信息 | - |

### 示例

```bash
# 使用默认配置启动
safesql-mcp

# 指定配置文件
safesql-mcp --config /path/to/safesql.yaml

# 创建默认配置文件
safesql-mcp --init

# HTTP 模式启动
safesql-mcp --port 8000 --host 0.0.0.0

# 显示版本
safesql-mcp --version
```

### 配置文件

默认配置文件：`safesql.yaml`

```yaml
# 数据库连接
databases:
  my_postgres:
    type: postgresql
    host: localhost
    port: 5432
    database: mydb
    user: readonly_user
    password: ${POSTGRES_PASSWORD}

# MCP Server 配置
mcp_server:
  name: safesql
  version: "1.0.0"

# 日志配置
logging:
  level: INFO
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `SAFESQL_CONFIG_PATH` | 配置文件路径 |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 |
| `MYSQL_PASSWORD` | MySQL 密码 |

### 退出码

| 代码 | 说明 |
|------|------|
| 0 | 正常退出 |
| 1 | 配置错误 |
| 2 | 数据库连接失败 |
| 3 | 启动失败 |

---

## 🔍 safesql-review

SQL 风险审查工具。

### 用法

```bash
safesql-review [OPTIONS] [SQL]
```

### 选项

| 选项 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--sql` | `-s` | 验证单条 SQL | - |
| `--file` | `-f` | 审查 SQL 文件 | - |
| `--directory` | `-d` | 审查目录 | . |
| `--config` | `-c` | 配置文件路径 | safesql.yaml |
| `--format` | `-o` | 输出格式 | text |
| `--fail-on-high-risk` | - | 高风险时返回非零退出码 | false |
| `--test-connection` | - | 测试数据库连接 | false |
| `--show-rules` | - | 显示风险规则 | false |
| `--help` | - | 显示帮助信息 | - |

### 子命令

#### 验证单条 SQL

```bash
# 基础验证
safesql-review --sql "SELECT * FROM users"

# 输出 JSON 格式
safesql-review --sql "SELECT * FROM users" --format json
```

**输出示例**：

```
SQL: SELECT * FROM users
Risk Level: medium
Message: 建议避免使用 SELECT *，请指定具体列
Executable: true
Suggestions:
  - 明确指定需要的列名，而不是使用 SELECT *
```

#### 审查 SQL 文件

```bash
# 审查单个文件
safesql-review --file queries.sql

# 审查目录
safesql-review --directory ./sql

# 输出 JSON 格式
safesql-review --directory ./sql --format json

# 高风险时返回非零退出码（用于 CI）
safesql-review --directory ./sql --fail-on-high-risk
```

**输出示例**：

```
Found 5 SQL files

📄 ./sql/users.sql
  🟡 MEDIUM: 建议避免使用 SELECT *

📄 ./sql/orders.sql
  🔴 HIGH: DELETE 操作缺少 WHERE 条件
     SQL: DELETE FROM orders

Review Summary:
  Files reviewed: 5
  High risk: 1
  Medium risk: 1
```

#### 测试数据库连接

```bash
# 测试配置文件中的所有数据库
safesql-review --config safesql.yaml --test-connection

# 输出：
# ✅ postgres_main: Connection successful
# ✅ mysql_analytics: Connection successful
```

#### 显示风险规则

```bash
# 显示所有规则
safesql-review --show-rules

# 输出 YAML 格式
safesql-review --show-rules --format yaml

# 输出 JSON 格式
safesql-review --show-rules --format json
```

**输出示例**：

```yaml
risk_rules:
  high_risk:
    - name: drop_table
      pattern: 'DROP\s+TABLE'
      message: DROP TABLE 操作被禁止
      enabled: true
    - name: delete_without_where
      pattern: 'DELETE\s+FROM\s+\S+\s*$'
      message: DELETE 操作缺少 WHERE 条件
      enabled: true
  medium_risk:
    - name: select_all
      pattern: 'SELECT\s+\*\s+FROM'
      message: 建议避免使用 SELECT *
      enabled: true
  # ...
```

### 输出格式

#### text 格式（默认）

```
SQL: SELECT * FROM users
Risk Level: medium
Message: 建议避免使用 SELECT *，请指定具体列
Executable: true
```

#### json 格式

```json
{
  "sql": "SELECT * FROM users",
  "risk_level": "medium",
  "message": "建议避免使用 SELECT *，请指定具体列",
  "executable": true,
  "suggestions": ["明确指定需要的列名，而不是使用 SELECT *"]
}
```

### 退出码

| 代码 | 说明 |
|------|------|
| 0 | 成功，无高风险 |
| 1 | 存在高风险 SQL（使用 `--fail-on-high-risk` 时） |
| 2 | 配置错误 |
| 3 | 文件不存在 |

### 使用场景

#### 1. 开发环境

```bash
# 快速验证 SQL
safesql-review --sql "DELETE FROM users"

# 审查迁移文件
safesql-review --file migrations/001_create_users.sql
```

#### 2. CI/CD 集成

```bash
# 在 CI 中审查 SQL 文件
safesql-review --directory ./sql --fail-on-high-risk

# 在 PR 中添加评论
safesql-review --directory ./sql --format json > review.json
```

#### 3. 代码审查

```bash
# 审查所有 SQL 文件
safesql-review --directory ./src --format json

# 生成报告
safesql-review --directory ./sql --format json > report.json
```

#### 4. 配置验证

```bash
# 验证配置文件
safesql-review --config safesql.yaml --test-connection

# 查看生效规则
safesql-review --config safesql.yaml --show-rules
```

---

## 🔧 高级用法

### 管道使用

```bash
# 从标准输入读取 SQL
echo "SELECT * FROM users" | safesql-review --sql -

# 与其他工具结合
cat queries.sql | grep "SELECT" | safesql-review --sql -
```

### 批量处理

```bash
# 批量审查多个文件
for file in sql/*.sql; do
  echo "审查: $file"
  safesql-review --file "$file"
done

# 生成汇总报告
safesql-review --directory ./sql --format json | jq '.[] | select(.risk_level == "high")'
```

### 环境变量

```bash
# 使用环境变量
export SAFESQL_CONFIG_PATH=/path/to/safesql.yaml
export POSTGRES_PASSWORD=your_password

safesql-review --test-connection
```

### 配置文件优先级

1. 命令行参数 `--config`
2. 环境变量 `SAFESQL_CONFIG_PATH`
3. 当前目录 `safesql.yaml`
4. 默认配置

---

## 📚 相关文档

- [MCP 工具 API](mcp-tools.md) - MCP 工具详细说明
- [Python API](python-api.md) - Python 编程接口
- [配置文件参考](config-reference.md) - 配置文件说明