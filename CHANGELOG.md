# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-06-03

### Added
- 🚀 **Connection Pool Optimization** - Advanced connection pool with configurable parameters
  - Min/max pool size configuration
  - Connection idle timeout and max lifetime
  - Automatic connection validation and retry
  - Pool statistics and monitoring
- ⚡ **Async Database Drivers** - True async database support for better performance
  - `asyncpg` for PostgreSQL async operations
  - `aiomysql` for MySQL async operations
  - Async connection pool management
  - Non-blocking database operations
- 💾 **Query Caching** - Intelligent query result caching
  - TTL-based cache expiration
  - Configurable cache size
  - Cache hit/miss statistics
  - Automatic cache invalidation for write operations
- 🛡️ **SQL Injection Detection** - Advanced SQL injection pattern detection
  - 14+ injection pattern categories
  - Risk level assessment (None/Low/Medium/High/Critical)
  - Configurable detection rules
  - Integration with risk assessment engine
- 🔧 **Enhanced Rule Engine** - More powerful and flexible rule system
  - Rule priority and categories
  - Rule groups and tags
  - Dynamic rule support
  - Rule conflict detection
  - Hot rule updates
- 🚨 **Comprehensive Error Handling** - Structured error handling system
  - Custom error types with error codes
  - Error context and details
  - Error handler registration
  - Decorator-based error handling
- 📊 **Structured Logging** - Enhanced logging capabilities
  - JSON-formatted log output
  - Structured log data with extra fields
  - Query execution logging
  - Connection event logging
  - Risk assessment logging

### Changed
- 🔄 **Database Driver Architecture** - Refactored database drivers for better extensibility
  - Separate sync and async driver implementations
  - Unified driver interface
  - Driver selection via configuration
- 📈 **Performance Monitoring** - Added performance metrics and statistics
  - Cache hit rate monitoring
  - Connection pool utilization
  - Query execution time tracking
  - Risk rule match statistics
- 📝 **Configuration Enhancement** - Extended configuration options
  - Performance tuning section
  - Cache configuration
  - Async driver configuration
  - Connection pool parameters

### Fixed
- 🐛 **Connection Management** - Improved connection lifecycle management
  - Proper connection cleanup on errors
  - Connection leak prevention
  - Graceful shutdown handling
- 🔒 **Security Improvements** - Enhanced security measures
  - Better input validation
  - Parameterized query enforcement
  - Injection pattern detection

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