import pytest
import os
import sys
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
