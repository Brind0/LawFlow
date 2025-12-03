"""
Update modules with Notion database IDs
Run this once to configure the database IDs for each module
"""
import sqlite3

# Module name -> Notion Database ID mapping
MODULE_DBS = {
    "Land Law": "27f203d451d180a8ae8ee2de21141297",
    "Tort Law": "27f203d451d180f2b785dbf4c696b9ed",
    "Employment Law": "27f203d451d180c9996eed832036e572",
    "Legal Practice": "27f203d451d1806693aac3310264511f",
}

def update_modules():
    conn = sqlite3.connect('data/lawflow.db')
    cursor = conn.cursor()
    
    print("Updating module Notion database IDs...\n")
    
    for module_name, db_id in MODULE_DBS.items():
        cursor.execute(
            "UPDATE modules SET notion_database_id = ? WHERE name = ?",
            (db_id, module_name)
        )
        if cursor.rowcount > 0:
            print(f"✅ {module_name} → {db_id}")
        else:
            print(f"⚠️  Module '{module_name}' not found in database")
    
    conn.commit()
    conn.close()
    print("\n✅ All modules updated!")

if __name__ == "__main__":
    update_modules()
