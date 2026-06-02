"""
SafeSQL CLI 工具
"""

import click
import sys
from typing import Optional

from .utils.config import load_config, create_default_config
from .core.engine import RiskEngine


@click.group()
def cli():
    """SafeSQL CLI 工具 - SQL 风险审查"""
    pass


@cli.command()
@click.argument("sql")
@click.option("--config", "-c", "config_path", help="配置文件路径")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="输出格式")
def validate(sql: str, config_path: Optional[str], output: str):
    """验证 SQL 语句的风险等级"""
    # 加载配置
    try:
        config = load_config(config_path)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # 创建风险引擎
    if config.risk_rules:
        engine = RiskEngine(custom_rules=config.risk_rules)
    else:
        engine = RiskEngine()
    
    # 评估 SQL
    assessment = engine.assess_sql(sql)
    
    # 输出结果
    if output == "json":
        import json
        click.echo(json.dumps(assessment.to_dict(), indent=2, ensure_ascii=False))
    else:
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
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("--github-pr", is_flag=True, help="GitHub PR 模式")
@click.option("--fail-on-high-risk", is_flag=True, help="高风险时失败")
def review(directory: str, config_path: Optional[str], output: str, github_pr: bool, fail_on_high_risk: bool):
    """审查目录中的 SQL 文件"""
    import os
    import glob
    
    # 加载配置
    try:
        config = load_config(config_path)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
    
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
    
    # 审查每个文件
    results = []
    high_risk_count = 0
    medium_risk_count = 0
    
    for sql_file in sql_files:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 简单分割 SQL 语句
        sql_statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        file_results = []
        for sql in sql_statements:
            assessment = engine.assess_sql(sql)
            file_results.append({
                "sql": sql,
                "assessment": assessment.to_dict()
            })
            
            if assessment.risk_level.value == "high":
                high_risk_count += 1
            elif assessment.risk_level.value == "medium":
                medium_risk_count += 1
        
        results.append({
            "file": sql_file,
            "statements": file_results
        })
    
    # 输出结果
    if output == "json":
        import json
        summary = {
            "files_reviewed": len(sql_files),
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "results": results
        }
        click.echo(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        click.echo(f"Found {len(sql_files)} SQL files")
        
        for result in results:
            click.echo(f"\n📄 {result['file']}")
            for stmt in result["statements"]:
                assessment = stmt["assessment"]
                if assessment["risk_level"] == "high":
                    click.echo(f"  🔴 HIGH: {assessment['message']}")
                    click.echo(f"     SQL: {stmt['sql'][:100]}...")
                elif assessment["risk_level"] == "medium":
                    click.echo(f"  🟡 MEDIUM: {assessment['message']}")
        
        click.echo(f"\nReview Summary:")
        click.echo(f"  Files reviewed: {len(sql_files)}")
        click.echo(f"  High risk: {high_risk_count}")
        click.echo(f"  Medium risk: {medium_risk_count}")
    
    # GitHub PR 模式
    if github_pr and high_risk_count > 0:
        click.echo("\n⚠️  High risk SQL detected in PR!")
        if fail_on_high_risk:
            sys.exit(1)


@cli.command()
@click.option("--config", "-c", "config_path", help="配置文件路径")
@click.option("--output", "-o", type=click.Choice(["yaml", "json"]), default="yaml", help="输出格式")
def rules(config_path: Optional[str], output: str):
    """显示当前配置的风险规则"""
    # 加载配置
    try:
        config = load_config(config_path)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # 创建风险引擎
    if config.risk_rules:
        engine = RiskEngine(custom_rules=config.risk_rules)
    else:
        engine = RiskEngine()
    
    # 输出规则
    if output == "json":
        click.echo(engine.export_rules("json"))
    else:
        click.echo(engine.export_rules("yaml"))


@cli.command()
@click.argument("config_path", default="safesql.yaml")
def init(config_path: str):
    """创建默认配置文件"""
    try:
        create_default_config(config_path)
        click.echo(f"Default configuration created: {config_path}")
    except Exception as e:
        click.echo(f"Error creating configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config_path", default="safesql.yaml")
def check(config_path: str):
    """检查配置文件的有效性"""
    import os
    
    if not os.path.exists(config_path):
        click.echo(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        config = load_config(config_path)
        click.echo("Configuration is valid")
        
        # 显示配置摘要
        click.echo(f"\nDatabases: {len(config.databases)}")
        for name, db_config in config.databases.items():
            click.echo(f"  - {name} ({db_config.type})")
        
        click.echo(f"\nRisk Rules: {len(config.risk_rules)}")
        if config.risk_rules:
            engine = RiskEngine(custom_rules=config.risk_rules)
            summary = engine.get_rules_summary()
            click.echo(f"  High: {summary['by_level']['high']}")
            click.echo(f"  Medium: {summary['by_level']['medium']}")
            click.echo(f"  Low: {summary['by_level']['low']}")
            click.echo(f"  Safe: {summary['by_level']['safe']}")
        
    except Exception as e:
        click.echo(f"Invalid configuration: {e}", err=True)
        sys.exit(1)


def main():
    """CLI 入口"""
    cli()


if __name__ == "__main__":
    main()