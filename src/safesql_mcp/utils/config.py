"""
配置管理模块
"""

import os
import yaml
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..core.rules import RiskRule, RiskLevel
from ..databases.base import DatabaseConfig


@dataclass
class Config:
    """SafeSQL 配置"""
    
    # 数据库配置
    databases: Dict[str, DatabaseConfig] = field(default_factory=dict)
    
    # 风险规则配置
    risk_rules: List[RiskRule] = field(default_factory=list)
    
    # MCP Server 配置
    mcp_server: Dict[str, Any] = field(default_factory=lambda: {
        "name": "safesql",
        "version": "1.0.0",
        "description": "SafeSQL MCP Server - 安全数据库访问"
    })
    
    # EXPLAIN 配置
    explain: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "analyze": True,
        "buffers": True,
        "format": "TEXT"
    })
    
    # 日志配置
    logging: Dict[str, Any] = field(default_factory=lambda: {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": None
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "databases": {
                name: config.to_dict() 
                for name, config in self.databases.items()
            },
            "risk_rules": [
                {
                    "name": rule.name,
                    "pattern": rule.pattern,
                    "level": rule.level.value,
                    "message": rule.message,
                    "description": rule.description,
                    "enabled": rule.enabled
                }
                for rule in self.risk_rules
            ],
            "mcp_server": self.mcp_server,
            "explain": self.explain,
            "logging": self.logging
        }


def load_config(config_path: Optional[str] = None) -> Config:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，如果为 None 则使用默认路径
        
    Returns:
        Config: 配置对象
    """
    # 确定配置文件路径
    if config_path is None:
        # 尝试从环境变量获取
        config_path = os.getenv("SAFESQL_CONFIG_PATH")
        
        if config_path is None:
            # 使用默认路径
            config_path = "safesql.yaml"
    
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        # 返回默认配置
        return Config()
    
    # 读取配置文件
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    if config_data is None:
        return Config()
    
    # 解析配置
    config = Config()
    
    # 解析数据库配置
    if "databases" in config_data:
        for name, db_config in config_data["databases"].items():
            # 处理环境变量
            password = db_config.get("password", "")
            if password.startswith("${") and password.endswith("}"):
                env_var = password[2:-1]
                password = os.getenv(env_var, "")
            
            config.databases[name] = DatabaseConfig(
                type=db_config.get("type", "postgresql"),
                host=db_config.get("host", "localhost"),
                port=db_config.get("port", 5432),
                database=db_config.get("database", ""),
                user=db_config.get("user", ""),
                password=password,
                options=db_config.get("options")
            )
    
    # 解析风险规则配置
    if "risk_rules" in config_data:
        risk_rules_data = config_data["risk_rules"]
        
        # 高风险规则
        for rule_data in risk_rules_data.get("high_risk", []):
            config.risk_rules.append(RiskRule(
                name=rule_data["name"],
                pattern=rule_data["pattern"],
                level=RiskLevel.HIGH,
                message=rule_data["message"],
                description=rule_data.get("description"),
                enabled=rule_data.get("enabled", True)
            ))
        
        # 中风险规则
        for rule_data in risk_rules_data.get("medium_risk", []):
            config.risk_rules.append(RiskRule(
                name=rule_data["name"],
                pattern=rule_data["pattern"],
                level=RiskLevel.MEDIUM,
                message=rule_data["message"],
                description=rule_data.get("description"),
                enabled=rule_data.get("enabled", True)
            ))
        
        # 低风险规则
        for rule_data in risk_rules_data.get("low_risk", []):
            config.risk_rules.append(RiskRule(
                name=rule_data["name"],
                pattern=rule_data["pattern"],
                level=RiskLevel.LOW,
                message=rule_data["message"],
                description=rule_data.get("description"),
                enabled=rule_data.get("enabled", True)
            ))
        
        # 白名单规则
        for rule_data in risk_rules_data.get("whitelist", []):
            config.risk_rules.append(RiskRule(
                name=rule_data["name"],
                pattern=rule_data["pattern"],
                level=RiskLevel.SAFE,
                message=rule_data["message"],
                description=rule_data.get("description"),
                enabled=rule_data.get("enabled", True)
            ))
    
    # 解析 MCP Server 配置
    if "mcp_server" in config_data:
        config.mcp_server.update(config_data["mcp_server"])
    
    # 解析 EXPLAIN 配置
    if "explain" in config_data:
        config.explain.update(config_data["explain"])
    
    # 解析日志配置
    if "logging" in config_data:
        config.logging.update(config_data["logging"])
    
    return config


def save_config(config: Config, config_path: str) -> None:
    """
    保存配置到文件
    
    Args:
        config: 配置对象
        config_path: 配置文件路径
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # 转换为字典
    config_dict = config.to_dict()
    
    # 写入文件
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)


def create_default_config(config_path: str) -> Config:
    """
    创建默认配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config: 默认配置对象
    """
    config = Config()
    
    # 添加示例数据库配置
    config.databases["postgres_example"] = DatabaseConfig(
        type="postgresql",
        host="localhost",
        port=5432,
        database="mydb",
        user="readonly_user",
        password="${POSTGRES_PASSWORD}"
    )
    
    config.databases["mysql_example"] = DatabaseConfig(
        type="mysql",
        host="localhost",
        port=3306,
        database="analytics",
        user="readonly_user",
        password="${MYSQL_PASSWORD}"
    )
    
    # 保存配置
    save_config(config, config_path)
    
    return config