"""
Unit tests for GenerationService.

Tests the core generation orchestration logic including:
- Stage unlock requirements validation
- Prompt generation workflow
- Generation history tracking
"""
import pytest
from database.models import (
    Module, Topic, ContentItem, Generation,
    ContentType, Stage, GenerationStatus
)
from database.repositories.module_repo import ModuleRepository
from database.repositories.topic_repo import TopicRepository
from database.repositories.content_repo import ContentRepository
from database.repositories.generation_repo import GenerationRepository
from services.generation_service import GenerationService


class TestGenerationService:
    """Test suite for GenerationService"""

    @pytest.fixture
    def service(self, test_db_conn):
        """Create a GenerationService instance with test database"""
        return GenerationService(test_db_conn)

    @pytest.fixture
    def sample_module(self, test_db_conn):
        """Create a test module"""
        module = Module.create(name="Land Law", claude_project_name="land-law")
        repo = ModuleRepository(test_db_conn)
        return repo.create(module)

    @pytest.fixture
    def sample_topic(self, test_db_conn, sample_module):
        """Create a test topic"""
        topic = Topic.create(module_id=sample_module.id, name="Easements")
        repo = TopicRepository(test_db_conn)
        return repo.create(topic)

    def test_can_generate_mk1_with_lecture_pdf(self, service, sample_topic, test_db_conn):
        """Test MK1 can be generated when LECTURE_PDF is uploaded"""
        # Upload LECTURE_PDF
        content = ContentItem.create(
            topic_id=sample_topic.id,
            content_type=ContentType.LECTURE_PDF,
            file_name="lecture.pdf",
            file_size_bytes=1024
        )
        ContentRepository(test_db_conn).create(content)

        # Check requirements
        can_generate, missing = service.can_generate_stage(sample_topic.id, Stage.MK1)

        assert can_generate is True
        assert missing == []

    def test_cannot_generate_mk1_without_lecture_pdf(self, service, sample_topic):
        """Test MK1 cannot be generated without LECTURE_PDF"""
        can_generate, missing = service.can_generate_stage(sample_topic.id, Stage.MK1)

        assert can_generate is False
        assert "Missing Lecture Pdf" in missing

    def test_can_generate_mk2_with_all_requirements(self, service, sample_topic, test_db_conn):
        """Test MK2 can be generated when all required files are uploaded"""
        # Upload all required files
        required_types = [
            ContentType.LECTURE_PDF,
            ContentType.SOURCE_MATERIAL,
            ContentType.TUTORIAL_PDF
        ]

        for content_type in required_types:
            content = ContentItem.create(
                topic_id=sample_topic.id,
                content_type=content_type,
                file_name=f"{content_type.value.lower()}.pdf",
                file_size_bytes=1024
            )
            ContentRepository(test_db_conn).create(content)

        # Check requirements
        can_generate, missing = service.can_generate_stage(sample_topic.id, Stage.MK2)

        assert can_generate is True
        assert missing == []

    def test_cannot_generate_mk2_without_source_material(self, service, sample_topic, test_db_conn):
        """Test MK2 cannot be generated without SOURCE_MATERIAL"""
        # Upload only LECTURE_PDF and TUTORIAL_PDF (missing SOURCE_MATERIAL)
        for content_type in [ContentType.LECTURE_PDF, ContentType.TUTORIAL_PDF]:
            content = ContentItem.create(
                topic_id=sample_topic.id,
                content_type=content_type,
                file_name=f"{content_type.value.lower()}.pdf",
                file_size_bytes=1024
            )
            ContentRepository(test_db_conn).create(content)

        can_generate, missing = service.can_generate_stage(sample_topic.id, Stage.MK2)

        assert can_generate is False
        assert "Missing Source Material" in missing

    def test_cannot_generate_mk3_without_completed_mk2(self, service, sample_topic, test_db_conn):
        """Test MK3 cannot be generated without a completed MK2 generation"""
        # Upload all required files including TRANSCRIPT
        required_types = [
            ContentType.LECTURE_PDF,
            ContentType.SOURCE_MATERIAL,
            ContentType.TUTORIAL_PDF,
            ContentType.TRANSCRIPT
        ]

        for content_type in required_types:
            content = ContentItem.create(
                topic_id=sample_topic.id,
                content_type=content_type,
                file_name=f"{content_type.value.lower()}.pdf",
                file_size_bytes=1024
            )
            ContentRepository(test_db_conn).create(content)

        # Check requirements (should fail due to missing MK2)
        can_generate, missing = service.can_generate_stage(sample_topic.id, Stage.MK3)

        assert can_generate is False
        assert "Missing completed MK2 generation" in missing

    def test_can_generate_mk3_with_completed_mk2(self, service, sample_topic, test_db_conn):
        """Test MK3 can be generated when MK2 is completed"""
        # Upload all required files
        required_types = [
            ContentType.LECTURE_PDF,
            ContentType.SOURCE_MATERIAL,
            ContentType.TUTORIAL_PDF,
            ContentType.TRANSCRIPT
        ]

        for content_type in required_types:
            content = ContentItem.create(
                topic_id=sample_topic.id,
                content_type=content_type,
                file_name=f"{content_type.value.lower()}.pdf",
                file_size_bytes=1024
            )
            ContentRepository(test_db_conn).create(content)

        # Create a completed MK2 generation
        mk2_gen = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK2,
            version=1,
            prompt_used="Test prompt"
        )
        mk2_gen.response_content = "Test MK2 response content"
        mk2_gen.status = GenerationStatus.COMPLETED
        GenerationRepository(test_db_conn).create(mk2_gen)

        # Check requirements
        can_generate, missing = service.can_generate_stage(sample_topic.id, Stage.MK3)

        assert can_generate is True
        assert missing == []

    def test_start_generation_creates_pending_record(self, service, sample_topic, test_db_conn):
        """Test that start_generation creates a pending Generation record"""
        # Upload LECTURE_PDF
        content = ContentItem.create(
            topic_id=sample_topic.id,
            content_type=ContentType.LECTURE_PDF,
            file_name="lecture.pdf",
            file_size_bytes=1024
        )
        ContentRepository(test_db_conn).create(content)

        # Start generation
        generation = service.start_generation(sample_topic.id, Stage.MK1)

        assert generation is not None
        assert generation.topic_id == sample_topic.id
        assert generation.stage == Stage.MK1
        assert generation.version == 1
        assert generation.status == GenerationStatus.PENDING
        assert generation.prompt_used is not None
        assert len(generation.prompt_used) > 0
        assert generation.response_content is None

    def test_start_generation_increments_version(self, service, sample_topic, test_db_conn):
        """Test that subsequent generations increment version number"""
        # Upload LECTURE_PDF
        content = ContentItem.create(
            topic_id=sample_topic.id,
            content_type=ContentType.LECTURE_PDF,
            file_name="lecture.pdf",
            file_size_bytes=1024
        )
        ContentRepository(test_db_conn).create(content)

        # Create first generation
        gen1 = service.start_generation(sample_topic.id, Stage.MK1)
        assert gen1.version == 1

        # Create second generation
        gen2 = service.start_generation(sample_topic.id, Stage.MK1)
        assert gen2.version == 2

    def test_start_generation_fails_without_requirements(self, service, sample_topic):
        """Test that start_generation raises error when requirements not met"""
        with pytest.raises(ValueError, match="Missing requirements"):
            service.start_generation(sample_topic.id, Stage.MK1)

    def test_start_generation_mk3_includes_mk2_content(self, service, sample_topic, test_db_conn):
        """Test that MK3 generation includes MK2 content as previous_content"""
        # Upload all required files
        required_types = [
            ContentType.LECTURE_PDF,
            ContentType.SOURCE_MATERIAL,
            ContentType.TUTORIAL_PDF,
            ContentType.TRANSCRIPT
        ]

        for content_type in required_types:
            content = ContentItem.create(
                topic_id=sample_topic.id,
                content_type=content_type,
                file_name=f"{content_type.value.lower()}.pdf",
                file_size_bytes=1024
            )
            ContentRepository(test_db_conn).create(content)

        # Create completed MK2
        mk2_gen = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK2,
            version=1,
            prompt_used="MK2 prompt"
        )
        mk2_gen.response_content = "MK2 detailed notes content"
        mk2_gen.status = GenerationStatus.COMPLETED
        GenerationRepository(test_db_conn).create(mk2_gen)

        # Start MK3 generation
        mk3_gen = service.start_generation(sample_topic.id, Stage.MK3)

        # Verify MK3 references MK2
        assert mk3_gen.previous_generation_id == mk2_gen.id
        assert "MK2 detailed notes content" in mk3_gen.prompt_used

    def test_get_generation_history(self, service, sample_topic, test_db_conn):
        """Test getting generation history for a topic"""
        # Create multiple generations
        gen1 = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK1,
            version=1,
            prompt_used="Prompt 1"
        )
        gen2 = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK1,
            version=2,
            prompt_used="Prompt 2"
        )
        gen3 = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK2,
            version=1,
            prompt_used="Prompt 3"
        )

        repo = GenerationRepository(test_db_conn)
        repo.create(gen1)
        repo.create(gen2)
        repo.create(gen3)

        # Get all history
        all_history = service.get_generation_history(sample_topic.id)
        assert len(all_history) == 3

        # Get MK1 only
        mk1_history = service.get_generation_history(sample_topic.id, Stage.MK1)
        assert len(mk1_history) == 2
        assert all(g.stage == Stage.MK1 for g in mk1_history)

    def test_update_generation_response(self, service, sample_topic, test_db_conn):
        """Test updating generation with Claude's response"""
        # Create a pending generation
        generation = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK1,
            version=1,
            prompt_used="Test prompt"
        )
        repo = GenerationRepository(test_db_conn)
        created = repo.create(generation)

        # Update with response
        response_content = "This is Claude's response with notes"
        updated = service.update_generation_response(created.id, response_content)

        assert updated.response_content == response_content
        assert updated.status == GenerationStatus.COMPLETED

    def test_mark_generation_failed(self, service, sample_topic, test_db_conn):
        """Test marking a generation as failed"""
        # Create a pending generation
        generation = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK1,
            version=1,
            prompt_used="Test prompt"
        )
        repo = GenerationRepository(test_db_conn)
        created = repo.create(generation)

        # Mark as failed
        failed = service.mark_generation_failed(created.id)

        assert failed.status == GenerationStatus.FAILED

    def test_get_latest_completed_generation(self, service, sample_topic, test_db_conn):
        """Test getting the latest completed generation"""
        repo = GenerationRepository(test_db_conn)

        # Create multiple generations
        gen1 = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK1,
            version=1,
            prompt_used="Prompt 1"
        )
        gen1.status = GenerationStatus.COMPLETED
        repo.create(gen1)

        gen2 = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK1,
            version=2,
            prompt_used="Prompt 2"
        )
        gen2.status = GenerationStatus.COMPLETED
        repo.create(gen2)

        gen3 = Generation.create(
            topic_id=sample_topic.id,
            stage=Stage.MK1,
            version=3,
            prompt_used="Prompt 3"
        )
        gen3.status = GenerationStatus.PENDING
        repo.create(gen3)

        # Get latest completed
        latest = service.get_latest_completed_generation(sample_topic.id, Stage.MK1)

        assert latest is not None
        assert latest.version == 2  # gen2, not gen3 (which is pending)
        assert latest.status == GenerationStatus.COMPLETED
