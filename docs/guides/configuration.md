# 配置文件指南

SafeSQL MCP 配置文件完整说明。

## 📄 配置文件格式

SafeSQL MCP 使用 YAML 格式的配置文件。默认文件名：`safesql.yaml`

## 📝 完整配置示例

```yaml
# SafeSQL MCP 配置文件

# 数据库连接配置
databases:
  # PostgreSQL 示例
  postgres_main:
    type: postgresql
    host: localhost
    port: 5432
    database: mydb
    user: readonly_user
    password: ${POSTGRES_PASSWORD}  # 支持环境变量
    options:
      sslmode: require
      connect_timeout: 10
  
  # MySQL 示例
  mysql_analytics:
    type: mysql
    host: localhost
    port: 3306
    database: analytics
    user: readonly_user
    password: ${MYSQL_PASSWORD}
    options:
      charset: utf8mb4
      connect_timeout: 10

# 风险审查规则
risk_rules:
  # 高风险规则（自动拦截）
  high_risk:
    - name: drop_table
      pattern: 'DROP\s+TABLE'
      message: 'DROP TABLE 操作被禁止'
      description: '删除表操作可能导致数据丢失'
      enabled: true
    
    - name: delete_without_where
      pattern: 'DELETE\s+FROM\s+\S+\s*$'
      message: 'DELETE 操作缺少 WHERE 条件'
      description: '无条件删除将影响所有行'
      enabled: true
  
  # 中风险规则（警告执行）
  medium_risk:
    - name: select_all
      pattern: 'SELECT\s+\*\s+FROM'
      message: '建议避免使用 SELECT *，请指定具体列'
      description: 'SELECT * 会返回所有列，可能影响性能'
      enabled: true
    
    - name: like_wildcard
      pattern: "LIKE\\s+'%"
      message: '前缀通配符可能导致全表扫描'
      description: '前缀通配符无法使用索引'
      enabled: true
  
  # 低风险规则（直接执行）
  low_risk:
    - name: safe_select
      pattern: 'SELECT\s+.*\s+FROM\s+.*\s+WHERE'
      message: '安全查询'
      enabled: true
  
  # 白名单（忽略检查）
  whitelist:
    - name: health_check
      pattern: 'SELECT\s+1'
      message: '健康检查查询'
      enabled: true

# MCP Server 配置
mcp_server:
  name: safesql
  version: "1.0.0"
  description: "SafeSQL MCP Server - 安全数据库访问"

# EXPLAIN 配置
explain:
  enabled: true
  analyze: true      # 包含实际执行统计
  buffers: true      # 包含缓冲区使用情况
  format: TEXT       # TEXT, JSON, XML, YAML

# 日志配置
logging:
  level: INFO        # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null         # 日志文件路径，null 表示只输出到控制台
```

## 🔧 配置项详解

### 数据库连接 (`databases`)

每个数据库连接包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 数据库类型：`postgresql` 或 `mysql` |
| `host` | string | 是 | 数据库主机地址 |
| `port` | integer | 是 | 数据库端口 |
| `database` | string | 是 | 数据库名称 |
| `user` | string | 是 | 用户名 |
| `password` | string | 是 | 密码（支持环境变量） |
| `options` | object | 否 | 额外连接选项 |

**环境变量支持**：

```yaml
password: ${ENV_VAR_NAME}  # 从环境变量读取
password: "plain_password" # 明文密码（不推荐）
```

**PostgreSQL 选项**：

```yaml
options:
  sslmode: require          # disable, allow, prefer, require
  connect_timeout: 10       # 连接超时（秒）
  application_name: safesql # 应用名称
```

**MySQL 选项**：

```yaml
options:
  charset: utf8mb4          # 字符集
  connect_timeout: 10       # 连接超时（秒）
  autocommit: true          # 自动提交
```

### 风险规则 (`risk_rules`)

#### 规则结构

```yaml
- name: rule_name           # 规则名称（唯一标识）
  pattern: 'REGEX_PATTERN'  # 正则表达式
  level: high               # 风险等级：high, medium, low, safe
  message: '提示消息'        # 风险提示消息
  description: '详细说明'    # 详细描述（可选）
  enabled: true             # 是否启用
```

#### 风险等级

| 等级 | 说明 | 行为 |
|------|------|------|
| `high` | 高风险 | 自动拦截，不允许执行 |
| `medium` | 中风险 | 警告但允许执行 |
| `low` | 低风险 | 直接执行 |
| `safe` | 安全 | 忽略检查（白名单） |

#### 正则表达式语法

SafeSQL MCP 使用 Python 正则表达式语法：

```yaml
# 匹配 DROP TABLE
pattern: 'DROP\s+TABLE'

# 匹配 SELECT *
pattern: 'SELECT\s+\*\s+FROM'

# 匹配无 WHERE 的 DELETE
pattern: 'DELETE\s+FROM\s+\S+\s*$'

# 匹配 LIKE 前缀通配符
pattern: "LIKE\\s+'%"

# 匹配多个关键字
pattern: '(GRANT|REVOKE)\s+'
```

