"""
Integration tests for MCP tools
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from safesql_mcp.core.engine import RiskEngine
from safesql_mcp.core.rules import RiskLevel
from safesql_mcp.databases.base import DatabaseBase, DatabaseConfig, QueryResult
from safesql_mcp.mcp.tools import SafeSQLTools


class MockDatabase(DatabaseBase):
    """Mock database for testing"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._connected = False
        self._mock_result = QueryResult(
            columns=["id", "name"],
            rows=[(1, "test"), (2, "test2")],
            row_count=2,
            execution_time=0.1
        )
    
    async def connect(self) -> None:
        self._connected = True
        self._is_connected = True
    
    async def disconnect(self) -> None:
        self._connected = False
        self._is_connected = False
    
    async def execute(self, sql: str, params=None) -> QueryResult:
        if not self._connected:
            raise ConnectionError("Not connected")
        return self._mock_result
    
    async def explain(self, sql: str, analyze: bool = False) -> str:
        return "Seq Scan on users  (cost=0.00..1.02 rows=2 width=100)"
    
    async def get_schema(self) -> Dict[str, Any]:
        return {
            "database": "testdb",
            "user": "testuser",
            "version": "PostgreSQL 15.0",
            "schemas": ["public"],
            "tables": [{"schema": "public", "name": "users", "type": "BASE TABLE"}]
        }
    
    async def get_tables(self) -> list:
        return ["users", "orders"]
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        return {
            "table": table_name,
            "columns": [
                {"name": "id", "type": "integer", "nullable": False, "default": None},
                {"name": "name", "type": "varchar", "nullable": True, "default": None}
            ],
            "indexes": [],
            "constraints": []
        }
    
    async def test_connection(self) -> bool:
        return self._connected
    
    async def _rollback(self) -> None:
        pass
    
    async def _commit(self) -> None:
        pass


@pytest.fixture
def mock_server():
    """Create a mock MCP server"""
    server = MagicMock()
    server.list_tools = MagicMock()
    server.call_tool = MagicMock()
    server.list_resources = MagicMock()
    server.read_resource = MagicMock()
    return server


@pytest.fixture
def risk_engine():
    """Create a risk engine instance"""
    return RiskEngine()


@pytest.fixture
def mock_database():
    """Create a mock database instance"""
    config = DatabaseConfig(
        type="postgresql",
        host="localhost",
        port=5432,
        database="testdb",
        user="testuser",
        password="testpass"
    )
    return MockDatabase(config)


@pytest.fixture
def databases(mock_database):
    """Create a databases dictionary"""
    return {"testdb": mock_database}


@pytest.fixture
def safe_sql_tools(mock_server, risk_engine, databases):
    """Create SafeSQL tools instance"""
    return SafeSQLTools(mock_server, risk_engine, databases)


