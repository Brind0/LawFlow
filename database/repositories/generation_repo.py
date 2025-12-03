from typing import Optional, List
from database.repositories.base import BaseRepository
from database.models import Generation, Stage, GenerationStatus
from datetime import datetime


class GenerationRepository(BaseRepository[Generation]):
    def create(self, generation: Generation) -> Generation:
        query = """
            INSERT INTO generations (
                id, topic_id, stage, version, prompt_used,
                response_content, notion_page_id, notion_url,
                drive_backup_id, drive_backup_url, previous_generation_id,
                created_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (
            generation.id,
            generation.topic_id,
            generation.stage.value,
            generation.version,
            generation.prompt_used,
            generation.response_content,
            generation.notion_page_id,
            generation.notion_url,
            generation.drive_backup_id,
            generation.drive_backup_url,
            generation.previous_generation_id,
            generation.created_at,
            generation.status.value
        ))
        return generation

    def get_by_id(self, id: str) -> Optional[Generation]:
        query = "SELECT * FROM generations WHERE id = ?"
        cursor = self.conn.execute(query, (id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_generation(row)
        return None

    def get_for_topic(self, topic_id: str) -> List[Generation]:
        """Get all generations for a topic, ordered by creation date (newest first)"""
        query = """
            SELECT * FROM generations
            WHERE topic_id = ?
            ORDER BY created_at DESC
        """
        cursor = self.conn.execute(query, (topic_id,))
        return [self._row_to_generation(row) for row in cursor.fetchall()]

    def get_by_stage(self, topic_id: str, stage: Stage) -> List[Generation]:
        """Get all generations for a specific topic and stage, ordered by version (newest first)"""
        query = """
            SELECT * FROM generations
            WHERE topic_id = ? AND stage = ?
            ORDER BY version DESC
        """
        cursor = self.conn.execute(query, (topic_id, stage.value))
        return [self._row_to_generation(row) for row in cursor.fetchall()]

    def get_latest_version(self, topic_id: str, stage: Stage) -> Optional[Generation]:
        """Get the most recent generation for a specific topic and stage"""
        query = """
            SELECT * FROM generations
            WHERE topic_id = ? AND stage = ?
            ORDER BY version DESC
            LIMIT 1
        """
        cursor = self.conn.execute(query, (topic_id, stage.value))
        row = cursor.fetchone()
        if row:
            return self._row_to_generation(row)
        return None

    def get_completed_for_stage(self, topic_id: str, stage: Stage) -> List[Generation]:
        """Get all completed generations for a specific topic and stage"""
        query = """
            SELECT * FROM generations
            WHERE topic_id = ? AND stage = ? AND status = 'COMPLETED'
            ORDER BY version DESC
        """
        cursor = self.conn.execute(query, (topic_id, stage.value))
        return [self._row_to_generation(row) for row in cursor.fetchall()]

    def get_next_version(self, topic_id: str, stage: Stage) -> int:
        """Get the next version number for a topic+stage combination"""
        query = """
            SELECT MAX(version) as max_version
            FROM generations
            WHERE topic_id = ? AND stage = ?
        """
        cursor = self.conn.execute(query, (topic_id, stage.value))
        row = cursor.fetchone()
        max_version = row['max_version'] if row['max_version'] is not None else 0
        return max_version + 1

    def update(self, generation: Generation) -> Generation:
        query = """
            UPDATE generations
            SET response_content = ?,
                notion_page_id = ?,
                notion_url = ?,
                drive_backup_id = ?,
                drive_backup_url = ?,
                status = ?
            WHERE id = ?
        """
        self.conn.execute(query, (
            generation.response_content,
            generation.notion_page_id,
            generation.notion_url,
            generation.drive_backup_id,
            generation.drive_backup_url,
            generation.status.value,
            generation.id
        ))
        return generation

    def delete(self, id: str) -> bool:
        """Hard delete a generation (no soft delete for generations)"""
        query = "DELETE FROM generations WHERE id = ?"
        cursor = self.conn.execute(query, (id,))
        return cursor.rowcount > 0

    def _row_to_generation(self, row) -> Generation:
        """Convert a database row to a Generation object"""
        return Generation(
            id=row['id'],
            topic_id=row['topic_id'],
            stage=Stage(row['stage']),
            version=row['version'],
            prompt_used=row['prompt_used'],
            response_content=row['response_content'],
            notion_page_id=row['notion_page_id'],
            notion_url=row['notion_url'],
            drive_backup_id=row['drive_backup_id'],
            drive_backup_url=row['drive_backup_url'],
            previous_generation_id=row['previous_generation_id'],
            created_at=row['created_at'],
            status=GenerationStatus(row['status'])
        )
