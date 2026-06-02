# 系统架构

SafeSQL MCP 架构设计说明。

## 📐 架构概览

SafeSQL MCP 采用分层架构设计，核心组件包括：

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Client Layer                         │
│  (Claude Desktop, Python Client, Custom Applications)       │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Tools     │  │  Resources  │  │   Server    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Engine Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Risk Engine │  │  Analyzer   │  │   Rules     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PostgreSQL  │  │    MySQL    │  │   Base DB   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 🧩 核心组件

### 1. MCP Server Layer

MCP Server Layer 负责处理 MCP 协议通信，提供工具和资源接口。

**组件**：

- **Server**: MCP 服务器主入口，处理协议初始化和生命周期管理
- **Tools**: 提供可调用的工具（query, validate, explain 等）
- **Resources**: 提供可访问的资源（schema, tables 等）

**职责**：
- 接收 MCP 客户端请求
- 参数验证和转换
- 调用 Core Engine 处理业务逻辑
- 格式化响应返回给客户端

### 2. Core Engine Layer

Core Engine Layer 是系统的核心，负责 SQL 风险审查和分析。

**组件**：

- **RiskEngine**: 风险审查引擎，评估 SQL 风险等级
- **SQLAnalyzer**: SQL 分析器，解析 SQL 结构和特征
- **RiskRules**: 风险规则定义和管理

**职责**：
- SQL 语句解析和分析
- 风险等级评估（HIGH, MEDIUM, LOW, SAFE）
- 性能问题检测
- 优化建议生成

### 3. Database Layer

Database Layer 负责数据库连接和查询执行。

**组件**：

- **DatabaseBase**: 数据库基类，定义通用接口
- **PostgreSQLDatabase**: PostgreSQL 实现
- **MySQLDatabase**: MySQL 实现

**职责**：
- 数据库连接管理
- SQL 查询执行
- EXPLAIN 计划生成
- Schema 信息获取

## 🔄 数据流

### 查询执行流程

```
Client Request
     │
     ▼
┌─────────────────┐
│  MCP Server     │ ← 接收请求
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Risk Engine    │ ← 风险评估
└────────┬────────┘
         │
         ├─ HIGH Risk → 拦截，返回错误
         │
         ├─ MEDIUM Risk → 警告，继续执行
         │
         └─ LOW/SAFE Risk → 继续执行
                    │
                    ▼
         ┌─────────────────┐
         │  Database       │ ← 执行查询
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Response       │ ← 返回结果
         └─────────────────┘
```

### 详细流程

1. **请求接收**
   - MCP Server 接收客户端请求
   - 解析请求参数（database, sql, explain 等）

2. **风险评估**
   - Risk Engine 分析 SQL 语句
   - 匹配风险规则
   - 确定风险等级

3. **风险处理**
   - **HIGH**: 立即返回错误，不执行查询
   - **MEDIUM**: 添加警告信息，继续执行
   - **LOW/SAFE**: 直接执行

4. **查询执行**
   - 连接到指定数据库
   - 执行 SQL 查询
   - 生成 EXPLAIN 计划（如果启用）

5. **响应返回**
   - 格式化查询结果
   - 包含风险评估信息
   - 返回给客户端

## 🛡️ 安全模型

### 风险等级定义

```
┌─────────────────────────────────────────────────────────┐
│                    Risk Level Hierarchy                 │
├─────────────────────────────────────────────────────────┤
│  SAFE    │ 忽略检查，直接执行                           │
│  LOW     │ 直接执行，无警告                             │
│  MEDIUM  │ 警告执行，提示风险                           │
│  HIGH    │ 自动拦截，拒绝执行                           │
└─────────────────────────────────────────────────────────┘
```

### 规则匹配机制

```
SQL Input
     │
     ▼
┌─────────────────┐
│  Preprocess     │ ← 清理注释、标准化格式
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Whitelist      │ ← 检查白名单
└────────┬────────┘
         │
         ├─ Match → SAFE
         │
         └─ No Match
                    │
                    ▼
         ┌─────────────────┐
         │  High Risk      │ ← 检查高风险规则
         └────────┬────────┘
                  │
                  ├─ Match → HIGH
                  │
                  └─ No Match
                             │
                             ▼
                  ┌─────────────────┐
                  │  Medium Risk    │ ← 检查中风险规则
                  └────────┬────────┘
                           │
                           ├─ Match → MEDIUM
                           │
                           └─ No Match
                                      │
                                      ▼
                           ┌─────────────────┐
                           │  Deep Analysis  │ ← 深度分析
                           └────────┬────────┘
                                    │
                                    ▼
                              LOW or MEDIUM
```

### 安全边界

