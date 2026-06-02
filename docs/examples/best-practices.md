# 最佳实践

SafeSQL MCP 生产环境最佳实践。

## 🎯 核心原则

1. **最小权限原则**：只授予必要的数据库权限
2. **防御性编程**：假设所有输入都是不可信的
3. **可观测性**：记录关键操作和错误
4. **渐进式部署**：先在测试环境验证

---

## 🗄️ 数据库配置

### 1. 使用只读用户

**❌ 不推荐**：
```yaml
databases:
  prod_db:
    user: admin
    password: admin_password
```

**✅ 推荐**：
```yaml
databases:
  prod_db:
    user: readonly_user
    password: ${READONLY_PASSWORD}
```

### 2. 创建专用只读用户

**PostgreSQL**：
```sql
-- 创建只读用户
CREATE USER safesql_user WITH PASSWORD 'secure_password';

-- 授予连接权限
GRANT CONNECT ON DATABASE mydb TO safesql_user;

-- 授予 schema 使用权限
GRANT USAGE ON SCHEMA public TO safesql_user;

-- 授予所有表的 SELECT 权限
GRANT SELECT ON ALL TABLES IN SCHEMA public TO safesql_user;

-- 设置默认权限（新表自动授予 SELECT）
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO safesql_user;
```

**MySQL**：
```sql
-- 创建只读用户
CREATE USER 'safesql_user'@'%' IDENTIFIED BY 'secure_password';

-- 授予 SELECT 权限
GRANT SELECT ON mydb.* TO 'safesql_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 3. 使用环境变量

**❌ 不推荐**：
```yaml
databases:
  prod_db:
    password: plain_password
```

**✅ 推荐**：
```yaml
databases:
  prod_db:
    password: ${DB_PASSWORD}
```

**设置环境变量**：
```bash
# Linux/macOS
export DB_PASSWORD="secure_password"

# 或使用 .env 文件
echo "DB_PASSWORD=secure_password" >> .env

# Docker
docker run -e DB_PASSWORD="secure_password" ...
```

### 4. 启用 SSL 连接

**PostgreSQL**：
```yaml
databases:
  prod_db:
    options:
      sslmode: require
      sslcert: /path/to/client-cert.pem
      sslkey: /path/to/client-key.pem
      sslrootcert: /path/to/ca-cert.pem
```

**MySQL**：
```yaml
databases:
  prod_db:
    options:
      ssl:
        ca: /path/to/ca-cert.pem
        cert: /path/to/client-cert.pem
        key: /path/to/client-key.pem
```

---

## 🛡️ 风险规则配置

### 1. 生产环境严格模式

```yaml
risk_rules:
  # 阻止所有写操作
  high_risk:
    - name: block_all_writes
      pattern: '(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\s+'
      message: '生产环境禁止写操作'
      enabled: true
    
    - name: block_system_tables
      pattern: '(information_schema|pg_catalog|mysql\.|sys\.)'
      message: '禁止访问系统表'
      enabled: true
  
  # 警告性能问题
  medium_risk:
    - name: select_star
      pattern: 'SELECT\s+\*\s+FROM'
      message: '建议明确指定列名'
      enabled: true
    
    - name: missing_limit
      pattern: 'SELECT\s+.*(?<!LIMIT\s+\d+)$'
      message: '建议添加 LIMIT 限制结果集'
      enabled: true
  
  # 允许健康检查
  whitelist:
    - name: health_check
      pattern: 'SELECT\s+1'
      message: '健康检查查询'
      enabled: true
```

### 2. 开发环境宽松模式

```yaml
risk_rules:
  # 允许大部分操作
  high_risk:
    - name: block_drop_database
      pattern: 'DROP\s+DATABASE'
      message: '禁止删除数据库'
      enabled: true
  
  # 使用默认规则
  medium_risk: []
  low_risk: []
  whitelist: []
```

### 3. 分级配置

```yaml
# 开发环境
risk_rules: {}  # 使用默认规则

# 测试环境
risk_rules:
  high_risk:
    - name: block_writes
      pattern: '(INSERT|UPDATE|DELETE|DROP)\s+'
      message: '测试环境禁止写操作'

# 生产环境
risk_rules:
  high_risk:
    - name: block_all_modifications
      pattern: '(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\s+'
      message: '生产环境禁止修改操作'
```

---

## 📊 监控和日志

### 1. 配置日志级别

```yaml
logging:
  level: INFO  # 生产环境使用 INFO 或 WARNING
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: /var/log/safesql/safesql.log
```

### 2. 日志轮转

使用 logrotate 配置日志轮转：

```bash
# /etc/logrotate.d/safesql
/var/log/safesql/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 safesql safesql
    sharedscripts
    postrotate
        systemctl reload safesql || true
    endscript
}
```

### 3. 关键指标监控

```python
# 记录关键指标
import logging

