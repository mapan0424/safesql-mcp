# 示例文件目录

本目录包含 SafeSQL MCP 的配置示例和使用示例。

## 📁 文件列表

### 配置文件示例

| 文件 | 说明 | 适用场景 |
|------|------|----------|
| [safesql.yaml](safesql.yaml) | 基础配置 | 快速开始 |
| [safesql-development.yaml](safesql-development.yaml) | 开发环境配置 | 本地开发 |
| [safesql-production.yaml](safesql-production.yaml) | 生产环境配置 | 生产部署 |

### SQL 示例

| 文件 | 说明 |
|------|------|
| [demo.sql](demo.sql) | 风险审查演示 SQL |

## 🚀 快速使用

### 1. 基础配置

```bash
# 复制基础配置
cp examples/safesql.yaml safesql.yaml

# 编辑配置
vi safesql.yaml

# 测试连接
safesql-review --config safesql.yaml --test-connection
```

### 2. 开发环境

```bash
# 使用开发环境配置
cp examples/safesql-development.yaml safesql.yaml

# 启动 MCP Server
safesql-mcp --config safesql.yaml
```

### 3. 生产环境

```bash
# 使用生产环境配置
cp examples/safesql-production.yaml safesql.yaml

# 设置环境变量
export DB_HOST=your-db-host
export DB_NAME=your-db-name
export DB_PASSWORD=your-db-password

# 测试连接
safesql-review --config safesql.yaml --test-connection

# 启动服务
safesql-mcp --config safesql.yaml
```

## 📝 配置说明

### 数据库连接

```yaml
databases:
  my_db:
    type: postgresql        # 数据库类型：postgresql 或 mysql
    host: localhost          # 主机地址
    port: 5432              # 端口
    database: mydb          # 数据库名
    user: readonly_user     # 用户名
    password: ${DB_PASSWORD} # 密码（支持环境变量）
    options:                 # 额外选项
      sslmode: require
```

### 风险规则

```yaml
risk_rules:
  high_risk:     # 高风险：自动拦截
    - name: rule_name
      pattern: 'REGEX_PATTERN'
      message: '提示消息'
  
  medium_risk:   # 中风险：警告执行
    - name: rule_name
      pattern: 'REGEX_PATTERN'
      message: '提示消息'
  
  low_risk:      # 低风险：直接执行
    - name: rule_name
      pattern: 'REGEX_PATTERN'
      message: '提示消息'
  
  whitelist:     # 白名单：忽略检查
    - name: rule_name
      pattern: 'REGEX_PATTERN'
      message: '提示消息'
```

## 🔧 自定义配置

### 添加自定义规则

```yaml
risk_rules:
  high_risk:
    - name: custom_rule
      pattern: 'CUSTOM_PATTERN'
      message: '自定义提示消息'
      description: '详细说明'
      enabled: true
```

### 多数据库配置

```yaml
databases:
  postgres_main:
    type: postgresql
    host: localhost
    port: 5432
    database: maindb
    user: readonly_user
    password: ${PG_PASSWORD}
  
  mysql_analytics:
    type: mysql
    host: localhost
    port: 3306
    database: analytics
    user: readonly_user
    password: ${MYSQL_PASSWORD}
```

### 环境变量支持

```yaml
# 使用环境变量
password: ${ENV_VAR_NAME}

# 环境变量格式
# 必须以 ${ 开头，以 } 结尾
# 例如：${DB_PASSWORD}, ${POSTGRES_HOST}
```

## 📚 更多文档

- [快速开始指南](../docs/guides/quickstart.md)
- [配置文件指南](../docs/guides/configuration.md)
- [基础使用示例](../docs/examples/basic-examples.md)
- [最佳实践](../docs/examples/best-practices.md)

## 💡 提示

1. **安全性**：生产环境务必使用只读用户
2. **环境变量**：敏感信息使用环境变量，不要硬编码
3. **SSL 连接**：生产环境建议启用 SSL
4. **日志配置**：生产环境使用 INFO 或 WARNING 级别
5. **连接池**：高并发场景配置连接池