1. **只读访问**
   - 默认只允许 SELECT 查询
   - 写操作需要显式配置

2. **参数化查询**
   - 支持参数化查询防止 SQL 注入
   - 自动转义特殊字符

3. **连接隔离**
   - 每个查询使用独立连接
   - 防止连接状态污染

4. **超时控制**
   - 查询超时限制
   - 防止长时间运行查询

## 📦 模块依赖

```
safesql_mcp/
├── __init__.py
├── server.py              # MCP Server 主入口
├── cli.py                 # CLI 工具
├── core/
│   ├── __init__.py
│   ├── engine.py          # 风险审查引擎
│   ├── rules.py           # 风险规则定义
│   └── analyzer.py        # SQL 分析器
├── databases/
│   ├── __init__.py
│   ├── base.py            # 数据库基类
│   ├── postgresql.py      # PostgreSQL 实现
│   └── mysql.py           # MySQL 实现
├── mcp/
│   ├── __init__.py
│   ├── tools.py           # MCP 工具
│   └── resources.py       # MCP 资源
└── utils/
    ├── __init__.py
    ├── config.py          # 配置管理
    └── logger.py          # 日志工具
```

### 依赖关系

```python
# server.py 依赖
from .core.engine import RiskEngine
from .databases.postgresql import PostgreSQLDatabase
from .databases.mysql import MySQLDatabase
from .mcp.tools import SafeSQLTools
from .mcp.resources import SafeSQLResources

# core/engine.py 依赖
from .rules import RiskLevel, RiskRule, RiskAssessment, DefaultRiskRules
from .analyzer import SQLAnalyzer

# databases/postgresql.py 依赖
from .base import DatabaseBase, DatabaseConfig, QueryResult
import psycopg2

# mcp/tools.py 依赖
from ..core.engine import RiskEngine
from ..databases.base import DatabaseBase
from mcp import types
```

## 🔌 扩展点

### 1. 添加新数据库支持

```python
# databases/oracle.py
from .base import DatabaseBase, DatabaseConfig, QueryResult

class OracleDatabase(DatabaseBase):
    """Oracle 数据库连接器"""
    
    async def connect(self) -> None:
        # 实现 Oracle 连接
        pass
    
    async def execute(self, sql: str, params=None) -> QueryResult:
        # 实现 Oracle 查询
        pass
    
    async def explain(self, sql: str, analyze: bool = False) -> str:
        # 实现 Oracle EXPLAIN
        pass
    
    # ... 其他方法
```

### 2. 添加自定义风险规则

```python
from safesql_mcp.core.rules import RiskRule, RiskLevel

custom_rules = [
    RiskRule(
        name="custom_rule",
        pattern=r"CUSTOM_PATTERN",
        level=RiskLevel.HIGH,
        message="自定义风险消息"
    )
]

engine = RiskEngine(custom_rules=custom_rules)
```

### 3. 添加自定义 MCP 工具

```python
from mcp import types

@server.call_tool()
async def handle_custom_tool(name: str, arguments: dict):
    if name == "custom_tool":
        # 实现自定义工具逻辑
        return [types.TextContent(type="text", text="结果")]
```

## 🚀 性能优化

### 1. 连接池

```python
# 使用连接池减少连接开销
databases:
  my_db:
    type: postgresql
    host: localhost
    options:
      min_connections: 2
      max_connections: 10
```

### 2. 查询缓存

```python
# 缓存频繁查询的结果
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_assess(sql: str):
    return engine.assess_sql(sql)
```

### 3. 异步并发

```python
# 并发执行多个查询
import asyncio

async def parallel_queries(queries: list):
    tasks = [db.execute(sql) for sql in queries]
    return await asyncio.gather(*tasks)
```

## 📊 监控指标

### 关键指标

- **查询延迟**: 查询执行时间
- **风险分布**: HIGH/MEDIUM/LOW 查询比例
- **拦截率**: 被拦截的查询比例
- **连接池使用率**: 活跃连接数

### 日志记录

```python
# 记录关键事件
logger.info(f"Query executed: {sql[:50]}... risk={risk_level}")
logger.warning(f"High risk query blocked: {sql[:50]}...")
logger.error(f"Query failed: {error}")
```

## 🔮 未来规划

### 短期（1-3 个月）

- 添加更多数据库支持（达梦、金仓、虚谷）
- 实现查询缓存机制
- 添加更多性能指标

### 中期（3-6 个月）

- 支持自定义插件系统
- 实现分布式部署
- 添加 Web UI 管理界面

### 长期（6-12 个月）

- 支持 AI 驱动的 SQL 优化建议
- 实现自动化性能调优
- 集成更多 DevOps 工具