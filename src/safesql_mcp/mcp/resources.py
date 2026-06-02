"""
MCP 资源实现：SafeSQL 数据库资源
"""

from typing import Any, Dict, List, Optional, Sequence

from mcp import types
from mcp.server import Server

from ..databases.base import DatabaseBase


class SafeSQLResources:
    """SafeSQL MCP 资源集"""
    
    def __init__(self, server: Server, databases: Dict[str, DatabaseBase]):
        """
        初始化资源集
        
        Args:
            server: MCP Server 实例
            databases: 数据库连接字典
        """
        self.server = server
        self.databases = databases
        
        # 注册资源处理器
        self._register_resources()
    
    def _register_resources(self) -> None:
        """注册 MCP 资源"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[types.Resource]:
            """列出所有可用资源"""
            resources = []
            
            # 为每个数据库创建资源
            for name, db in self.databases.items():
                # 数据库 schema 资源
                resources.append(types.Resource(
                    uri=f"safesql://database/{name}/schema",
                    name=f"{name} Schema",
                    description=f"Database schema for {name}",
                    mimeType="application/json"
                ))
                
                # 数据库表列表资源
                resources.append(types.Resource(
                    uri=f"safesql://database/{name}/tables",
                    name=f"{name} Tables",
                    description=f"Table list for {name}",
                    mimeType="application/json"
                ))
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """读取资源内容"""
            # 解析 URI
            if not uri.startswith("safesql://"):
                raise ValueError(f"Invalid URI: {uri}")
            
            parts = uri.replace("safesql://", "").split("/")
            if len(parts) < 3:
                raise ValueError(f"Invalid URI format: {uri}")
            
            resource_type = parts[0]  # database
            database_name = parts[1]
            resource_name = parts[2]
            
            # 检查数据库是否存在
            if database_name not in self.databases:
                raise ValueError(f"Database '{database_name}' not found")
            
            db = self.databases[database_name]
            
            try:
                if resource_name == "schema":
                    # 获取数据库 schema
                    schema_info = await db.get_schema()
                    import json
                    return json.dumps(schema_info, indent=2, ensure_ascii=False)
                
                elif resource_name == "tables":
                    # 获取表列表
                    tables = await db.get_tables()
                    import json
                    return json.dumps({"tables": tables}, indent=2)
                
                else:
                    # 检查是否是特定表的 schema
                    if resource_name.startswith("table/"):
                        table_name = resource_name.replace("table/", "")
                        table_schema = await db.get_table_schema(table_name)
                        import json
                        return json.dumps(table_schema, indent=2, ensure_ascii=False)
                    else:
                        raise ValueError(f"Unknown resource: {resource_name}")
            
            except Exception as e:
                raise RuntimeError(f"Failed to read resource: {str(e)}")
    
    def get_resource_templates(self) -> List[types.ResourceTemplate]:
        """获取资源模板"""
        return [
            types.ResourceTemplate(
                uriTemplate="safesql://database/{database}/schema",
                name="Database Schema",
                description="Get database schema information",
                mimeType="application/json"
            ),
            types.ResourceTemplate(
                uriTemplate="safesql://database/{database}/tables",
                name="Database Tables",
                description="Get list of tables in database",
                mimeType="application/json"
            ),
            types.ResourceTemplate(
                uriTemplate="safesql://database/{database}/table/{table}",
                name="Table Schema",
                description="Get table schema information",
                mimeType="application/json"
            )
        ]