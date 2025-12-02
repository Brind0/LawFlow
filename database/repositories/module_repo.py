from typing import Optional, List
from database.repositories.base import BaseRepository
from database.models import Module
from datetime import datetime

class ModuleRepository(BaseRepository[Module]):
    def create(self, module: Module) -> Module:
        query = """
            INSERT INTO modules (id, name, claude_project_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (
            module.id,
            module.name,
            module.claude_project_name,
            module.created_at,
            module.updated_at
        ))
        return module
    
    def get_by_id(self, id: str) -> Optional[Module]:
        query = "SELECT * FROM modules WHERE id = ?"
        cursor = self.conn.execute(query, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_module(row)
        return None
    
    def get_all(self) -> List[Module]:
        query = "SELECT * FROM modules ORDER BY name ASC"
        cursor = self.conn.execute(query)
        return [self._row_to_module(row) for row in cursor.fetchall()]
    
    def update(self, module: Module) -> Module:
        query = """
            UPDATE modules 
            SET name = ?, claude_project_name = ?, updated_at = ?
            WHERE id = ?
        """
        self.conn.execute(query, (
            module.name,
            module.claude_project_name,
            datetime.utcnow(),
            module.id
        ))
        # Refresh updated_at from object (approximate) or fetch again
        module.updated_at = datetime.utcnow() 
        return module
    
    def delete(self, id: str) -> bool:
        query = "DELETE FROM modules WHERE id = ?"
        cursor = self.conn.execute(query, (id,))
        return cursor.rowcount > 0

    def _row_to_module(self, row) -> Module:
        return Module(
            id=row['id'],
            name=row['name'],
            claude_project_name=row['claude_project_name'],
            created_at=row['created_at'], # SQLite stores as string, might need parsing if strict datetime needed
            updated_at=row['updated_at']
        )
