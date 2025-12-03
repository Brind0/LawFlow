from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

class ContentType(Enum):
    LECTURE_PDF = "LECTURE_PDF"
    SOURCE_MATERIAL = "SOURCE_MATERIAL"
    TUTORIAL_PDF = "TUTORIAL_PDF"
    TRANSCRIPT = "TRANSCRIPT"

class Stage(Enum):
    MK1 = "MK1"
    MK2 = "MK2"
    MK3 = "MK3"

class GenerationStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class Module:
    id: str
    name: str
    claude_project_name: Optional[str]
    notion_database_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(name: str, claude_project_name: str = None, notion_database_id: str = None) -> 'Module':
        now = datetime.utcnow()
        return Module(
            id=str(uuid.uuid4()),
            name=name,
            claude_project_name=claude_project_name,
            notion_database_id=notion_database_id,
            created_at=now,
            updated_at=now
        )

@dataclass
class Topic:
    id: str
    module_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    
    @staticmethod
    def create(module_id: str, name: str) -> 'Topic':
        now = datetime.utcnow()
        return Topic(
            id=str(uuid.uuid4()),
            module_id=module_id,
            name=name,
            created_at=now,
            updated_at=now
        )

@dataclass
class ContentItem:
    id: str
    topic_id: str
    content_type: ContentType
    file_name: str
    drive_file_id: Optional[str]
    drive_url: Optional[str]
    uploaded_at: datetime
    file_size_bytes: int
    is_active: bool  # False = soft deleted
    
    @staticmethod
    def create(
        topic_id: str,
        content_type: ContentType,
        file_name: str,
        file_size_bytes: int,
        drive_file_id: Optional[str] = None,
        drive_url: Optional[str] = None
    ) -> 'ContentItem':
        return ContentItem(
            id=str(uuid.uuid4()),
            topic_id=topic_id,
            content_type=content_type,
            file_name=file_name,
            drive_file_id=drive_file_id,
            drive_url=drive_url,
            uploaded_at=datetime.utcnow(),
            file_size_bytes=file_size_bytes,
            is_active=True
        )

@dataclass
class Generation:
    id: str
    topic_id: str
    stage: Stage
    version: int
    prompt_used: str
    response_content: Optional[str]
    notion_page_id: Optional[str]
    notion_url: Optional[str]
    drive_backup_id: Optional[str]
    drive_backup_url: Optional[str]
    previous_generation_id: Optional[str]  # For Mk-3, points to Mk-2
    created_at: datetime
    status: GenerationStatus
    
    @staticmethod
    def create(
        topic_id: str,
        stage: Stage,
        version: int,
        prompt_used: str,
        previous_generation_id: str = None
    ) -> 'Generation':
        return Generation(
            id=str(uuid.uuid4()),
            topic_id=topic_id,
            stage=stage,
            version=version,
            prompt_used=prompt_used,
            response_content=None,
            notion_page_id=None,
            notion_url=None,
            drive_backup_id=None,
            drive_backup_url=None,
            previous_generation_id=previous_generation_id,
            created_at=datetime.utcnow(),
            status=GenerationStatus.PENDING
        )
