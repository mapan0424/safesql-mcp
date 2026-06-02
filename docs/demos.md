# Integration Demos

Real-world examples of how to connect SafeSQL MCP with popular AI coding tools.

## 📋 Table of Contents

- [Claude Desktop](#claude-desktop)
- [Cursor](#cursor)
- [Codex CLI](#codex-cli)
- [Continue.dev](#continuedev)
- [Cline (VS Code)](#cline-vs-code)

---

## Claude Desktop

[Claude Desktop](https://claude.ai/download) natively supports MCP servers.

### Configuration

1. **Locate the config file**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Add SafeSQL MCP configuration**:

```json
{
  "mcpServers": {
    "safesql": {
      "command": "safesql-mcp",
      "args": ["--config", "/path/to/safesql.yaml"],
      "env": {
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

### Usage Examples

Once configured, you can ask Claude to query your database:

```
You: Show me all active users in the database

Claude: I'll query the database for active users.

[Uses query tool: SELECT id, name, email FROM users WHERE status = 'active']

Here are the active users:
| id | name     | email              |
|----|----------|--------------------|
| 1  | John Doe | john@example.com   |
| 2  | Jane Doe | jane@example.com   |
```

```
You: Delete all inactive users

Claude: I'll check if this operation is safe.

[Uses validate tool: DELETE FROM users WHERE status = 'inactive']

⚠️ This query has been flagged as medium risk because it could affect multiple rows. 
Would you like me to proceed, or would you prefer to add more specific conditions?
```

---

## Cursor

[Cursor](https://cursor.sh) supports MCP through its settings.

### Configuration

1. **Open Cursor Settings**:
   - Go to `Cursor` → `Preferences` → `Settings`
   - Or press `Cmd + ,` (macOS) / `Ctrl + ,` (Windows/Linux)

2. **Search for "MCP"** and add configuration:

```json
{
  "mcpServers": {
    "safesql": {
      "command": "safesql-mcp",
      "args": ["--config", "/path/to/safesql.yaml"]
    }
  }
}
```

3. **Alternative**: Edit `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "safesql": {
      "command": "safesql-mcp",
      "args": ["--config", "./safesql.yaml"],
      "env": {
        "DB_PASSWORD": "${env:DB_PASSWORD}"
      }
    }
  }
}
```

### Usage Examples

In Cursor's AI chat:

```
@cursor What's the schema of the orders table?

[Uses schema tool to fetch table structure]

The orders table has the following columns:
- id (INTEGER, PRIMARY KEY)
- user_id (INTEGER, FOREIGN KEY → users.id)
- product_id (INTEGER, FOREIGN KEY → products.id)
- quantity (INTEGER)
- total (DECIMAL)
- created_at (TIMESTAMP)
```

---

## Codex CLI

[OpenAI Codex CLI](https://github.com/openai/codex) can be configured to use MCP servers.

### Configuration

1. **Create or edit** `~/.codex/config.json`:

```json
{
  "mcpServers": {
    "safesql": {
      "command": "safesql-mcp",
      "args": ["--config", "/path/to/safesql.yaml"]
    }
  }
}
```

2. **Or use environment variables**:

```bash
export CODEX_MCP_SERVERS='{"safesql":{"command":"safesql-mcp","args":["--config","safesql.yaml"]}}'
```

### Usage Examples

```bash
$ codex "Query the database for the top 10 customers by order value"

# Codex will use SafeSQL MCP to:
# 1. Validate the SQL query
# 2. Execute it safely
# 3. Return formatted results
```

---

## Continue.dev

[Continue.dev](https://continue.dev) supports MCP servers in VS Code and JetBrains.

### Configuration

1. **Edit** `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "safesql",
      "command": "safesql-mcp",
      "args": ["--config", "/path/to/safesql.yaml"]
    }
  ]
}
```

2. **Or in VS Code settings**:

```json
{
  "continue.mcpServers": [
    {
      "name": "safesql",
      "command": "safesql-mcp",
      "args": ["--config", "./safesql.yaml"]
    }
  ]
}
```

### Usage Examples

In Continue's chat:

```
> Show me the database schema

[Uses schema tool]

> Write a query to find users who haven't ordered in 30 days

[Uses validate tool to check query safety]
[Uses query tool to execute]

Here's the query result:
...
```

---

## Cline (VS Code)

[Cline](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev) is a VS Code extension that supports MCP.

### Configuration

1. **Open VS Code Settings**:
   - Press `Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"

2. **Add MCP configuration**:

```json
{
  "cline.mcpServers": {
    "safesql": {
      "command": "safesql-mcp",
      "args": ["--config", "/path/to/safesql.yaml"]
    }
  }
}
```

3. **Or use Cline's UI**:
   - Click the Cline icon in the sidebar
   - Go to "MCP Servers" tab
   - Add new server with command: `safesql-mcp --config /path/to/safesql.yaml`

### Usage Examples

```
Cline: What tables are in the database?

[Uses databases tool to list tables]

The database contains the following tables:
- users
- orders
- products
- categories
- reviews

Cline: Can you show me the structure of the users table?

[Uses schema tool with table parameter]

The users table has these columns:
- id (INTEGER, NOT NULL, PRIMARY KEY)
- name (VARCHAR(255), NOT NULL)
- email (VARCHAR(255), UNIQUE)
- status (VARCHAR(50), DEFAULT 'active')
- created_at (TIMESTAMP, DEFAULT NOW())
```

---

## Docker Configuration

For containerized environments:

### docker-compose.yml

```yaml
version: '3.8'

services:
  safesql:
    image: safesql-mcp:latest
    volumes:
      - ./safesql.yaml:/app/safesql.yaml:ro
    environment:
      - DB_PASSWORD=${DB_PASSWORD}
    ports:
      - "8000:8000"
    restart: unless-stopped

  # Your AI tool connects to localhost:8000
```

### Claude Desktop with Docker

```json
{
  "mcpServers": {
    "safesql": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/path/to/safesql.yaml:/app/safesql.yaml:ro",
        "-e", "DB_PASSWORD=your_password",
        "safesql-mcp",
        "--config", "/app/safesql.yaml"
      ]
    }
  }
}
```

---

## Troubleshooting

### Common Issues

#### 1. "Command not found: safesql-mcp"

**Solution**: Make sure SafeSQL MCP is installed and in your PATH:

```bash
# Install
pip install safesql-mcp

# Verify installation
which safesql-mcp

# Or use full path in config
{
  "command": "/usr/local/bin/safesql-mcp",
  "args": [...]
}
```

#### 2. "Connection refused"

**Solution**: Check your database connection:

```bash
# Test connection
safesql-review --config safesql.yaml --test-connection

# Verify database is running
pg_isready  # PostgreSQL
mysqladmin ping  # MySQL
```

#### 3. "Permission denied"

**Solution**: Check file permissions:

```bash
# Fix permissions
chmod 600 safesql.yaml
chmod +x $(which safesql-mcp)
```

#### 4. "Module not found: oracledb"

**Solution**: Install Oracle dependencies:

```bash
pip install safesql-mcp[oracle]
```

---

## Best Practices

1. **Use read-only database users** for all connections
2. **Store passwords in environment variables**, not in config files
3. **Enable SSL/TLS** for production database connections
4. **Regularly update** SafeSQL MCP to get security patches
5. **Test risk rules** before deploying to production
6. **Monitor logs** for suspicious queries

---

## Need Help?

- 📖 [Documentation](docs/)
- 🐛 [Report Issues](https://github.com/mapan0424/safesql-mcp/issues)
- 💬 [Discussions](https://github.com/mapan0424/safesql-mcp/discussions)