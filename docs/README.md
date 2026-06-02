# SafeSQL MCP 文档

欢迎阅读 SafeSQL MCP 文档！

## 📚 文档目录

### 快速开始
- [快速开始指南](guides/quickstart.md) - 5 分钟上手 SafeSQL MCP
- [安装指南](guides/installation.md) - 详细安装步骤

### 使用指南
- [基础使用](guides/basic-usage.md) - 基本查询和风险审查
- [MCP Server 配置](guides/mcp-server.md) - MCP Server 详细配置
- [数据库连接](guides/database-connection.md) - PostgreSQL/MySQL 连接配置
- [风险规则配置](guides/risk-rules.md) - 自定义风险审查规则
- [GitHub Action 集成](guides/github-action.md) - CI/CD 集成指南

### API 参考
- [MCP 工具 API](api/mcp-tools.md) - MCP 工具详细说明
- [CLI 命令参考](api/cli-reference.md) - 命令行工具使用
- [配置文件参考](api/config-reference.md) - 配置文件完整说明
- [Python API](api/python-api.md) - Python 编程接口

### 示例代码
- [基础示例](examples/basic-examples.md) - 常见使用场景
- [高级示例](examples/advanced-examples.md) - 高级用法和集成
- [最佳实践](examples/best-practices.md) - 生产环境最佳实践

### 架构设计
- [系统架构](architecture.md) - SafeSQL MCP 架构说明
- [安全模型](security-model.md) - 安全审查机制详解

## 🔗 快速链接

- **GitHub**: https://github.com/mapan0424/safesql-mcp
- **问题反馈**: https://github.com/mapan0424/safesql-mcp/issues
- **更新日志**: https://github.com/mapan0424/safesql-mcp/blob/main/CHANGELOG.md

## 📖 贡献文档

发现文档错误或有改进建议？欢迎提交 Pull Request！

```bash
# 克隆项目
git clone https://github.com/mapan0424/safesql-mcp.git

# 编辑文档
cd safesql-mcp/docs

# 提交更改
git add .
git commit -m "docs: 改进 XXX 文档"
git push origin main
```