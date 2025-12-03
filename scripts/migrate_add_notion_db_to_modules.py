"""
Migration: Add notion_database_id to modules table
Date: 2025-12-03
"""
import sqlite3
from database.connection import get_connection

def run_migration():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(modules)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'notion_database_id' not in columns:
            print("Adding notion_database_id column to modules table...")
            cursor.execute("""
                ALTER TABLE modules 
                ADD COLUMN notion_database_id TEXT
            """)
            conn.commit()
            print("✅ Migration complete! Column added to modules table.")
        else:
            print("ℹ️  Column 'notion_database_id' already exists. Skipping migration.")

if __name__ == "__main__":
    run_migration()
