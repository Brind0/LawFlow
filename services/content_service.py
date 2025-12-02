import os
from typing import List, Optional
from datetime import datetime
from database.models import ContentItem, ContentType
from database.repositories.content_repo import ContentRepository
from integrations.drive_client import DriveClient
from config.settings import settings

class ContentService:
    """
    Service layer for managing content items.
    Orchestrates interactions between the UI, Database, and Google Drive.
    """
    
    def __init__(self, conn):
        self.repo = ContentRepository(conn)
        # Initialize Drive Client only if credentials exist
        if settings.GOOGLE_CREDENTIALS_PATH.exists():
            self.drive_client = DriveClient(
                credentials_path=str(settings.GOOGLE_CREDENTIALS_PATH),
                token_path=str(settings.GOOGLE_TOKEN_PATH)
            )
        else:
            self.drive_client = None
            
    def upload_content(
        self, 
        file_obj, 
        filename: str, 
        topic_id: str,
        module_name: str,
        topic_name: str
    ) -> ContentItem:
        """
        Uploads a file to Google Drive and creates a database record.
        """
        if not self.drive_client:
            raise Exception("Google Drive credentials not configured.")
            
        # 1. Ensure Folder Structure Exists
        # Root -> Module -> Topic
        root_id = self.drive_client.get_or_create_folder(settings.DRIVE_ROOT_FOLDER)
        module_folder_id = self.drive_client.get_or_create_folder(module_name, parent_id=root_id)
        topic_folder_id = self.drive_client.get_or_create_folder(topic_name, parent_id=module_folder_id)
        
        # 2. Upload to Drive
        # Read file content
        content_bytes = file_obj.getvalue()
        file_size = len(content_bytes)
        
        # Determine mime type (basic)
        mime_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'text/plain'
        
        drive_file = self.drive_client.upload_file(
            file_content=content_bytes,
            file_name=filename,
            folder_id=topic_folder_id,
            mime_type=mime_type
        )
        
        # 3. Create Database Record
        content_item = ContentItem.create(
            topic_id=topic_id,
            content_type=ContentType.LECTURE_PDF if mime_type == 'application/pdf' else ContentType.TRANSCRIPT,
            file_name=filename,
            drive_file_id=drive_file['id'],
            drive_url=drive_file['url'],
            file_size_bytes=file_size
        )
        
        return self.repo.create(content_item)
    
    def get_topic_content(self, topic_id: str) -> List[ContentItem]:
        """
        Retrieves all active content for a topic.
        """
        return self.repo.get_for_topic(topic_id)
    
    def delete_content(self, content_id: str) -> bool:
        """
        Soft deletes content from DB and trashes it in Drive.
        """
        item = self.repo.get_by_id(content_id)
        if not item:
            return False
            
        # 1. Trash in Drive (if client available)
        if self.drive_client and item.drive_file_id:
            try:
                self.drive_client.delete_file(item.drive_file_id)
            except Exception as e:
                print(f"Warning: Failed to delete from Drive: {e}")
                # Continue to soft delete in DB
        
        # 2. Soft delete in DB
        return self.repo.delete(content_id)