**常用模式**：

| 模式 | 说明 |
|------|------|
| `\s+` | 一个或多个空白字符 |
| `\S+` | 一个或多个非空白字符 |
| `.*` | 任意字符（零个或多个） |
| `$` | 行尾 |
| `(?i)` | 忽略大小写 |
| `(?:...)` | 非捕获组 |

#### 内置规则

SafeSQL MCP 内置了以下规则：

**高风险规则**：
- `drop_table` - DROP TABLE 操作
- `drop_database` - DROP DATABASE 操作
- `drop_index` - DROP INDEX 操作
- `truncate_table` - TRUNCATE TABLE 操作
- `delete_without_where` - 无条件 DELETE
- `update_without_where` - 无条件 UPDATE
- `grant_revoke` - 权限操作
- `alter_table_drop_column` - 删除列
- `system_tables` - 系统表访问
- `stored_procedures` - 存储过程执行

**中风险规则**：
- `select_all` - SELECT * 查询
- `insert_without_columns` - 无列名 INSERT
- `like_prefix_wildcard` - 前缀通配符
- `multiple_joins` - 多表 JOIN
- `subquery_in_where` - WHERE 子查询
- `or_conditions` - 多个 OR 条件

**低风险规则**：
- `safe_select` - 带 WHERE 的 SELECT
- `safe_insert` - 指定列名的 INSERT
- `safe_update` - 带 WHERE 的 UPDATE
- `safe_delete` - 带 WHERE 的 DELETE

**白名单规则**：
- `health_check` - SELECT 1
- `version_check` - SELECT version()
- `current_time` - SELECT NOW()

### MCP Server 配置 (`mcp_server`)

```yaml
mcp_server:
  name: safesql              # 服务器名称
  version: "1.0.0"           # 版本号
  description: "描述信息"     # 服务器描述
```

### EXPLAIN 配置 (`explain`)

```yaml
explain:
  enabled: true              # 是否启用 EXPLAIN
  analyze: true              # 包含实际执行统计
  buffers: true              # 包含缓冲区使用情况
  format: TEXT               # 输出格式：TEXT, JSON, XML, YAML
```

### 日志配置 (`logging`)

```yaml
logging:
  level: INFO                # 日志级别
  format: "%(asctime)s..."   # 日志格式
  file: /var/log/safesql.log # 日志文件（null 表示控制台）
```

**日志级别**：
- `DEBUG` - 详细调试信息
- `INFO` - 一般信息
- `WARNING` - 警告信息
- `ERROR` - 错误信息
- `CRITICAL` - 严重错误

## 🔒 安全最佳实践

### 1. 使用只读用户

```yaml
databases:
  my_db:
    type: postgresql
    user: readonly_user      # 使用只读用户
    password: ${DB_PASSWORD} # 从环境变量读取密码
```

### 2. 限制数据库权限

```sql
-- PostgreSQL
CREATE USER readonly_user WITH PASSWORD 'password';
GRANT CONNECT ON DATABASE mydb TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- MySQL
CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'password';
GRANT SELECT ON mydb.* TO 'readonly_user'@'%';
FLUSH PRIVILEGES;
```

### 3. 使用环境变量

```bash
# 设置环境变量
export POSTGRES_PASSWORD="your_secure_password"
export MYSQL_PASSWORD="your_secure_password"

# 在配置文件中引用
password: ${POSTGRES_PASSWORD}
```

### 4. 限制网络访问

```yaml
databases:
  my_db:
    host: 10.0.0.100        # 使用内网地址
    options:
      sslmode: require       # 启用 SSL
```

## 📋 配置文件模板

### 开发环境

```yaml
databases:
  dev_db:
    type: postgresql
    host: localhost
    port: 5432
    database: devdb
    user: dev_user
    password: dev_password

risk_rules: {}  # 使用默认规则

logging:
  level: DEBUG
```

### 生产环境

```yaml
databases:
  prod_db:
    type: postgresql
    host: ${DB_HOST}
    port: 5432
    database: ${DB_NAME}
    user: readonly_user
    password: ${DB_PASSWORD}
    options:
      sslmode: require
      connect_timeout: 30

risk_rules:
  high_risk:
    - name: block_all_writes
      pattern: '(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER)\s+'
      message: '生产环境禁止写操作'
      enabled: true

logging:
  level: WARNING
  file: /var/log/safesql.log
```

### 测试环境

```yaml
databases:
  test_db:
    type: sqlite
    database: :memory:

risk_rules: {}

logging:
  level: DEBUG
```

## 🔍 配置验证

### 检查配置文件语法

```bash
safesql-review --config safesql.yaml --check
```

### 测试数据库连接

```bash
safesql-review --config safesql.yaml --test-connection
```

### 查看生效规则

```bash
safesql-review --config safesql.yaml --show-rules
```

## 📚 下一步

- [风险规则配置详解](risk-rules.md) - 更多规则示例
- [数据库连接配置](database-connection.md) - 各数据库详细配置
- [MCP Server 配置](mcp-server.md) - 服务器高级配置