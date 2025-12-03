"""
Unit tests for OutputService.

Tests the orchestration of processing Claude's responses:
- Markdown to Notion blocks conversion
- Generation record updates
- Error handling and rollback
- Integration with NotionClient and DriveClient (mocked)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from database.repositories.generation_repo import GenerationRepository
from database.repositories.topic_repo import TopicRepository
from database.repositories.module_repo import ModuleRepository
from database.models import Generation, Topic, Module, Stage, GenerationStatus
from services.output_service import OutputService


class TestOutputService:
    """Test suite for OutputService"""

    @pytest.fixture
    def mock_notion_client(self):
        """Create a mock NotionClient"""
        mock = Mock()
        mock.create_page.return_value = {
            'id': 'notion-page-123',
            'url': 'https://notion.so/page-123'
        }
        # For rollback testing
        mock.client = Mock()
        mock.client.pages = Mock()
        mock.client.pages.update = Mock()
        return mock

    @pytest.fixture
    def mock_drive_client(self):
        """Create a mock DriveClient"""
        mock = Mock()
        mock.get_or_create_folder.return_value = 'folder-id-123'
        mock.upload_file.return_value = {
            'id': 'drive-file-456',
            'url': 'https://drive.google.com/file/456'
        }
        mock.delete_file.return_value = True
        return mock

    @pytest.fixture
    def service(self, test_db_conn, mock_notion_client, mock_drive_client):
        """Create an OutputService instance with mocked clients"""
        return OutputService(
            conn=test_db_conn,
            notion_client=mock_notion_client,
            drive_client=mock_drive_client
        )

    @pytest.fixture
    def sample_data(self, test_db_conn):
        """Create sample module, topic, and generation for testing"""
        # Create module
        module = Module.create(name="Land Law", claude_project_name="land-law")
        module_repo = ModuleRepository(test_db_conn)
        created_module = module_repo.create(module)

        # Create topic
        topic = Topic.create(module_id=created_module.id, name="Easements")
        topic_repo = TopicRepository(test_db_conn)
        created_topic = topic_repo.create(topic)

        # Create pending generation
        generation = Generation.create(
            topic_id=created_topic.id,
            stage=Stage.MK1,
            version=1,
            prompt_used="Test prompt"
        )
        gen_repo = GenerationRepository(test_db_conn)
        created_generation = gen_repo.create(generation)

        # Commit the test data so it's not rolled back during error tests
        test_db_conn.commit()

        return {
            'module': created_module,
            'topic': created_topic,
            'generation': created_generation
        }

    # ==================== SUCCESSFUL PROCESSING TESTS ====================

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_successful(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        test_db_conn
    ):
        """Test successful processing of Claude's response"""
        # Setup mocks
        mock_blocks = [{'type': 'paragraph', 'paragraph': {'rich_text': []}}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        generation_id = sample_data['generation'].id
        response_content = "# Test Notes\n\nThis is a test response."
        notion_db_id = "notion-database-123"

        # Process response
        result = service.process_response(
            generation_id=generation_id,
            response_content=response_content,
            notion_database_id=notion_db_id
        )

        # Verify result structure
        assert 'notion_url' in result
        assert 'drive_url' in result
        assert 'generation_id' in result
        assert result['generation_id'] == generation_id
        assert result['notion_url'] == 'https://notion.so/page-123'
        assert result['drive_url'] == 'https://drive.google.com/file/456'

        # Verify generation was updated
        gen_repo = GenerationRepository(test_db_conn)
        updated_gen = gen_repo.get_by_id(generation_id)
        assert updated_gen.status == GenerationStatus.COMPLETED
        assert updated_gen.response_content == response_content
        assert updated_gen.notion_page_id == 'notion-page-123'
        assert updated_gen.notion_url == 'https://notion.so/page-123'
        assert updated_gen.drive_backup_id == 'drive-file-456'
        assert updated_gen.drive_backup_url == 'https://drive.google.com/file/456'

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_calls_notion_with_correct_params(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        mock_notion_client
    ):
        """Test that Notion client is called with correct parameters"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        generation_id = sample_data['generation'].id
        response_content = "Test content"
        notion_db_id = "notion-db-123"

        service.process_response(
            generation_id=generation_id,
            response_content=response_content,
            notion_database_id=notion_db_id
        )

        # Verify Notion create_page was called
        mock_notion_client.create_page.assert_called_once()
        call_args = mock_notion_client.create_page.call_args

        # Check the title includes module, topic, and stage
        assert 'Land Law' in call_args[1]['title']
        assert 'Easements' in call_args[1]['title']
        assert 'MK1' in call_args[1]['title']

        # Check properties
        properties = call_args[1]['properties']
        assert properties['Topic'] == 'Easements'
        assert properties['Stage'] == 'MK1'
        assert properties['Version'] == 1

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_calls_drive_with_correct_params(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        mock_drive_client
    ):
        """Test that Drive client is called with correct parameters"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        generation_id = sample_data['generation'].id
        response_content = "Test content"

        service.process_response(
            generation_id=generation_id,
            response_content=response_content,
            notion_database_id="db-123"
        )

        # Verify folder structure was created
        assert mock_drive_client.get_or_create_folder.call_count == 3
        calls = mock_drive_client.get_or_create_folder.call_args_list

        # First call: root folder
        assert calls[0][0][0] == 'LawFlow'

        # Second call: module folder
        assert calls[1][0][0] == 'Land Law'

        # Third call: topic folder
        assert calls[2][0][0] == 'Easements'

        # Verify file upload
        mock_drive_client.upload_file.assert_called_once()
        upload_args = mock_drive_client.upload_file.call_args[1]
        assert upload_args['file_name'] == 'MK1_v1.md'
        assert upload_args['mime_type'] == 'text/markdown'
        assert b'Test content' == upload_args['file_content']

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_commits_transaction(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        test_db_conn
    ):
        """Test that database transaction is committed on success"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        # Process the response
        result = service.process_response(
            generation_id=sample_data['generation'].id,
            response_content="Test",
            notion_database_id="db-123"
        )

        # Verify the generation was marked as completed (which requires a commit)
        gen_repo = GenerationRepository(test_db_conn)
        updated_gen = gen_repo.get_by_id(sample_data['generation'].id)
        assert updated_gen.status == GenerationStatus.COMPLETED
        assert result is not None

    # ==================== ERROR HANDLING TESTS ====================

    def test_process_response_generation_not_found(self, service):
        """Test error when generation ID doesn't exist"""
        with pytest.raises(ValueError, match="Generation not found"):
            service.process_response(
                generation_id="non-existent-id",
                response_content="Test",
                notion_database_id="db-123"
            )

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_already_completed(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        test_db_conn
    ):
        """Test error when trying to process an already completed generation"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        # Mark generation as completed
        gen_repo = GenerationRepository(test_db_conn)
        generation = sample_data['generation']
        generation.status = GenerationStatus.COMPLETED
        gen_repo.update(generation)

        # Try to process again
        with pytest.raises(ValueError, match="already completed"):
            service.process_response(
                generation_id=generation.id,
                response_content="Test",
                notion_database_id="db-123"
            )

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_notion_failure_triggers_rollback(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        test_db_conn,
        mock_notion_client,
        mock_drive_client
    ):
        """Test that Notion failure triggers rollback"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        # Make Notion create_page fail
        mock_notion_client.create_page.side_effect = Exception("Notion API error")

        # Store original generation ID
        generation_id = sample_data['generation'].id

        # Process should raise exception
        with pytest.raises(Exception, match="Failed to process response"):
            service.process_response(
                generation_id=generation_id,
                response_content="Test",
                notion_database_id="db-123"
            )

        # Verify Drive client was NOT called (failure happened before Drive)
        mock_drive_client.upload_file.assert_not_called()

        # Verify generation exists and is marked as FAILED
        # The service commits the FAILED status separately after rollback
        gen_repo = GenerationRepository(test_db_conn)
        failed_gen = gen_repo.get_by_id(generation_id)
        assert failed_gen is not None, "Generation should still exist after failure"
        assert failed_gen.status == GenerationStatus.FAILED, "Generation should be marked as FAILED"

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_drive_failure_triggers_rollback(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        test_db_conn,
        mock_notion_client,
        mock_drive_client
    ):
        """Test that Drive failure triggers rollback including Notion page deletion"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        # Notion succeeds, but Drive fails
        mock_drive_client.upload_file.side_effect = Exception("Drive API error")

        # Store generation ID
        generation_id = sample_data['generation'].id

        # Process should raise exception
        with pytest.raises(Exception, match="Failed to process response"):
            service.process_response(
                generation_id=generation_id,
                response_content="Test",
                notion_database_id="db-123"
            )

        # Verify Notion page was archived (rollback)
        mock_notion_client.client.pages.update.assert_called_once_with(
            page_id='notion-page-123',
            archived=True
        )

        # Verify generation status is FAILED (separate commit after rollback)
        gen_repo = GenerationRepository(test_db_conn)
        failed_gen = gen_repo.get_by_id(generation_id)
        assert failed_gen is not None, "Generation should still exist after failure"
        assert failed_gen.status == GenerationStatus.FAILED, "Generation should be marked as FAILED"

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_rollback_handles_notion_deletion_failure_gracefully(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        mock_notion_client,
        mock_drive_client
    ):
        """Test that rollback continues even if Notion deletion fails"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        # Drive upload fails
        mock_drive_client.upload_file.side_effect = Exception("Drive error")

        # Make Notion rollback also fail
        mock_notion_client.client.pages.update.side_effect = Exception("Notion delete error")

        # Should still raise the original Drive error, not the rollback error
        with pytest.raises(Exception, match="Failed to process response"):
            service.process_response(
                generation_id=sample_data['generation'].id,
                response_content="Test",
                notion_database_id="db-123"
            )

        # Both should have been attempted
        mock_notion_client.client.pages.update.assert_called_once()

    @patch('services.output_service.markdown_to_notion_blocks')
    def test_process_response_markdown_conversion_failure(
        self,
        mock_markdown_to_blocks,
        service,
        sample_data
    ):
        """Test error handling when markdown conversion fails"""
        # Make markdown conversion fail
        mock_markdown_to_blocks.side_effect = Exception("Invalid markdown")

        with pytest.raises(Exception, match="Failed to process response"):
            service.process_response(
                generation_id=sample_data['generation'].id,
                response_content="Bad markdown",
                notion_database_id="db-123"
            )

    # ==================== DATABASE TRANSACTION TESTS ====================

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_rollback_on_failure(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        test_db_conn
    ):
        """Test that database changes are rolled back on failure"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        # Make Drive upload fail after Notion succeeds
        service.drive_client.upload_file.side_effect = Exception("Drive error")

        # Store generation ID
        generation_id = sample_data['generation'].id

        # Process should raise exception
        with pytest.raises(Exception, match="Failed to process response"):
            service.process_response(
                generation_id=generation_id,
                response_content="Test",
                notion_database_id="db-123"
            )

        # Verify the generation was marked as FAILED after rollback
        gen_repo = GenerationRepository(test_db_conn)
        failed_gen = gen_repo.get_by_id(generation_id)
        assert failed_gen is not None, "Generation should still exist after failure"
        assert failed_gen.status == GenerationStatus.FAILED, "Generation should be marked as FAILED"

    # ==================== EDGE CASES ====================

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_with_mk2_stage(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        test_db_conn,
        mock_drive_client
    ):
        """Test processing response for MK2 stage"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        # Create MK2 generation
        module = Module.create(name="Tort Law")
        module_repo = ModuleRepository(test_db_conn)
        created_module = module_repo.create(module)

        topic = Topic.create(module_id=created_module.id, name="Negligence")
        topic_repo = TopicRepository(test_db_conn)
        created_topic = topic_repo.create(topic)

        generation = Generation.create(
            topic_id=created_topic.id,
            stage=Stage.MK2,
            version=1,
            prompt_used="MK2 prompt"
        )
        gen_repo = GenerationRepository(test_db_conn)
        created_gen = gen_repo.create(generation)

        # Process
        result = service.process_response(
            generation_id=created_gen.id,
            response_content="MK2 content",
            notion_database_id="db-123"
        )

        # Verify Drive filename includes MK2
        upload_call = mock_drive_client.upload_file.call_args[1]
        assert upload_call['file_name'] == 'MK2_v1.md'

        assert result['generation_id'] == created_gen.id

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_with_version_2(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data,
        test_db_conn,
        mock_drive_client
    ):
        """Test processing response for version 2 of a generation"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        # Create version 2 generation
        generation_v2 = Generation.create(
            topic_id=sample_data['topic'].id,
            stage=Stage.MK1,
            version=2,
            prompt_used="Version 2 prompt"
        )
        gen_repo = GenerationRepository(test_db_conn)
        created_gen_v2 = gen_repo.create(generation_v2)

        # Process
        service.process_response(
            generation_id=created_gen_v2.id,
            response_content="Version 2 content",
            notion_database_id="db-123"
        )

        # Verify Drive filename includes version 2
        upload_call = mock_drive_client.upload_file.call_args[1]
        assert upload_call['file_name'] == 'MK1_v2.md'

    @patch('services.output_service.markdown_to_notion_blocks')
    @patch('services.output_service.validate_blocks')
    def test_process_response_with_unicode_content(
        self,
        mock_validate_blocks,
        mock_markdown_to_blocks,
        service,
        sample_data
    ):
        """Test processing response with unicode characters"""
        mock_blocks = [{'type': 'paragraph'}]
        mock_markdown_to_blocks.return_value = mock_blocks
        mock_validate_blocks.return_value = mock_blocks

        unicode_content = "# Notes\n\nLegal symbols: § © ® \n\nUnicode: 你好 🏛️"

        result = service.process_response(
            generation_id=sample_data['generation'].id,
            response_content=unicode_content,
            notion_database_id="db-123"
        )

        assert result['generation_id'] == sample_data['generation'].id

    def test_process_response_topic_not_found(self, service, test_db_conn):
        """Test error when topic is deleted but generation exists"""
        # Create a generation with invalid topic_id
        generation = Generation.create(
            topic_id="non-existent-topic",
            stage=Stage.MK1,
            version=1,
            prompt_used="Test"
        )
        gen_repo = GenerationRepository(test_db_conn)
        created_gen = gen_repo.create(generation)

        with pytest.raises(ValueError, match="Topic not found"):
            service.process_response(
                generation_id=created_gen.id,
                response_content="Test",
                notion_database_id="db-123"
            )
