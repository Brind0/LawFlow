import pytest
import os
import sys
import sqlite3
from pathlib import Path

# Add project root to python path
sys.path.append(str(Path(__file__).parent.parent))

@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database for testing."""
    d = tmp_path / "data"
    d.mkdir()
    return d / "test_lawflow.db"

@pytest.fixture
def mock_settings(monkeypatch, test_db_path):
    """Mock settings to use temporary database."""
    from config.settings import settings
    monkeypatch.setattr(settings, "DATABASE_PATH", test_db_path)
    return settings

@pytest.fixture
def test_db_conn(mock_settings):
    """Create a test database connection with schema initialized."""
    from database.connection import init_db

    # Initialize database with schema
    init_db()

    # Create connection with Row factory
    conn = sqlite3.connect(mock_settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    yield conn

    # Cleanup
    conn.close()
