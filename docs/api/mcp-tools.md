# MCP 工具 API 参考

SafeSQL MCP 提供的 MCP 工具详细说明。

## 📋 工具列表

| 工具 | 说明 | 参数 |
|------|------|------|
| `query` | 执行 SQL 查询 | database, sql, explain, timeout |
| `validate` | 验证 SQL 风险 | sql |
| `explain` | 生成 EXPLAIN 计划 | database, sql |
| `databases` | 列出数据库连接 | 无 |
| `schema` | 获取数据库 Schema | database, table |
| `test_connection` | 测试数据库连接 | database |

---

## 🔍 query

执行 SQL 查询并返回结果，自动进行风险审查。

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `database` | string | 是 | - | 数据库连接名称 |
| `sql` | string | 是 | - | SQL 查询语句 |
| `explain` | boolean | 否 | false | 是否生成 EXPLAIN 计划 |
| `timeout` | integer | 否 | 30 | 查询超时时间（秒） |

### 返回值

```json
{
  "risk_assessment": {
    "sql": "SELECT id, name FROM users WHERE id = 1",
    "risk_level": "low",
    "message": "安全查询",
    "matched_rule": "safe_select",
    "suggestions": [],
    "is_executable": true,
    "requires_warning": false
  },
  "executable": true,
  "warning_required": false,
  "query_result": {
    "columns": ["id", "name"],
    "rows": [[1, "John Doe"]],
    "row_count": 1,
    "execution_time": 0.023
  },
  "explain_plan": "Seq Scan on users  (cost=0.00..1.02 rows=1 width=100)",
  "message": "✅ 查询执行成功"
}
```

### 示例

```python
# 基础查询
result = await session.call_tool(
    "query",
    arguments={
        "database": "my_postgres",
        "sql": "SELECT id, name FROM users WHERE id = 1"
    }
)

# 带 EXPLAIN 的查询
result = await session.call_tool(
    "query",
    arguments={
        "database": "my_postgres",
        "sql": "SELECT * FROM users WHERE status = 'active'",
        "explain": True,
        "timeout": 60
    }
)

# 高风险查询（会被拦截）
result = await session.call_tool(
    "query",
    arguments={
        "database": "my_postgres",
        "sql": "DROP TABLE users"
    }
)
# 返回：executable: false, message: "🚫 高风险 SQL 被拦截"
```

### 错误处理

```json
{
  "error": "database 'nonexistent' not found",
  "message": "❌ 查询执行失败"
}
```

---

## ✅ validate

验证 SQL 语句的风险等级，不执行查询。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sql` | string | 是 | SQL 查询语句 |

### 返回值

```json
{
  "sql": "SELECT * FROM users",
  "risk_assessment": {
    "risk_level": "medium",
    "message": "建议避免使用 SELECT *，请指定具体列",
    "matched_rule": "select_all",
    "suggestions": ["明确指定需要的列名，而不是使用 SELECT *"],
    "is_executable": true,
    "requires_warning": true
  },
  "executable": true,
  "warning_required": true
}
```

### 示例

```python
# 验证安全 SQL
result = await session.call_tool(
    "validate",
    arguments={
        "sql": "SELECT id, name FROM users WHERE id = 1"
    }
)
# risk_level: "low", executable: true

# 验证高风险 SQL
result = await session.call_tool(
    "validate",
    arguments={
        "sql": "DELETE FROM users"
    }
)
# risk_level: "high", executable: false

# 验证中风险 SQL
result = await session.call_tool(
    "validate",
    arguments={
        "sql": "SELECT * FROM users WHERE name LIKE '%john%'"
    }
)
# risk_level: "medium", executable: true, warning_required: true
```

---

## 📊 explain

生成 SQL 查询的 EXPLAIN 执行计划。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `database` | string | 是 | 数据库连接名称 |
| `sql` | string | 是 | SQL 查询语句 |

### 返回值

```json
{
  "sql": "SELECT * FROM users WHERE id = 1",
  "explain_plan": "Seq Scan on users  (cost=0.00..1.02 rows=1 width=100)\n  Filter: (id = 1)"
}
```

### 示例

```python
# 获取 EXPLAIN 计划
result = await session.call_tool(
    "explain",
    arguments={
        "database": "my_postgres",
        "sql": "SELECT * FROM users WHERE id = 1"
    }
)

# PostgreSQL EXPLAIN 输出示例：
# Seq Scan on users  (cost=0.00..1.02 rows=1 width=100)
#   Filter: (id = 1)

