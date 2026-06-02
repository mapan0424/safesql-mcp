# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | ✅ Yes             |
| 1.0.x   | ✅ Yes             |
| < 1.0   | ❌ No              |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in SafeSQL MCP, please report it responsibly.

### How to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:

📧 **315337987@qq.com**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- **Type of vulnerability** (e.g., SQL injection, authentication bypass, etc.)
- **Full paths of source file(s)** related to the vulnerability
- **The location of the affected source code** (tag/branch/commit or direct URL)
- **Any special configuration** required to reproduce the issue
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact** of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours.
- **Assessment**: We will assess the vulnerability and determine its impact.
- **Fix**: We will work on a fix and release it as soon as possible.
- **Disclosure**: We will coordinate with you on the timing of public disclosure.
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous).

## Security Considerations

### Database Access

SafeSQL MCP is designed to provide **read-only** access to databases by default. However, users should:

1. **Use dedicated read-only database users** for SafeSQL MCP connections
2. **Never use administrative credentials** in configuration files
3. **Use environment variables** for sensitive configuration (passwords, tokens)
4. **Enable SSL/TLS** for database connections in production

### SQL Risk Audit

The SQL risk audit engine is designed to block dangerous operations, but:

1. **No security system is 100% foolproof** - always follow the principle of least privilege
2. **Regular expression patterns** may have edge cases - report any bypasses you find
3. **Custom rules** should be thoroughly tested before deployment
4. **Default rules** are designed for common cases - customize for your specific needs

### Configuration Security

1. **Never commit configuration files** with real credentials to version control
2. **Use `.gitignore`** to exclude sensitive files
3. **Use environment variables** or secret management tools for production
4. **Restrict file permissions** on configuration files (e.g., `chmod 600 safesql.yaml`)

### Network Security

1. **Use internal network addresses** for database connections when possible
2. **Enable firewall rules** to restrict access to database ports
3. **Use VPN or SSH tunneling** for remote database access
4. **Enable SSL/TLS** for all database connections

## Security Best Practices

### For Users

```bash
# 1. Use read-only database user
CREATE USER 'safesql_readonly'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT ON mydb.* TO 'safesql_readonly'@'%';

# 2. Use environment variables
export DB_PASSWORD="strong_password"

# 3. Set restrictive file permissions
chmod 600 safesql.yaml

# 4. Enable SSL in configuration
# In safesql.yaml:
# options:
#   sslmode: require
```

### For Developers

```python
# 1. Use parameterized queries (already implemented)
# 2. Validate all inputs
# 3. Follow principle of least privilege
# 4. Regular security audits
# 5. Keep dependencies updated
```

## Known Limitations

1. **SQL Pattern Matching**: The risk audit engine uses regular expressions, which may not catch all edge cases. We recommend combining SafeSQL MCP with other security measures.

2. **Database-Specific Syntax**: Some database-specific SQL syntax may not be fully covered. Please report any gaps you find.

3. **Performance**: Complex SQL analysis may impact performance for high-throughput applications. Consider using caching for frequently executed queries.

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.1, 1.0.2) and will be clearly marked in the [CHANGELOG](CHANGELOG.md).

Subscribe to our [GitHub Releases](https://github.com/mapan0424/safesql-mcp/releases) to receive notifications about security updates.

## Responsible Disclosure

We kindly ask that you:

1. **Give us reasonable time** to address the issue before public disclosure
2. **Avoid exploiting the vulnerability** beyond what is necessary to demonstrate it
3. **Do not access or modify data** belonging to other users
4. **Act in good faith** to avoid privacy violations and disruption of services

## Recognition

We would like to thank the following security researchers for their responsible disclosures:

- (No reports yet - be the first!)

## Contact

- **Security Contact**: 315337987@qq.com
- **GitHub Issues**: [For non-security bugs only](https://github.com/mapan0424/safesql-mcp/issues)
- **Documentation**: [docs/](docs/)

---

Thank you for helping keep SafeSQL MCP and its users safe! 🔒