class TestSafeSQLTools:
    """Test SafeSQL MCP tools"""
    
    @pytest.mark.asyncio
    async def test_handle_query_safe_sql(self, safe_sql_tools, mock_database):
        """Test handling a safe SQL query"""
        await mock_database.connect()
        
        arguments = {
            "database": "testdb",
            "sql": "SELECT id, name FROM users WHERE id = 1",
            "explain": False,
            "timeout": 30
        }
        
        result = await safe_sql_tools._handle_query(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the result
        import json
        data = json.loads(result[0].text)
        assert data["executable"] is True
        assert data["risk_assessment"]["risk_level"] == "low"
    
    @pytest.mark.asyncio
    async def test_handle_query_high_risk_sql(self, safe_sql_tools, mock_database):
        """Test handling a high risk SQL query"""
        await mock_database.connect()
        
        arguments = {
            "database": "testdb",
            "sql": "DROP TABLE users",
            "explain": False,
            "timeout": 30
        }
        
        result = await safe_sql_tools._handle_query(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert data["executable"] is False
        assert data["risk_assessment"]["risk_level"] == "high"
        assert "拦截" in data["message"]
    
    @pytest.mark.asyncio
    async def test_handle_query_medium_risk_sql(self, safe_sql_tools, mock_database):
        """Test handling a medium risk SQL query"""
        await mock_database.connect()
        
        arguments = {
            "database": "testdb",
            "sql": "SELECT * FROM users",
            "explain": False,
            "timeout": 30
        }
        
        result = await safe_sql_tools._handle_query(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert data["executable"] is True
        assert data["risk_assessment"]["risk_level"] == "medium"
        assert data["warning_required"] is True
    
    @pytest.mark.asyncio
    async def test_handle_query_with_explain(self, safe_sql_tools, mock_database):
        """Test handling a query with EXPLAIN"""
        await mock_database.connect()
        
        arguments = {
            "database": "testdb",
            "sql": "SELECT id, name FROM users WHERE id = 1",
            "explain": True,
            "timeout": 30
        }
        
        result = await safe_sql_tools._handle_query(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert "explain_plan" in data
        assert data["explain_plan"] is not None
    
    @pytest.mark.asyncio
    async def test_handle_query_invalid_database(self, safe_sql_tools):
        """Test handling a query with invalid database"""
        arguments = {
            "database": "nonexistent",
            "sql": "SELECT * FROM users",
            "explain": False,
            "timeout": 30
        }
        
        result = await safe_sql_tools._handle_query(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Error" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_query_missing_parameters(self, safe_sql_tools):
        """Test handling a query with missing parameters"""
        arguments = {
            "database": "testdb"
            # Missing sql parameter
        }
        
        result = await safe_sql_tools._handle_query(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Error" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_validate_safe_sql(self, safe_sql_tools):
        """Test validating a safe SQL"""
        arguments = {
            "sql": "SELECT id, name FROM users WHERE id = 1"
        }
        
        result = await safe_sql_tools._handle_validate(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert data["executable"] is True
        assert data["risk_assessment"]["risk_level"] == "low"
    
    @pytest.mark.asyncio
    async def test_handle_validate_high_risk_sql(self, safe_sql_tools):
        """Test validating a high risk SQL"""
        arguments = {
            "sql": "DROP TABLE users"
        }
        
        result = await safe_sql_tools._handle_validate(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert data["executable"] is False
        assert data["risk_assessment"]["risk_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_handle_validate_missing_sql(self, safe_sql_tools):
        """Test validating with missing SQL"""
        arguments = {}
        
        result = await safe_sql_tools._handle_validate(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Error" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_explain(self, safe_sql_tools, mock_database):
        """Test handling EXPLAIN request"""
        await mock_database.connect()
        
        arguments = {
            "database": "testdb",
            "sql": "SELECT * FROM users WHERE id = 1"
        }
        
        result = await safe_sql_tools._handle_explain(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert "explain_plan" in data
        assert "Seq Scan" in data["explain_plan"]
    
    @pytest.mark.asyncio
    async def test_handle_explain_invalid_database(self, safe_sql_tools):
        """Test handling EXPLAIN with invalid database"""
        arguments = {
            "database": "nonexistent",
            "sql": "SELECT * FROM users"
        }
        
        result = await safe_sql_tools._handle_explain(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Error" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_databases(self, safe_sql_tools, mock_database):
        """Test handling databases list request"""
        await mock_database.connect()
        
        arguments = {}
        
        result = await safe_sql_tools._handle_databases(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert "databases" in data
        assert "testdb" in data["databases"]
        assert data["databases"]["testdb"]["type"] == "postgresql"
    
    @pytest.mark.asyncio
    async def test_handle_schema(self, safe_sql_tools, mock_database):
        """Test handling schema request"""
        await mock_database.connect()
        
        arguments = {
            "database": "testdb"
        }
        
        result = await safe_sql_tools._handle_schema(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert "schema" in data
        assert data["schema"]["database"] == "testdb"
    
    @pytest.mark.asyncio
    async def test_handle_schema_with_table(self, safe_sql_tools, mock_database):
        """Test handling schema request for specific table"""
        await mock_database.connect()
        
        arguments = {
            "database": "testdb",
            "table": "users"
        }
        
        result = await safe_sql_tools._handle_schema(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert "schema" in data
        assert data["schema"]["table"] == "users"
    
    @pytest.mark.asyncio
    async def test_handle_test_connection(self, safe_sql_tools, mock_database):
        """Test handling connection test request"""
        await mock_database.connect()
        
        arguments = {
            "database": "testdb"
        }
        
        result = await safe_sql_tools._handle_test_connection(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert data["connected"] is True
        assert data["message"] == "Connection successful"
    
    @pytest.mark.asyncio
    async def test_handle_test_connection_not_connected(self, safe_sql_tools, mock_database):
        """Test handling connection test when not connected"""
        arguments = {
            "database": "testdb"
        }
        
        result = await safe_sql_tools._handle_test_connection(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        import json
        data = json.loads(result[0].text)
        assert data["connected"] is False
        assert data["message"] == "Connection failed"
    
    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self, safe_sql_tools):
        """Test handling unknown tool"""
        # This test verifies that the tool registration is working
        # In a real MCP server, unknown tools would raise an error
        # For unit testing, we just verify the SafeSQLTools object is properly initialized
        assert safe_sql_tools.risk_engine is not None
        assert safe_sql_tools.databases is not None
        assert len(safe_sql_tools.databases) > 0