from typing import Optional, List
from database.repositories.base import BaseRepository
from database.models import Topic
from datetime import datetime

class TopicRepository(BaseRepository[Topic]):
    def create(self, topic: Topic) -> Topic:
        query = """
            INSERT INTO topics (id, module_id, name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (
            topic.id,
            topic.module_id,
            topic.name,
            topic.created_at,
            topic.updated_at
        ))
        return topic
    
    def get_by_id(self, id: str) -> Optional[Topic]:
        query = "SELECT * FROM topics WHERE id = ?"
        cursor = self.conn.execute(query, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_topic(row)
        return None
    
    def get_for_module(self, module_id: str) -> List[Topic]:
        query = "SELECT * FROM topics WHERE module_id = ? ORDER BY name ASC"
        cursor = self.conn.execute(query, (module_id,))
        return [self._row_to_topic(row) for row in cursor.fetchall()]
    
    def update(self, topic: Topic) -> Topic:
        query = """
            UPDATE topics 
            SET name = ?, updated_at = ?
            WHERE id = ?
        """
        self.conn.execute(query, (
            topic.name,
            datetime.utcnow(),
            topic.id
        ))
        topic.updated_at = datetime.utcnow()
        return topic
    
    def delete(self, id: str) -> bool:
        query = "DELETE FROM topics WHERE id = ?"
        cursor = self.conn.execute(query, (id,))
        return cursor.rowcount > 0

    def _row_to_topic(self, row) -> Topic:
        return Topic(
            id=row['id'],
            module_id=row['module_id'],
            name=row['name'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
