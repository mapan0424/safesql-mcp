# Contributing to SafeSQL MCP

感谢您对 SafeSQL MCP 项目的关注！我们欢迎各种形式的贡献。

## 🚀 快速开始

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/safesql-mcp.git
cd safesql-mcp
```

### 2. 设置开发环境

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 3. 运行测试

```bash
pytest tests/
```

## 📋 贡献类型

### 🐛 Bug 报告
- 使用 GitHub Issues 报告 bug
- 提供复现步骤、预期行为和实际行为

### ✨ 功能建议
- 使用 GitHub Issues 提出新功能
- 说明使用场景和预期收益

### 🔧 代码贡献
- Fork 项目并创建特性分支
- 编写代码和测试
- 提交 PR 并描述变更

### 📖 文档改进
- 修正错误或改进文档
- 添加使用示例

## 📝 开发规范

### 代码风格
- 使用 Black 格式化代码
- 使用 isort 排序导入
- 遵循 PEP 8 规范

### 提交规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 分支命名
- `feature/xxx`: 新功能
- `fix/xxx`: Bug 修复
- `docs/xxx`: 文档更新

## 🧪 测试

### 单元测试
```bash
pytest tests/unit/
```

### 集成测试
```bash
pytest tests/integration/
```

### 覆盖率
```bash
pytest --cov=safesql_mcp --cov-report=html
```

## 📦 发布

### 版本号
遵循 [Semantic Versioning](https://semver.org/):
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的 Bug 修复

### 发布流程
1. 更新 `CHANGELOG.md`
2. 更新 `pyproject.toml` 中的版本号
3. 创建 Git tag
4. 推送到 GitHub
5. GitHub Actions 自动发布到 PyPI

## 📜 许可证

贡献即表示您同意您的代码将以 MIT 许可证发布。

## 🙏 致谢

感谢所有为 SafeSQL MCP 做出贡献的人！