# MySQL EXPLAIN 输出示例：
# id | select_type | table | type | possible_keys | key | key_len | ref | rows | Extra
# 1  | SIMPLE      | users | ALL  | NULL          | NULL| NULL    | NULL| 1    | Using where
```

---

## 🗄️ databases

列出所有可用的数据库连接。

### 参数

无

### 返回值

```json
{
  "databases": {
    "postgres_main": {
      "type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database": "mydb",
      "connected": true
    },
    "mysql_analytics": {
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "analytics",
      "connected": false
    }
  },
  "count": 2
}
```

### 示例

```python
# 列出所有数据库
result = await session.call_tool(
    "databases",
    arguments={}
)

# 输出：
# databases: {
#   "postgres_main": {"type": "postgresql", "connected": true},
#   "mysql_analytics": {"type": "mysql", "connected": false}
# }
# count: 2
```

---

## 📋 schema

获取数据库的 Schema 信息。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `database` | string | 是 | 数据库连接名称 |
| `table` | string | 否 | 特定表名（可选） |

### 返回值

#### 获取整个数据库 Schema

```json
{
  "database": "my_postgres",
  "table": null,
  "schema": {
    "database": "mydb",
    "user": "readonly_user",
    "version": "PostgreSQL 15.0",
    "schemas": ["public"],
    "tables": [
      {"schema": "public", "name": "users", "type": "BASE TABLE"},
      {"schema": "public", "name": "orders", "type": "BASE TABLE"}
    ]
  }
}
```

#### 获取特定表 Schema

```json
{
  "database": "my_postgres",
  "table": "users",
  "schema": {
    "table": "users",
    "columns": [
      {"name": "id", "type": "integer", "nullable": false, "default": "nextval('users_id_seq'::regclass)"},
      {"name": "name", "type": "character varying", "nullable": true, "default": null},
      {"name": "email", "type": "character varying", "nullable": true, "default": null}
    ],
    "indexes": [
      {"name": "users_pkey", "definition": "CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id)"}
    ],
    "constraints": [
      {"name": "users_pkey", "type": "PRIMARY KEY"}
    ]
  }
}
```

### 示例

```python
# 获取整个数据库 Schema
result = await session.call_tool(
    "schema",
    arguments={
        "database": "my_postgres"
    }
)

# 获取特定表 Schema
result = await session.call_tool(
    "schema",
    arguments={
        "database": "my_postgres",
        "table": "users"
    }
)
```

---

## 🔌 test_connection

测试数据库连接是否正常。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `database` | string | 是 | 数据库连接名称 |

### 返回值

```json
{
  "database": "my_postgres",
  "connected": true,
  "message": "Connection successful"
}
```

### 示例

```python
# 测试连接
result = await session.call_tool(
    "test_connection",
    arguments={
        "database": "my_postgres"
    }
)

# 成功：connected: true, message: "Connection successful"
# 失败：connected: false, message: "Connection failed"
```

---

## 📚 MCP 资源

除了工具，SafeSQL MCP 还提供资源访问。

### 资源列表

| URI | 说明 | MIME 类型 |
|-----|------|-----------|
| `safesql://database/{name}/schema` | 数据库 Schema | application/json |
| `safesql://database/{name}/tables` | 表列表 | application/json |
| `safesql://database/{name}/table/{table}` | 表 Schema | application/json |

### 示例

```python
# 获取数据库 Schema 资源
schema = await session.read_resource("safesql://database/my_postgres/schema")

# 获取表列表资源
tables = await session.read_resource("safesql://database/my_postgres/tables")

# 获取特定表 Schema 资源
table_schema = await session.read_resource("safesql://database/my_postgres/table/users")
```

---

## 🔧 错误处理

### 错误响应格式

```json
{
  "error": "错误描述",
  "message": "用户友好的错误消息",
  "code": "ERROR_CODE"
}
```

### 常见错误

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `database not found` | 数据库连接不存在 | 检查配置文件中的数据库名称 |
| `connection failed` | 数据库连接失败 | 检查数据库连接参数 |
| `query timeout` | 查询超时 | 增加 timeout 参数或优化查询 |
| `high risk blocked` | 高风险查询被拦截 | 修改 SQL 或调整风险规则 |

### 错误处理示例

```python
try:
    result = await session.call_tool(
        "query",
        arguments={
            "database": "my_postgres",
            "sql": "SELECT * FROM users"
        }
    )
    
    if "error" in result:
        print(f"错误: {result['error']}")
    elif not result.get("executable", True):
        print(f"高风险被拦截: {result['message']}")
    else:
        print(f"查询成功: {result['query_result']}")
        
except Exception as e:
    print(f"异常: {e}")
```

---

## 📖 相关文档

- [Python API](python-api.md) - Python 编程接口
- [CLI 命令参考](cli-reference.md) - 命令行工具
- [配置文件参考](config-reference.md) - 配置文件说明