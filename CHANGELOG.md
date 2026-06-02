# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-06-02

### Added
- 🐘 **Oracle Database Support** - Full Oracle database support with EXPLAIN plan analysis
- Oracle connection via service_name, sid, or full DSN
- Oracle-specific SQL patterns and risk rules
- Example configuration for Oracle environments

### Changed
- Updated dependencies to include `oracledb>=2.0.0`
- Updated documentation with Oracle configuration examples

## [1.0.0] - 2026-06-02

### Added
- 🛡️ **SQL Risk Audit Engine** - Three-level risk assessment (High/Medium/Low)
- 🔌 **MCP Server** - Standard Model Context Protocol server implementation
- 🐘 **PostgreSQL Support** - Full read-only query support with EXPLAIN
- 🐬 **MySQL Support** - Full read-only query support with EXPLAIN
- 🔍 **EXPLAIN Analysis** - Automatic query execution plan generation
- 🚀 **GitHub Action** - PR SQL risk review automation
- 📝 **CLI Tools** - `safesql-mcp` server and `safesql-review` auditor
- 📋 **Configurable Rules** - YAML-based risk rule configuration
- 🔗 **Connection Pool** - Database connection management

### Security
- High-risk SQL operations are automatically blocked
- Only SELECT queries are allowed by default
- Read-only database access enforced
- SQL injection prevention through parameterized queries