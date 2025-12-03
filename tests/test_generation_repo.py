"""
Unit tests for GenerationRepository.

Tests CRUD operations, query methods, and version management
for the generations table.
"""
import pytest
from database.repositories.generation_repo import GenerationRepository
from database.models import Generation, Stage, GenerationStatus


class TestGenerationRepository:
    """Test suite for GenerationRepository"""

    @pytest.fixture
    def repo(self, test_db_conn):
        """Create a GenerationRepository instance with test database"""
        return GenerationRepository(test_db_conn)

    @pytest.fixture
    def sample_generation(self):
        """Create a sample generation object"""
        return Generation.create(
            topic_id="topic-123",
            stage=Stage.MK1,
            version=1,
            prompt_used="Test prompt for MK1"
        )

    # ==================== CREATE TESTS ====================

    def test_create_generation(self, repo, sample_generation):
        """Test creating a new generation"""
        created = repo.create(sample_generation)

        assert created.id == sample_generation.id
        assert created.topic_id == sample_generation.topic_id
        assert created.stage == Stage.MK1
        assert created.version == 1
        assert created.status == GenerationStatus.PENDING
        assert created.prompt_used == "Test prompt for MK1"
        assert created.response_content is None

    def test_create_with_all_fields(self, repo):
        """Test creating a generation with all optional fields populated"""
        gen = Generation.create(
            topic_id="topic-456",
            stage=Stage.MK2,
            version=2,
            prompt_used="Full prompt",
            previous_generation_id="prev-gen-789"
        )
        gen.response_content = "Generated content"
        gen.notion_page_id = "notion-123"
        gen.notion_url = "https://notion.so/page-123"
        gen.drive_backup_id = "drive-456"
        gen.drive_backup_url = "https://drive.google.com/file/456"
        gen.status = GenerationStatus.COMPLETED

        created = repo.create(gen)

        assert created.response_content == "Generated content"
        assert created.notion_page_id == "notion-123"
        assert created.notion_url == "https://notion.so/page-123"
        assert created.drive_backup_id == "drive-456"
        assert created.drive_backup_url == "https://drive.google.com/file/456"
        assert created.previous_generation_id == "prev-gen-789"
        assert created.status == GenerationStatus.COMPLETED

    # ==================== READ TESTS ====================

    def test_get_by_id_found(self, repo, sample_generation):
        """Test retrieving a generation by ID when it exists"""
        created = repo.create(sample_generation)
        retrieved = repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.topic_id == created.topic_id
        assert retrieved.stage == Stage.MK1

    def test_get_by_id_not_found(self, repo):
        """Test retrieving a generation by ID when it doesn't exist"""
        result = repo.get_by_id("non-existent-id")
        assert result is None

    def test_get_for_topic_empty(self, repo):
        """Test getting generations for a topic with none"""
        results = repo.get_for_topic("topic-no-gens")
        assert results == []

    def test_get_for_topic_multiple(self, repo):
        """Test getting all generations for a topic with multiple generations"""
        topic_id = "topic-multi"

        # Create 3 generations for the same topic
        gen1 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=1, prompt_used="Prompt 1")
        gen2 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=2, prompt_used="Prompt 2")
        gen3 = Generation.create(topic_id=topic_id, stage=Stage.MK2, version=1, prompt_used="Prompt 3")

        repo.create(gen1)
        repo.create(gen2)
        repo.create(gen3)

        results = repo.get_for_topic(topic_id)

        assert len(results) == 3
        # Should be ordered by created_at DESC (newest first)
        assert results[0].version >= results[1].version or results[0].stage != results[1].stage

    def test_get_for_topic_isolation(self, repo):
        """Test that get_for_topic only returns generations for the specified topic"""
        topic1 = "topic-isolated-1"
        topic2 = "topic-isolated-2"

        gen1 = Generation.create(topic_id=topic1, stage=Stage.MK1, version=1, prompt_used="Topic 1 Gen")
        gen2 = Generation.create(topic_id=topic2, stage=Stage.MK1, version=1, prompt_used="Topic 2 Gen")

        repo.create(gen1)
        repo.create(gen2)

        results = repo.get_for_topic(topic1)

        assert len(results) == 1
        assert results[0].topic_id == topic1

    def test_get_by_stage_empty(self, repo):
        """Test getting generations by stage when none exist"""
        results = repo.get_by_stage("topic-no-stage", Stage.MK1)
        assert results == []

    def test_get_by_stage_multiple_versions(self, repo):
        """Test getting all versions of a specific stage"""
        topic_id = "topic-stage-test"

        # Create multiple versions of MK1 and one MK2
        mk1_v1 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=1, prompt_used="MK1 v1")
        mk1_v2 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=2, prompt_used="MK1 v2")
        mk1_v3 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=3, prompt_used="MK1 v3")
        mk2_v1 = Generation.create(topic_id=topic_id, stage=Stage.MK2, version=1, prompt_used="MK2 v1")

        repo.create(mk1_v1)
        repo.create(mk1_v2)
        repo.create(mk1_v3)
        repo.create(mk2_v1)

        results = repo.get_by_stage(topic_id, Stage.MK1)

        assert len(results) == 3
        assert all(g.stage == Stage.MK1 for g in results)
        # Should be ordered by version DESC (newest first)
        assert results[0].version == 3
        assert results[1].version == 2
        assert results[2].version == 1

    def test_get_latest_version_found(self, repo):
        """Test getting the latest version for a stage"""
        topic_id = "topic-latest"

        # Create multiple versions
        gen1 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=1, prompt_used="v1")
        gen2 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=2, prompt_used="v2")
        gen3 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=3, prompt_used="v3")

        repo.create(gen1)
        repo.create(gen2)
        repo.create(gen3)

        latest = repo.get_latest_version(topic_id, Stage.MK1)

        assert latest is not None
        assert latest.version == 3
        assert latest.prompt_used == "v3"

    def test_get_latest_version_not_found(self, repo):
        """Test getting latest version when none exist"""
        latest = repo.get_latest_version("topic-none", Stage.MK1)
        assert latest is None

    def test_get_completed_for_stage_only_completed(self, repo):
        """Test that get_completed_for_stage only returns completed generations"""
        topic_id = "topic-completed"

        # Create generations with different statuses
        completed1 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=1, prompt_used="c1")
        completed1.status = GenerationStatus.COMPLETED
        completed2 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=2, prompt_used="c2")
        completed2.status = GenerationStatus.COMPLETED
        pending = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=3, prompt_used="p")
        pending.status = GenerationStatus.PENDING
        failed = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=4, prompt_used="f")
        failed.status = GenerationStatus.FAILED

        repo.create(completed1)
        repo.create(completed2)
        repo.create(pending)
        repo.create(failed)

        results = repo.get_completed_for_stage(topic_id, Stage.MK1)

        assert len(results) == 2
        assert all(g.status == GenerationStatus.COMPLETED for g in results)

    def test_get_completed_for_stage_empty(self, repo):
        """Test get_completed_for_stage when no completed generations exist"""
        topic_id = "topic-no-completed"

        pending = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=1, prompt_used="p")
        repo.create(pending)

        results = repo.get_completed_for_stage(topic_id, Stage.MK1)
        assert results == []

    # ==================== VERSION TESTS ====================

    def test_get_next_version_no_existing(self, repo):
        """Test getting next version when no generations exist"""
        next_version = repo.get_next_version("topic-new", Stage.MK1)
        assert next_version == 1

    def test_get_next_version_with_existing(self, repo):
        """Test getting next version when generations exist"""
        topic_id = "topic-versioned"

        gen1 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=1, prompt_used="v1")
        gen2 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=2, prompt_used="v2")

        repo.create(gen1)
        repo.create(gen2)

        next_version = repo.get_next_version(topic_id, Stage.MK1)
        assert next_version == 3

    def test_get_next_version_stage_isolation(self, repo):
        """Test that version counting is isolated per stage"""
        topic_id = "topic-stage-versions"

        # Create MK1 versions 1 and 2
        mk1_v1 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=1, prompt_used="mk1")
        mk1_v2 = Generation.create(topic_id=topic_id, stage=Stage.MK1, version=2, prompt_used="mk1")

        repo.create(mk1_v1)
        repo.create(mk1_v2)

        # MK2 should start at version 1
        next_mk2_version = repo.get_next_version(topic_id, Stage.MK2)
        assert next_mk2_version == 1

        # MK1 should be version 3
        next_mk1_version = repo.get_next_version(topic_id, Stage.MK1)
        assert next_mk1_version == 3

    # ==================== UPDATE TESTS ====================

    def test_update_generation(self, repo, sample_generation):
        """Test updating a generation's fields"""
        created = repo.create(sample_generation)

        # Update fields
        created.response_content = "Updated response"
        created.notion_page_id = "notion-updated"
        created.notion_url = "https://notion.so/updated"
        created.drive_backup_id = "drive-updated"
        created.drive_backup_url = "https://drive.google.com/updated"
        created.status = GenerationStatus.COMPLETED

        updated = repo.update(created)

        # Verify update worked
        assert updated.response_content == "Updated response"
        assert updated.status == GenerationStatus.COMPLETED

        # Verify in database
        retrieved = repo.get_by_id(created.id)
        assert retrieved.response_content == "Updated response"
        assert retrieved.notion_page_id == "notion-updated"
        assert retrieved.status == GenerationStatus.COMPLETED

    def test_update_status_only(self, repo, sample_generation):
        """Test updating just the status field"""
        created = repo.create(sample_generation)

        created.status = GenerationStatus.FAILED
        repo.update(created)

        retrieved = repo.get_by_id(created.id)
        assert retrieved.status == GenerationStatus.FAILED

    # ==================== DELETE TESTS ====================

    def test_delete_existing(self, repo, sample_generation):
        """Test hard deleting a generation"""
        created = repo.create(sample_generation)
        gen_id = created.id

        # Delete
        result = repo.delete(gen_id)
        assert result is True

        # Verify it's gone
        retrieved = repo.get_by_id(gen_id)
        assert retrieved is None

    def test_delete_non_existing(self, repo):
        """Test deleting a generation that doesn't exist"""
        result = repo.delete("non-existent-id")
        assert result is False

    # ==================== EDGE CASES ====================

    def test_multiple_topics_isolated(self, repo):
        """Test that operations are properly isolated between topics"""
        topic1 = "topic-isolation-1"
        topic2 = "topic-isolation-2"

        # Create generations for both topics
        gen1 = Generation.create(topic_id=topic1, stage=Stage.MK1, version=1, prompt_used="t1")
        gen2 = Generation.create(topic_id=topic2, stage=Stage.MK1, version=1, prompt_used="t2")

        repo.create(gen1)
        repo.create(gen2)

        # Test isolation
        topic1_gens = repo.get_for_topic(topic1)
        topic2_gens = repo.get_for_topic(topic2)

        assert len(topic1_gens) == 1
        assert len(topic2_gens) == 1
        assert topic1_gens[0].topic_id == topic1
        assert topic2_gens[0].topic_id == topic2

    def test_mk3_with_previous_generation_reference(self, repo):
        """Test creating MK3 with reference to previous MK2"""
        topic_id = "topic-mk3"

        # Create MK2
        mk2 = Generation.create(topic_id=topic_id, stage=Stage.MK2, version=1, prompt_used="MK2")
        mk2.status = GenerationStatus.COMPLETED
        repo.create(mk2)

        # Create MK3 referencing MK2
        mk3 = Generation.create(
            topic_id=topic_id,
            stage=Stage.MK3,
            version=1,
            prompt_used="MK3",
            previous_generation_id=mk2.id
        )
        repo.create(mk3)

        # Verify reference
        retrieved_mk3 = repo.get_by_id(mk3.id)
        assert retrieved_mk3.previous_generation_id == mk2.id

    def test_enum_serialization(self, repo):
        """Test that Stage and GenerationStatus enums are properly serialized/deserialized"""
        gen = Generation.create(
            topic_id="topic-enum",
            stage=Stage.MK2,
            version=1,
            prompt_used="Test"
        )
        gen.status = GenerationStatus.FAILED

        created = repo.create(gen)
        retrieved = repo.get_by_id(created.id)

        # Verify enums are proper enum objects, not strings
        assert isinstance(retrieved.stage, Stage)
        assert isinstance(retrieved.status, GenerationStatus)
        assert retrieved.stage == Stage.MK2
        assert retrieved.status == GenerationStatus.FAILED
