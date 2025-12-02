from typing import Optional, List
from database.repositories.base import BaseRepository
from database.models import ContentItem, ContentType
from datetime import datetime

class ContentRepository(BaseRepository[ContentItem]):
    def create(self, item: ContentItem) -> ContentItem:
        query = """
            INSERT INTO content_items (
                id, topic_id, content_type, file_name, 
                drive_file_id, drive_url, uploaded_at, 
                file_size_bytes, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (
            item.id,
            item.topic_id,
            item.content_type.value,
            item.file_name,
            item.drive_file_id,
            item.drive_url,
            item.uploaded_at,
            item.file_size_bytes,
            item.is_active
        ))
        return item
    
    def get_by_id(self, id: str) -> Optional[ContentItem]:
        query = "SELECT * FROM content_items WHERE id = ?"
        cursor = self.conn.execute(query, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_item(row)
        return None
    
    def get_for_topic(self, topic_id: str) -> List[ContentItem]:
        query = """
            SELECT * FROM content_items 
            WHERE topic_id = ? AND is_active = 1 
            ORDER BY uploaded_at DESC
        """
        cursor = self.conn.execute(query, (topic_id,))
        return [self._row_to_item(row) for row in cursor.fetchall()]
    
    def update(self, item: ContentItem) -> ContentItem:
        query = """
            UPDATE content_items 
            SET drive_file_id = ?, drive_url = ?, is_active = ?
            WHERE id = ?
        """
        self.conn.execute(query, (
            item.drive_file_id,
            item.drive_url,
            item.is_active,
            item.id
        ))
        return item
    
    def delete(self, id: str) -> bool:
        # Soft delete
        query = "UPDATE content_items SET is_active = 0 WHERE id = ?"
        cursor = self.conn.execute(query, (id,))
        return cursor.rowcount > 0

    def _row_to_item(self, row) -> ContentItem:
        return ContentItem(
            id=row['id'],
            topic_id=row['topic_id'],
            content_type=ContentType(row['content_type']),
            file_name=row['file_name'],
            drive_file_id=row['drive_file_id'],
            drive_url=row['drive_url'],
            uploaded_at=row['uploaded_at'],
            file_size_bytes=row['file_size_bytes'],
            is_active=bool(row['is_active'])
        )
