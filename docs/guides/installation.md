# 安装指南

详细的 SafeSQL MCP 安装说明。

## 📋 系统要求

- **Python**: 3.10 或更高版本
- **操作系统**: Linux, macOS, Windows
- **数据库**: PostgreSQL 12+ 或 MySQL 5.7+

## 🐍 Python 环境准备

### 检查 Python 版本

```bash
python3 --version
# 输出应为 Python 3.10.x 或更高
```

### 安装 Python（如果需要）

**macOS (使用 Homebrew)**:
```bash
brew install python@3.11
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**Windows**:
从 https://www.python.org/downloads/ 下载安装包

## 📦 安装 SafeSQL MCP

### 方式一：pip 安装（推荐）

```bash
# 创建虚拟环境（推荐）
python3 -m venv safesql-env
source safesql-env/bin/activate  # Linux/macOS
# safesql-env\Scripts\activate   # Windows

# 安装
pip install safesql-mcp
```

### 方式二：从源码安装

```bash
# 克隆仓库
git clone https://github.com/mapan0424/safesql-mcp.git
cd safesql-mcp

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装（开发模式）
pip install -e ".[dev]"
```

### 方式三：使用 uv（更快）

```bash
# 安装 uv
pip install uv

# 创建虚拟环境并安装
uv venv
source .venv/bin/activate
uv pip install safesql-mcp
```

## ✅ 验证安装

### 检查命令行工具

```bash
# 检查 safesql-mcp 命令
safesql-mcp --version

# 检查 safesql-review 命令
safesql-review --help
```

### 检查 Python 模块

```python
python3 -c "import safesql_mcp; print(safesql_mcp.__version__)"
```

### 运行测试

```bash
# 如果从源码安装
cd safesql-mcp
pytest tests/ -v
```

## 🗄️ 数据库驱动安装

SafeSQL MCP 需要数据库驱动。根据您的数据库类型安装：

### PostgreSQL

```bash
# psycopg2-binary 已包含在依赖中
# 如果需要从源码编译：
pip install psycopg2
```

**系统依赖（如果编译失败）**：

```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt install libpq-dev

# CentOS/RHEL
sudo yum install postgresql-devel
```

### MySQL

```bash
# pymysql 已包含在依赖中
# 如果需要 mysqlclient：
pip install mysqlclient
```

**系统依赖（如果编译失败）**：

```bash
# macOS
brew install mysql-client

# Ubuntu/Debian
sudo apt install libmysqlclient-dev

# CentOS/RHEL
sudo yum install mysql-devel
```

## 🔧 开发环境设置

如果您想参与开发或修改代码：

```bash
# 克隆仓库
git clone https://github.com/mapan0424/safesql-mcp.git
cd safesql-mcp

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit hooks
pre-commit install

# 运行代码格式化
black src/ tests/
isort src/ tests/

# 运行类型检查
mypy src/

# 运行测试
pytest tests/ -v --cov=safesql_mcp
```

## 🐳 Docker 安装（可选）

如果不想安装 Python 环境，可以使用 Docker：

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install -e .

EXPOSE 8000

CMD ["safesql-mcp", "--config", "/app/safesql.yaml"]
```

构建和运行：

```bash
# 构建镜像
docker build -t safesql-mcp .

# 运行容器
docker run -d \
  --name safesql \
  -p 8000:8000 \
  -v $(pwd)/safesql.yaml:/app/safesql.yaml \
  safesql-mcp
```

## 🔍 故障排除

### 问题：`ModuleNotFoundError: No module named 'safesql_mcp'`

**解决方案**：
```bash
# 确保在正确的虚拟环境中
source venv/bin/activate

# 重新安装
pip install -e .
```

### 问题：`psycopg2.OperationalError: could not connect to server`

**解决方案**：
1. 检查数据库是否运行
2. 检查连接参数（host, port, user, password）
3. 检查防火墙设置
4. 检查数据库用户权限

### 问题：`Permission denied` 错误

**解决方案**：
```bash
# 使用 --user 标志
pip install --user safesql-mcp

# 或使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip install safesql-mcp
```

### 问题：Python 版本过低

**解决方案**：
```bash
# 使用 pyenv 安装新版本
pyenv install 3.11.0
pyenv local 3.11.0

# 或使用系统包管理器
brew install python@3.11  # macOS
sudo apt install python3.11  # Ubuntu
```

## 📚 下一步

安装完成后，继续阅读：

- [快速开始指南](quickstart.md) - 5 分钟上手
- [基础使用](basic-usage.md) - 详细使用教程
- [配置指南](risk-rules.md) - 自定义配置

## 💬 获取帮助

遇到问题？

1. 查看 [常见问题](#-故障排除)
2. 搜索 [GitHub Issues](https://github.com/mapan0424/safesql-mcp/issues)
3. 提交新 Issue