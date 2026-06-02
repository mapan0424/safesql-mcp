"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_sql_select():
    """Sample SELECT SQL statement"""
    return "SELECT id, name, email FROM users WHERE status = 'active'"


@pytest.fixture
def sample_sql_insert():
    """Sample INSERT SQL statement"""
    return "INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com')"


@pytest.fixture
def sample_sql_update():
    """Sample UPDATE SQL statement"""
    return "UPDATE users SET status = 'inactive' WHERE id = 1"


@pytest.fixture
def sample_sql_delete():
    """Sample DELETE SQL statement"""
    return "DELETE FROM users WHERE id = 1"


@pytest.fixture
def sample_sql_dangerous():
    """Sample dangerous SQL statement"""
    return "DROP TABLE users"


@pytest.fixture
def sample_sql_medium_risk():
    """Sample medium risk SQL statement"""
    return "SELECT * FROM users WHERE name LIKE '%john%'"