import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from config.settings import settings

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with schema."""
    if not settings.DATABASE_PATH.parent.exists():
        settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
    conn = sqlite3.connect(settings.DATABASE_PATH)
    
    schema_path = settings.BASE_DIR / "database" / "schema.sql"
    if schema_path.exists():
        with open(schema_path, "r") as f:
            conn.executescript(f.read())
    else:
        logger.error(f"Schema file not found at {schema_path}")
        
    conn.close()

@contextmanager
def get_connection():
    """
    Context manager for SQLite database connection.
    Ensures connection is closed after use.
    """
    if not settings.DATABASE_PATH.exists():
        init_db()
        
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
