import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from services.content_service import ContentService
from database.models import ContentItem, ContentType

@pytest.fixture
def mock_drive_client():
    with patch('services.content_service.DriveClient') as MockClient:
        client_instance = MockClient.return_value
        # Mock get_or_create_folder
        client_instance.get_or_create_folder.return_value = "folder_123"
        # Mock upload_file
        client_instance.upload_file.return_value = {
            "id": "file_123",
            "url": "http://drive.google.com/file_123"
        }
        yield client_instance

@pytest.fixture
def content_service(mock_settings, mock_drive_client):
    # Mock connection
    conn = MagicMock()
    
    # Mock Repository
    with patch('services.content_service.ContentRepository') as MockRepo:
        repo_instance = MockRepo.return_value
        repo_instance.create.side_effect = lambda x: x # Return the item itself
        
        service = ContentService(conn)
        service.repo = repo_instance
        service.drive_client = mock_drive_client # Inject mock
        return service

def test_upload_content(content_service):
    # Prepare mock file
    file_content = b"Test PDF Content"
    file_obj = BytesIO(file_content)
    file_obj.name = "lecture.pdf"
    
    # Call upload
    item = content_service.upload_content(
        file_obj=file_obj,
        filename="lecture.pdf",
        topic_id="topic_1",
        module_name="Land Law",
        topic_name="Registration"
    )
    
    # Verify Drive calls
    content_service.drive_client.get_or_create_folder.assert_any_call("LawFlow")
    content_service.drive_client.get_or_create_folder.assert_any_call("Land Law", parent_id="folder_123")
    content_service.drive_client.upload_file.assert_called_once()
    
    # Verify Item creation
    assert item.file_name == "lecture.pdf"
    assert item.drive_file_id == "file_123"
    assert item.content_type == ContentType.LECTURE_PDF
    assert item.file_size_bytes == len(file_content)

def test_delete_content(content_service):
    # Mock existing item
    item = ContentItem.create(
        topic_id="t1", 
        content_type=ContentType.TRANSCRIPT, 
        file_name="test.txt",
        file_size_bytes=100,
        drive_file_id="d1"
    )
    content_service.repo.get_by_id.return_value = item
    content_service.repo.delete.return_value = True
    
    # Call delete
    result = content_service.delete_content("item_1")
    
    # Verify
    assert result is True
    content_service.drive_client.delete_file.assert_called_with("d1")
    content_service.repo.delete.assert_called_with("item_1")
