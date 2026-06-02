"""
SafeSQL MCP Server 主入口
"""

import asyncio
import sys
from typing import Dict, Optional

import click
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .core.engine import RiskEngine
from .core.rules import DefaultRiskRules
from .databases.base import DatabaseBase
from .databases.postgresql import PostgreSQLDatabase
from .databases.mysql import MySQLDatabase
from .mcp.tools import SafeSQLTools
from .mcp.resources import SafeSQLResources
from .utils.config import Config, load_config, create_default_config
from .utils.logger import setup_logger, get_logger


class SafeSQLServer:
    """SafeSQL MCP Server"""
    
    def __init__(self, config: Config):
        """
        初始化服务器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = setup_logger(
            level=config.logging.get("level", "INFO"),
            log_format=config.logging.get("format"),
            log_file=config.logging.get("file")
        )
        
        # 初始化风险引擎
        if config.risk_rules:
            self.risk_engine = RiskEngine(custom_rules=config.risk_rules)
        else:
            self.risk_engine = RiskEngine()
        
        # 初始化数据库连接
        self.databases: Dict[str, DatabaseBase] = {}
        self._init_databases()
        
        # 创建 MCP Server
        self.server = Server(config.mcp_server.get("name", "safesql"))
        
        # 初始化工具和资源
        self.tools = SafeSQLTools(self.server, self.risk_engine, self.databases)
        self.resources = SafeSQLResources(self.server, self.databases)
        
        self.logger.info(f"SafeSQL MCP Server initialized with {len(self.databases)} databases")
    
    def _init_databases(self) -> None:
        """初始化数据库连接"""
        for name, db_config in self.config.databases.items():
            try:
                if db_config.type == "postgresql":
                    db = PostgreSQLDatabase(db_config)
                elif db_config.type == "mysql":
                    db = MySQLDatabase(db_config)
                else:
                    self.logger.warning(f"Unsupported database type: {db_config.type}")
                    continue
                
                self.databases[name] = db
                self.logger.info(f"Database '{name}' ({db_config.type}) initialized")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize database '{name}': {e}")
    
    async def run(self) -> None:
        """运行 MCP Server"""
        self.logger.info("Starting SafeSQL MCP Server...")
        
        # 测试数据库连接
        for name, db in self.databases.items():
            try:
                connected = await db.test_connection()
                if connected:
                    self.logger.info(f"Database '{name}' connection test passed")
                else:
                    self.logger.warning(f"Database '{name}' connection test failed")
            except Exception as e:
                self.logger.error(f"Database '{name}' connection test error: {e}")
        
        # 运行 MCP Server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
    
    async def stop(self) -> None:
        """停止服务器"""
        self.logger.info("Stopping SafeSQL MCP Server...")
        
        # 关闭数据库连接
        for name, db in self.databases.items():
            try:
                await db.disconnect()
                self.logger.info(f"Database '{name}' disconnected")
            except Exception as e:
                self.logger.error(f"Error disconnecting database '{name}': {e}")
        
        self.logger.info("SafeSQL MCP Server stopped")


@click.command()
@click.option("--config", "-c", "config_path", help="配置文件路径")
@click.option("--init", is_flag=True, help="创建默认配置文件")
@click.option("--port", type=int, help="HTTP 端口（默认使用 stdio）")
@click.option("--host", default="localhost", help="HTTP 主机地址")
def main(config_path: Optional[str], init: bool, port: Optional[int], host: str):
    """SafeSQL MCP Server - 安全数据库访问"""
    
    # 创建默认配置文件
    if init:
        if config_path is None:
            config_path = "safesql.yaml"
        create_default_config(config_path)
        click.echo(f"Default configuration created: {config_path}")
        return
    
    # 加载配置
    try:
        config = load_config(config_path)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # 创建服务器
    server = SafeSQLServer(config)
    
    # 运行服务器
    try:
        if port:
            # HTTP 模式
            import uvicorn
            from mcp.server.fastmcp import FastMCP
            
            # 创建 FastMCP 应用
            app = FastMCP(
                config.mcp_server.get("name", "safesql"),
                version=config.mcp_server.get("version", "1.0.0")
            )
            
            # 注册工具和资源
            # 注意：这里简化处理，实际需要适配 FastMCP 接口
            
            click.echo(f"Starting HTTP server on {host}:{port}")
            uvicorn.run(app, host=host, port=port)
        else:
            # stdio 模式
            asyncio.run(server.run())
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        asyncio.run(server.stop())


@click.group()
def cli():
    """SafeSQL CLI 工具"""
    pass


@cli.command()
@click.argument("sql")
@click.option("--config", "-c", "config_path", help="配置文件路径")
def validate(sql: str, config_path: Optional[str]):
    """验证 SQL 语句的风险等级"""
    # 加载配置
    config = load_config(config_path)
    
    # 创建风险引擎
    if config.risk_rules:
        engine = RiskEngine(custom_rules=config.risk_rules)
    else:
        engine = RiskEngine()
    
    # 评估 SQL
    assessment = engine.assess_sql(sql)
    
    # 输出结果
    click.echo(f"SQL: {sql}")
    click.echo(f"Risk Level: {assessment.risk_level.value}")
    click.echo(f"Message: {assessment.message}")
    click.echo(f"Executable: {assessment.is_executable}")
    
    if assessment.suggestions:
        click.echo("Suggestions:")
        for suggestion in assessment.suggestions:
            click.echo(f"  - {suggestion}")


@cli.command()
@click.argument("directory", default=".")
@click.option("--config", "-c", "config_path", help="配置文件路径")
@click.option("--github-pr", is_flag=True, help="GitHub PR 模式")
@click.option("--fail-on-high-risk", is_flag=True, help="高风险时失败")
def review(directory: str, config_path: Optional[str], github_pr: bool, fail_on_high_risk: bool):
    """审查目录中的 SQL 文件"""
    import os
    import glob
    
    # 加载配置
    config = load_config(config_path)
    
    # 创建风险引擎
    if config.risk_rules:
        engine = RiskEngine(custom_rules=config.risk_rules)
    else:
        engine = RiskEngine()
    
    # 查找 SQL 文件
    sql_files = glob.glob(os.path.join(directory, "**/*.sql"), recursive=True)
    
    if not sql_files:
        click.echo("No SQL files found")
        return
    
    click.echo(f"Found {len(sql_files)} SQL files")
    
    # 审查每个文件
    high_risk_count = 0
    medium_risk_count = 0
    
    for sql_file in sql_files:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 简单分割 SQL 语句
        sql_statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        for sql in sql_statements:
            assessment = engine.assess_sql(sql)
            
            if assessment.risk_level.value == "high":
                click.echo(f"🔴 HIGH RISK in {sql_file}: {assessment.message}")
                click.echo(f"   SQL: {sql[:100]}...")
                high_risk_count += 1
            elif assessment.risk_level.value == "medium":
                click.echo(f"🟡 MEDIUM RISK in {sql_file}: {assessment.message}")
                medium_risk_count += 1
    
    # 输出统计
    click.echo(f"\nReview Summary:")
    click.echo(f"  Files reviewed: {len(sql_files)}")
    click.echo(f"  High risk: {high_risk_count}")
    click.echo(f"  Medium risk: {medium_risk_count}")
    
    # GitHub PR 模式
    if github_pr and high_risk_count > 0:
        click.echo("\n⚠️  High risk SQL detected in PR!")
        if fail_on_high_risk:
            sys.exit(1)


if __name__ == "__main__":
    main()