"""
MCP 工具实现：SafeSQL 数据库查询工具
"""

import asyncio
from typing import Any, Dict, List, Optional, Sequence

from mcp import types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from ..core.engine import RiskEngine
from ..core.rules import RiskLevel
from ..databases.base import DatabaseBase, QueryResult
from ..utils.cache import CacheManager, CacheConfig


class SafeSQLTools:
    """SafeSQL MCP 工具集"""
    
    def __init__(self, server: Server, risk_engine: RiskEngine, databases: Dict[str, DatabaseBase], cache_config: Optional[CacheConfig] = None):
        """
        初始化工具集
        
        Args:
            server: MCP Server 实例
            risk_engine: 风险审查引擎
            databases: 数据库连接字典
            cache_config: 缓存配置
        """
        self.server = server
        self.risk_engine = risk_engine
        self.databases = databases
        
        # 初始化缓存管理器
        if cache_config is None:
            cache_config = CacheConfig(enabled=False)
        self.cache_manager = CacheManager(cache_config)
        
        # 注册工具处理器
        self._register_tools()
    
    def _register_tools(self) -> None:
        """注册 MCP 工具"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """列出所有可用工具"""
            return [
                types.Tool(
                    name="query",
                    description="执行 SQL 查询并返回结果，自动进行风险审查",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "string",
                                "description": "数据库连接名称"
                            },
                            "sql": {
                                "type": "string",
                                "description": "SQL 查询语句"
                            },
                            "explain": {
                                "type": "boolean",
                                "description": "是否生成 EXPLAIN 计划",
                                "default": False
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "查询超时时间（秒）",
                                "default": 30
                            },
                            "use_cache": {
                                "type": "boolean",
                                "description": "是否使用缓存",
                                "default": True
                            }
                        },
                        "required": ["database", "sql"]
                    }
                ),
                types.Tool(
                    name="validate",
                    description="验证 SQL 语句的风险等级，不执行查询",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL 查询语句"
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                types.Tool(
                    name="explain",
                    description="生成 SQL 查询的 EXPLAIN 执行计划",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "string",
                                "description": "数据库连接名称"
                            },
                            "sql": {
                                "type": "string",
                                "description": "SQL 查询语句"
                            }
                        },
                        "required": ["database", "sql"]
                    }
                ),
                types.Tool(
                    name="databases",
                    description="列出所有可用的数据库连接",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="schema",
                    description="获取数据库的 schema 信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "string",
                                "description": "数据库连接名称"
                            },
                            "table": {
                                "type": "string",
                                "description": "特定表名（可选）"
                            }
                        },
                        "required": ["database"]
                    }
                ),
                types.Tool(
                    name="test_connection",
                    description="测试数据库连接",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "string",
                                "description": "数据库连接名称"
                            }
                        },
                        "required": ["database"]
                    }
                ),
                types.Tool(
                    name="cache_stats",
                    description="获取缓存统计信息",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="invalidate_cache",
                    description="使缓存失效",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {
                                "type": "string",
                                "description": "数据库连接名称（可选）"
                            },
                            "table": {
                                "type": "string",
                                "description": "表名（可选）"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """处理工具调用"""
            
            if name == "query":
                return await self._handle_query(arguments)
            elif name == "validate":
                return await self._handle_validate(arguments)
            elif name == "explain":
                return await self._handle_explain(arguments)
            elif name == "databases":
                return await self._handle_databases(arguments)
            elif name == "schema":
                return await self._handle_schema(arguments)
            elif name == "test_connection":
                return await self._handle_test_connection(arguments)
            elif name == "cache_stats":
                return await self._handle_cache_stats(arguments)
            elif name == "invalidate_cache":
                return await self._handle_invalidate_cache(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_query(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理查询工具调用"""
        database_name = arguments.get("database")
        sql = arguments.get("sql")
        explain = arguments.get("explain", False)
        timeout = arguments.get("timeout", 30)
        use_cache = arguments.get("use_cache", True)
        
        # 验证参数
        if not database_name or not sql:
            return [types.TextContent(
                type="text",
                text="Error: database and sql parameters are required"
            )]
        
        # 检查数据库是否存在
        if database_name not in self.databases:
            return [types.TextContent(
                type="text",
                text=f"Error: database '{database_name}' not found"
            )]
        
        # 进行风险评估
        assessment = self.risk_engine.assess_sql(sql)
        
        # 构建结果
        result = {
            "risk_assessment": assessment.to_dict(),
            "executable": assessment.is_executable,
            "warning_required": assessment.requires_warning
        }
        
        # 如果是高风险，直接返回，不执行查询
        if not assessment.is_executable:
            result["message"] = f"🚫 高风险 SQL 被拦截：{assessment.message}"
            return [types.TextContent(
                type="text",
                text=self._format_result(result)
            )]
        
        # 检查缓存
        cached_result = None
        if use_cache and self.cache_manager.cache.is_cacheable(sql):
            cached_result = self.cache_manager.cache.get(sql, database=database_name)
            if cached_result:
                result["query_result"] = cached_result
                result["from_cache"] = True
                result["message"] = f"✅ 查询执行成功（从缓存获取）"
                return [types.TextContent(
                    type="text",
                    text=self._format_result(result)
                )]
        
        # 执行查询
        try:
            db = self.databases[database_name]
            
            # 设置超时
            query_result = await asyncio.wait_for(
                db.execute(sql),
                timeout=timeout
            )
            
            # 如果需要 EXPLAIN
            explain_plan = None
            if explain:
                explain_plan = await db.explain(sql)
            
            result["query_result"] = query_result.to_dict()
            if explain_plan:
                result["explain_plan"] = explain_plan
            
            # 缓存结果
            if use_cache and self.cache_manager.cache.is_cacheable(sql):
                self.cache_manager.cache.set(sql, query_result.to_dict(), database=database_name)
            
            # 生成消息
            if assessment.requires_warning:
                result["message"] = f"⚠️ 中风险 SQL 执行成功，但有警告：{assessment.message}"
            else:
                result["message"] = f"✅ 查询执行成功"
            
        except asyncio.TimeoutError:
            result["error"] = f"查询超时（超过 {timeout} 秒）"
            result["message"] = f"❌ 查询超时"
        except Exception as e:
            result["error"] = str(e)
            result["message"] = f"❌ 查询执行失败：{str(e)}"
        
        return [types.TextContent(
            type="text",
            text=self._format_result(result)
        )]
    
    async def _handle_validate(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理验证工具调用"""
        sql = arguments.get("sql")
        
        if not sql:
            return [types.TextContent(
                type="text",
                text="Error: sql parameter is required"
            )]
        
        # 进行风险评估
        assessment = self.risk_engine.assess_sql(sql)
        
        # 构建结果
        result = {
            "sql": sql,
            "risk_assessment": assessment.to_dict(),
            "executable": assessment.is_executable,
            "warning_required": assessment.requires_warning
        }
        
        return [types.TextContent(
            type="text",
            text=self._format_result(result)
        )]
    
    async def _handle_explain(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理 EXPLAIN 工具调用"""
        database_name = arguments.get("database")
        sql = arguments.get("sql")
        
        if not database_name or not sql:
            return [types.TextContent(
                type="text",
                text="Error: database and sql parameters are required"
            )]
        
        # 检查数据库是否存在
        if database_name not in self.databases:
            return [types.TextContent(
                type="text",
                text=f"Error: database '{database_name}' not found"
            )]
        
        try:
            db = self.databases[database_name]
            explain_plan = await db.explain(sql)
            
            result = {
                "sql": sql,
                "explain_plan": explain_plan
            }
            
            return [types.TextContent(
                type="text",
                text=self._format_result(result)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error generating explain plan: {str(e)}"
            )]
    
    async def _handle_databases(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理数据库列表工具调用"""
        databases_info = {}
        
        for name, db in self.databases.items():
            databases_info[name] = {
                "type": db.config.type,
                "host": db.config.host,
                "port": db.config.port,
                "database": db.config.database,
                "connected": db.is_connected
            }
        
        result = {
            "databases": databases_info,
            "count": len(databases_info)
        }
        
        return [types.TextContent(
            type="text",
            text=self._format_result(result)
        )]
    
    async def _handle_schema(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理 schema 工具调用"""
        database_name = arguments.get("database")
        table_name = arguments.get("table")
        
        if not database_name:
            return [types.TextContent(
                type="text",
                text="Error: database parameter is required"
            )]
        
        # 检查数据库是否存在
        if database_name not in self.databases:
            return [types.TextContent(
                type="text",
                text=f"Error: database '{database_name}' not found"
            )]
        
        try:
            db = self.databases[database_name]
            
            if table_name:
                # 获取特定表的 schema
                schema_info = await db.get_table_schema(table_name)
            else:
                # 获取整个数据库的 schema
                schema_info = await db.get_schema()
            
            result = {
                "database": database_name,
                "table": table_name,
                "schema": schema_info
            }
            
            return [types.TextContent(
                type="text",
                text=self._format_result(result)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting schema: {str(e)}"
            )]
    
    async def _handle_test_connection(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理连接测试工具调用"""
        database_name = arguments.get("database")
        
        if not database_name:
            return [types.TextContent(
                type="text",
                text="Error: database parameter is required"
            )]
        
        # 检查数据库是否存在
        if database_name not in self.databases:
            return [types.TextContent(
                type="text",
                text=f"Error: database '{database_name}' not found"
            )]
        
        try:
            db = self.databases[database_name]
            is_connected = await db.test_connection()
            
            result = {
                "database": database_name,
                "connected": is_connected,
                "message": "Connection successful" if is_connected else "Connection failed"
            }
            
            return [types.TextContent(
                type="text",
                text=self._format_result(result)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error testing connection: {str(e)}"
            )]
    
    async def _handle_cache_stats(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理缓存统计工具调用"""
        stats = self.cache_manager.get_stats()
        
        result = {
            "cache_stats": stats
        }
        
        return [types.TextContent(
            type="text",
            text=self._format_result(result)
        )]
    
    async def _handle_invalidate_cache(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """处理缓存失效工具调用"""
        database_name = arguments.get("database")
        table_name = arguments.get("table")
        
        if database_name or table_name:
            # 使特定缓存失效
            self.cache_manager.invalidate_for_sql(f"SELECT * FROM {table_name or '*'}")
            message = f"Cache invalidated for {database_name or 'all databases'}"
        else:
            # 使所有缓存失效
            self.cache_manager.cache.invalidate_all()
            message = "All cache invalidated"
        
        result = {
            "message": message,
            "cache_stats": self.cache_manager.get_stats()
        }
        
        return [types.TextContent(
            type="text",
            text=self._format_result(result)
        )]
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """格式化结果为可读文本"""
        import json
        return json.dumps(result, indent=2, ensure_ascii=False)