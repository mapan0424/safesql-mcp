# SafeSQL MCP

**AI Agent Safe Database Access MCP Server + SQL Risk Audit Tool**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-brightgreen.svg)](https://modelcontextprotocol.io/)
[![GitHub Release](https://img.shields.io/github/v/release/mapan0424/safesql-mcp)](https://github.com/mapan0424/safesql-mcp/releases)

> **SafeSQL MCP** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides secure database access for AI agents. It includes a SQL risk audit engine that evaluates SQL statements before execution, blocking high-risk operations and warning about medium-risk ones. This ensures database safety when AI models generate and execute SQL queries.

**Key Features:**
- 🛡️ **SQL Risk Audit** - Three-level risk assessment (High/Medium/Low) with configurable rules
- 🗄️ **Multi-Database** - PostgreSQL, MySQL, Oracle support with EXPLAIN plan analysis
- 🔌 **MCP Server** - Standard MCP protocol compatible with Claude, Cursor, Codex, and other AI tools
- 🚀 **CI/CD Ready** - GitHub Action for automated SQL risk review in PRs
- 🔧 **Extensible** - Custom risk rules, whitelist support, and plugin architecture

**Use Cases:**
- Safe database access for AI coding assistants (Claude Desktop, Cursor, Codex CLI)
- SQL risk review in CI/CD pipelines
- Database security compliance for AI-generated queries
- Text-to-SQL application security

---

**SafeSQL MCP** 是一个 Model Context Protocol (MCP) Server，为 AI Agent 提供安全的数据库访问能力。它通过 SQL 风险审查引擎，在 AI 生成的 SQL 执行前进行安全评估，防止高风险操作，确保数据库安全。

## ✨ 核心特性

### 🛡️ SQL 风险审查引擎
- **三级风险评估**：高风险（拦截）、中风险（警告）、低风险（执行）
- **智能规则引擎**：基于 SQL 语法分析和模式匹配
- **可扩展规则**：支持自定义风险规则和白名单

### 🗄️ 多数据库支持
- **PostgreSQL**：完整支持，包括 EXPLAIN 分析
- **MySQL**：完整支持，包括 EXPLAIN 分析
- **Oracle**：完整支持，包括 EXPLAIN 分析
- **国产数据库**：预留扩展接口（虚谷、达梦、金仓等）

### 🔌 MCP Server 集成
- **标准 MCP 协议**：兼容所有 MCP 客户端
- **工具注册**：自动注册数据库查询工具
- **资源暴露**：数据库 schema 作为 MCP 资源

### 📊 执行分析
- **EXPLAIN 计划**：自动生成查询执行计划
- **性能警告**：识别潜在性能问题
- **优化建议**：提供 SQL 优化建议

### 🚀 CI/CD 集成
- **GitHub Action**：PR 中自动检测高风险 SQL
- **评论提醒**：自动在 PR 中添加风险评论
- **状态检查**：阻止包含高风险 SQL 的 PR 合并

## 🚀 快速开始

### 安装

```bash
# 使用 pip 安装
pip install safesql-mcp

# 或从源码安装
git clone https://github.com/mapan0424/safesql-mcp.git
cd safesql-mcp
pip install -e .
```

### 配置

创建配置文件 `safesql.yaml`：

```yaml
# 数据库连接配置
databases:
  postgres_main:
    type: postgresql
    host: localhost
    port: 5432
    database: mydb
    user: readonly_user
    password: ${POSTGRES_PASSWORD}
    
  mysql_analytics:
    type: mysql
    host: localhost
    port: 3306
    database: analytics
    user: readonly_user
    password: ${MYSQL_PASSWORD}

# 风险审查规则
risk_rules:
  # 高风险操作（自动拦截）
  high_risk:
    - pattern: "DROP\\s+TABLE"
      message: "DROP TABLE 操作被禁止"
    - pattern: "DELETE\\s+FROM\\s+.*\\s+WHERE\\s+1\\s*=\\s*1"
      message: "全表删除操作被禁止"
    - pattern: "UPDATE\\s+.*\\s+SET\\s+.*\\s+WHERE\\s+1\\s*=\\s*1"
      message: "全表更新操作被禁止"
      
  # 中风险操作（警告但允许执行）
  medium_risk:
    - pattern: "SELECT\\s+\\*\\s+FROM"
      message: "建议避免使用 SELECT *，请指定具体列"
    - pattern: "INSERT\\s+INTO\\s+.*\\s+VALUES"
      message: "建议使用 INSERT INTO ... (columns) VALUES 语法"
      
  # 低风险操作（直接执行）
  low_risk:
    - pattern: "SELECT\\s+.*\\s+FROM\\s+.*\\s+WHERE"
      message: "安全查询"
      
  # 白名单（忽略风险检查）
  whitelist:
    - pattern: "SELECT\\s+1"
      message: "健康检查查询"

# MCP Server 配置
mcp_server:
  name: "safesql"
  version: "1.0.0"
  description: "SafeSQL MCP Server - 安全数据库访问"
  
# EXPLAIN 配置
explain:
  enabled: true
  analyze: true  # 包含实际执行统计
  buffers: true  # 包含缓冲区使用情况
  format: "TEXT"  # TEXT, JSON, XML, YAML
```

### 启动 MCP Server

```bash
# 使用配置文件启动
safesql-mcp --config safesql.yaml

# 或使用环境变量
export SAFESQL_CONFIG_PATH=/path/to/safesql.yaml
safesql-mcp
```

### 在 AI Agent 中使用

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
        # 初始化连接
        await session.initialize()
        
        # 列出可用工具
        tools = await session.list_tools()
        print("可用工具:", [tool.name for tool in tools.tools])
        
        # 执行安全查询
        result = await session.call_tool(
            "query",
            arguments={
                "database": "postgres_main",
                "sql": "SELECT * FROM users WHERE id = 1",
                "explain": True
            }
        )
        
        print("查询结果:", result)
```

## 📋 MCP 工具列表

### 查询工具

#### `query`
执行 SQL 查询并返回结果，自动进行风险审查。

**参数：**
- `database` (string): 数据库连接名称
- `sql` (string): SQL 查询语句
- `explain` (boolean, 可选): 是否生成 EXPLAIN 计划
- `timeout` (integer, 可选): 查询超时时间（秒）

**返回：**
- `result`: 查询结果集
- `risk_level`: 风险等级 (high/medium/low)
- `risk_message`: 风险提示信息
- `explain_plan`: EXPLAIN 执行计划（如果启用）

#### `validate`
验证 SQL 语句的风险等级，不执行查询。

**参数：**
- `sql` (string): SQL 查询语句

**返回：**
- `risk_level`: 风险等级
- `risk_message`: 风险提示
- `suggestions`: 优化建议

#### `explain`
生成 SQL 查询的 EXPLAIN 执行计划。

**参数：**
- `database` (string): 数据库连接名称
- `sql` (string): SQL 查询语句

**返回：**
- `explain_plan`: EXPLAIN 执行计划
- `analysis`: 执行计划分析

### 资源工具

#### `databases`
列出所有可用的数据库连接。

#### `schema`
获取数据库的 schema 信息，包括表、列、索引等。

**参数：**
- `database` (string): 数据库连接名称
- `table` (string, 可选): 特定表名

## 🛡️ 风险审查规则

### 高风险操作（自动拦截）
- `DROP TABLE/DATABASE/INDEX`
- `DELETE FROM` 无 WHERE 条件
- `UPDATE ... SET` 无 WHERE 条件
- `TRUNCATE TABLE`
- `ALTER TABLE ... DROP COLUMN`
- `GRANT/REVOKE` 权限操作
- 系统表/系统存储过程访问

### 中风险操作（警告执行）
- `SELECT *` 查询
- 缺少列名的 `INSERT INTO`
- 多表 JOIN 无索引条件
- 子查询性能风险
- `LIKE '%...'` 前缀通配符

### 低风险操作（直接执行）
- 带 WHERE 条件的 SELECT
- 指定列名的 INSERT
- 单表简单查询
- 使用索引的查询

## 🚀 GitHub Action 集成

在 `.github/workflows/safesql-review.yml` 中配置：

```yaml
name: SQL Risk Review

on:
  pull_request:
    paths:
      - '**/*.sql'
      - '**/migrations/**'
      - '**/queries/**'

jobs:
  sql-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install SafeSQL
        run: pip install safesql-mcp
        
      - name: Review SQL Files
        run: |
          safesql-review --github-pr --fail-on-high-risk
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '⚠️ **SQL 风险审查失败**\n\n发现高风险 SQL 操作，请检查并修复。'
            })
```

## 🔧 开发指南

### 项目结构

```
safesql-mcp/
├── src/
│   └── safesql_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP Server 主入口
│       ├── core/
│       │   ├── __init__.py
│       │   ├── engine.py      # 风险审查引擎
│       │   ├── rules.py       # 风险规则定义
│       │   └── analyzer.py    # SQL 分析器
│       ├── databases/
│       │   ├── __init__.py
│       │   ├── base.py        # 数据库基类
│       │   ├── postgresql.py  # PostgreSQL 实现
│       │   └── mysql.py       # MySQL 实现
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── tools.py       # MCP 工具实现
│       │   └── resources.py   # MCP 资源实现
│       └── utils/
│           ├── __init__.py
│           ├── config.py      # 配置管理
│           └── logger.py      # 日志工具
├── tests/                     # 测试文件
├── docs/                      # 文档
├── .github/                   # GitHub 配置
│   └── workflows/
│       └── sql-review.yml     # GitHub Action
├── pyproject.toml             # 项目配置
├── requirements.txt           # 依赖
└── README.md                  # 项目说明
```

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/mapan0424/safesql-mcp.git
cd safesql-mcp

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 代码格式化
black src/ tests/
isort src/ tests/

# 类型检查
mypy src/
```

### 添加新数据库支持

1. 在 `src/safesql_mcp/databases/` 中创建新的数据库类
2. 继承 `DatabaseBase` 基类
3. 实现必要的方法：`connect()`, `execute()`, `explain()`, `get_schema()`
4. 在配置文件中添加数据库类型映射
5. 更新文档和测试

## 📈 性能优化

### 查询缓存
- 支持 Redis 和内存缓存
- 基于 SQL 语句和参数的缓存键
- 可配置的缓存过期策略

### 连接池
- 数据库连接池管理
- 自动连接回收和重连
- 连接健康检查

### 异步支持
- 全异步 I/O 操作
- 并发查询支持
- 非阻塞风险审查

## 📚 文档

完整文档请访问 [docs](docs/) 目录：

- **[快速开始指南](docs/guides/quickstart.md)** - 5 分钟上手
- **[安装指南](docs/guides/installation.md)** - 详细安装步骤
- **[配置文件指南](docs/guides/configuration.md)** - 配置详解
- **[基础使用示例](docs/examples/basic-examples.md)** - 常见场景
- **[最佳实践](docs/examples/best-practices.md)** - 生产环境建议
- **[MCP 工具 API](docs/api/mcp-tools.md)** - 工具详细说明
- **[CLI 命令参考](docs/api/cli-reference.md)** - 命令行工具
- **[系统架构](docs/architecture.md)** - 架构设计
- **[集成示例](docs/demos.md)** - Claude Desktop, Cursor, Codex CLI 等集成示例

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范
- 代码风格：Black + isort
- 类型注解：使用 type hints
- 测试覆盖：新功能必须包含测试
- 文档更新：重要变更需要更新文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 协议规范
- [SQLGlot](https://github.com/tobymao/sqlglot) - SQL 解析器
- [Psycopg](https://www.psycopg.org/) - PostgreSQL 适配器
- [PyMySQL](https://pymysql.readthedocs.io/) - MySQL 适配器

## 📞 支持

- 📧 邮箱：315337987@qq.com
- 🐛 问题反馈：[GitHub Issues](https://github.com/mapan0424/safesql-mcp/issues)
- 📖 文档：[GitHub Wiki](https://github.com/mapan0424/safesql-mcp/wiki)

---

**SafeSQL MCP** - 让 AI Agent 安全地访问数据库 🚀