logger = logging.getLogger("safesql")

def log_query(sql: str, risk_level: str, execution_time: float):
    """记录查询日志"""
    logger.info(
        f"Query executed: sql={sql[:50]}... "
        f"risk={risk_level} "
        f"time={execution_time:.3f}s"
    )

def log_high_risk_blocked(sql: str, rule: str):
    """记录高风险拦截"""
    logger.warning(
        f"High risk query blocked: sql={sql[:50]}... "
        f"rule={rule}"
    )

def log_error(sql: str, error: str):
    """记录查询错误"""
    logger.error(
        f"Query failed: sql={sql[:50]}... "
        f"error={error}"
    )
```

### 4. 集成监控系统

```yaml
# Prometheus 指标
metrics:
  enabled: true
  port: 9090
  path: /metrics

# 自定义指标
- safesql_queries_total{risk_level="high"}
- safesql_queries_total{risk_level="medium"}
- safesql_queries_blocked_total
- safesql_query_duration_seconds
```

---

## 🚀 部署建议

### 1. Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建非 root 用户
RUN useradd -m -s /bin/bash safesql
USER safesql

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["safesql-mcp", "--config", "/app/safesql.yaml"]
```

**docker-compose.yml**：
```yaml
version: '3.8'

services:
  safesql:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_PASSWORD=${DB_PASSWORD}
    volumes:
      - ./safesql.yaml:/app/safesql.yaml:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "safesql-review", "--test-connection"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 2. Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: safesql
spec:
  replicas: 2
  selector:
    matchLabels:
      app: safesql
  template:
    metadata:
      labels:
        app: safesql
    spec:
      containers:
      - name: safesql
        image: safesql-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        livenessProbe:
          exec:
            command:
            - safesql-review
            - --test-connection
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - safesql-review
            - --test-connection
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: safesql
spec:
  selector:
    app: safesql
  ports:
  - port: 8000
    targetPort: 8000
```

### 3. Systemd 服务

```ini
# /etc/systemd/system/safesql.service
[Unit]
Description=SafeSQL MCP Server
After=network.target

[Service]
Type=simple
User=safesql
Group=safesql
WorkingDirectory=/opt/safesql
Environment="DB_PASSWORD=secure_password"
ExecStart=/opt/safesql/venv/bin/safesql-mcp --config /opt/safesql/safesql.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl enable safesql
sudo systemctl start safesql

# 查看状态
sudo systemctl status safesql

# 查看日志
sudo journalctl -u safesql -f
```

---

## 🔒 安全建议

### 1. 网络安全

```yaml
# 只允许内网访问
databases:
  prod_db:
    host: 10.0.0.100  # 内网 IP
    options:
      sslmode: require
```

### 2. 密钥管理

```bash
# 使用 HashiCorp Vault
export DB_PASSWORD=$(vault kv get -field=password secret/safesql/db)

# 使用 AWS Secrets Manager
export DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id safesql/db --query SecretString --output text)
```

### 3. 审计日志

```yaml
logging:
  level: INFO
  format: "%(asctime)s %(levelname)s %(message)s"
  file: /var/log/safesql/audit.log

# 记录所有查询
audit:
  enabled: true
  log_all_queries: true
  log_risk_assessments: true
```

---

## 🧪 测试策略

### 1. 单元测试

```python
# tests/test_risk_engine.py
def test_high_risk_blocked():
    engine = RiskEngine()
    assessment = engine.assess_sql("DROP TABLE users")
    assert assessment.risk_level == RiskLevel.HIGH
    assert assessment.is_executable is False
```

### 2. 集成测试

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_query_execution():
    db = PostgreSQLDatabase(config)
    await db.connect()
    
    result = await db.execute("SELECT 1")
    assert result.row_count == 1
    
    await db.disconnect()
```

### 3. 端到端测试

```bash
# 测试完整流程
safesql-review --sql "SELECT * FROM users" --format json | jq '.risk_level'
# 应该输出: "medium"
```

### 4. 性能测试

```python
# tests/test_performance.py
def test_query_latency():
    engine = RiskEngine()
    
    start = time.time()
    for _ in range(1000):
        engine.assess_sql("SELECT * FROM users WHERE id = 1")
    elapsed = time.time() - start
    
    assert elapsed < 1.0  # 1000 次评估应该在 1 秒内完成
```

---

## 📚 相关文档

- [配置文件参考](../api/config-reference.md) - 完整配置说明
- [架构设计](../architecture.md) - 系统架构详解
- [故障排除](troubleshooting.md) - 常见问题解答