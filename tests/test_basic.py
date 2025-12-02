def test_imports():
    """Verify that all key modules can be imported."""
    try:
        import app
        from database.connection import get_connection
        from database.models import Module
        from database.repositories.module_repo import ModuleRepository
        from ui.components.sidebar import render_sidebar
    except ImportError as e:
        assert False, f"Failed to import module: {e}"

def test_database_initialization(mock_settings):
    """Verify database can be initialized."""
    from database.connection import init_db, get_connection
    
    # Run init
    init_db()
    
    # Check if file exists
    assert mock_settings.DATABASE_PATH.exists()
    
    # Check connection
    with get_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='modules'")
        assert cursor.fetchone() is not None
