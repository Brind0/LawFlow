import sqlite3
from typing import List, Tuple, Optional
from database.models import Generation, Stage, ContentType, GenerationStatus
from database.repositories.generation_repo import GenerationRepository
from database.repositories.content_repo import ContentRepository
from database.repositories.topic_repo import TopicRepository
from database.repositories.module_repo import ModuleRepository
from services.prompt_service import PromptService


class GenerationService:
    """
    Service layer for managing AI generation workflows.
    Orchestrates stage unlock logic, prompt generation, and generation records.

    This is a human-in-the-loop system - the service validates requirements,
    builds prompts, and creates pending records. Users manually copy-paste
    prompts to Claude and paste responses back.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize the service with database connection.

        Args:
            conn: Active SQLite database connection
        """
        self.conn = conn
        self.generation_repo = GenerationRepository(conn)
        self.content_repo = ContentRepository(conn)
        self.topic_repo = TopicRepository(conn)
        self.module_repo = ModuleRepository(conn)
        self.prompt_service = PromptService()

    def can_generate_stage(self, topic_id: str, stage: Stage) -> Tuple[bool, List[str]]:
        """
        Check if a topic meets all requirements to generate a specific stage.

        Requirements:
        - MK1: LECTURE_PDF must be uploaded
        - MK2: LECTURE_PDF, SOURCE_MATERIAL, TUTORIAL_PDF must be uploaded
        - MK3: All MK2 requirements + TRANSCRIPT + completed MK2 generation

        Args:
            topic_id: UUID of the topic to check
            stage: The generation stage to validate

        Returns:
            Tuple of (can_generate: bool, missing_requirements: List[str])
            If can_generate is True, missing_requirements will be empty.
            If False, missing_requirements contains human-readable error messages.

        Example:
            can_gen, missing = service.can_generate_stage(topic_id, Stage.MK2)
            if not can_gen:
                print(f"Cannot generate: {', '.join(missing)}")
        """
        missing_requirements = []

        # Get required file types for this stage
        required_files = self.prompt_service.get_required_files_for_stage(stage)

        # Get all uploaded content for the topic
        uploaded_content = self.content_repo.get_for_topic(topic_id)
        uploaded_types = {item.content_type for item in uploaded_content}

        # Check for missing file types
        for required_type in required_files:
            if required_type not in uploaded_types:
                # Convert enum to human-readable format
                type_name = required_type.value.replace('_', ' ').title()
                missing_requirements.append(f"Missing {type_name}")

        # MK3 has additional requirement: completed MK2 generation
        if stage == Stage.MK3:
            completed_mk2 = self.generation_repo.get_completed_for_stage(topic_id, Stage.MK2)
            if not completed_mk2:
                missing_requirements.append("Missing completed MK2 generation")

        # Return success if no missing requirements
        can_generate = len(missing_requirements) == 0
        return can_generate, missing_requirements

    def start_generation(self, topic_id: str, stage: Stage) -> Generation:
        """
        Start a new generation for a topic at a specific stage.

        This method:
        1. Validates all requirements are met
        2. Fetches topic and module information
        3. Fetches content file names
        4. For MK3: Fetches MK2 generation response content
        5. Builds the prompt using PromptService
        6. Creates a pending Generation record
        7. Returns the Generation object with prompt ready to copy

        Args:
            topic_id: UUID of the topic to generate for
            stage: The generation stage (MK1, MK2, or MK3)

        Returns:
            Generation object with status=PENDING and prompt_used populated

        Raises:
            ValueError: If requirements are not met or topic/module not found

        Example:
            try:
                gen = service.start_generation(topic_id, Stage.MK1)
                print(f"Copy this prompt:\\n{gen.prompt_used}")
            except ValueError as e:
                print(f"Error: {e}")
        """
        # 1. Validate requirements
        can_generate, missing = self.can_generate_stage(topic_id, stage)
        if not can_generate:
            raise ValueError(
                f"Cannot generate {stage.value} for topic. "
                f"Missing requirements: {', '.join(missing)}"
            )

        # 2. Fetch topic information
        topic = self.topic_repo.get_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic not found: {topic_id}")

        # 3. Fetch module information
        module = self.module_repo.get_by_id(topic.module_id)
        if not module:
            raise ValueError(f"Module not found: {topic.module_id}")

        # 4. Fetch content file names
        content_items = self.content_repo.get_for_topic(topic_id)
        file_names = [item.file_name for item in content_items]

        # 5. For MK3: Fetch MK2 generation response content
        previous_content = None
        previous_generation_id = None

        if stage == Stage.MK3:
            # Get the most recent completed MK2 generation
            completed_mk2 = self.generation_repo.get_completed_for_stage(topic_id, Stage.MK2)
            if not completed_mk2:
                # This should never happen due to validation above, but safety check
                raise ValueError("MK3 requires a completed MK2 generation")

            # Get the latest completed MK2 (list is ordered by version DESC)
            latest_mk2 = completed_mk2[0]
            previous_content = latest_mk2.response_content
            previous_generation_id = latest_mk2.id

            if not previous_content:
                raise ValueError(
                    "MK2 generation is marked as completed but has no response content"
                )

        # 6. Build the prompt
        prompt = self.prompt_service.build_prompt(
            stage=stage,
            topic_name=topic.name,
            module_name=module.name,
            file_names=file_names,
            previous_content=previous_content
        )

        # 7. Get next version number
        version = self.generation_repo.get_next_version(topic_id, stage)

        # 8. Create pending Generation record
        generation = Generation.create(
            topic_id=topic_id,
            stage=stage,
            version=version,
            prompt_used=prompt,
            previous_generation_id=previous_generation_id
        )

        # 9. Save to database
        created_generation = self.generation_repo.create(generation)

        return created_generation

    def get_generation_history(
        self,
        topic_id: str,
        stage: Optional[Stage] = None
    ) -> List[Generation]:
        """
        Get generation history for a topic, optionally filtered by stage.

        Args:
            topic_id: UUID of the topic
            stage: Optional - filter by specific stage (MK1, MK2, or MK3)

        Returns:
            List of Generation objects, ordered by creation date (newest first)

        Example:
            # Get all generations for a topic
            all_gens = service.get_generation_history(topic_id)

            # Get only MK1 generations
            mk1_gens = service.get_generation_history(topic_id, Stage.MK1)
        """
        if stage:
            return self.generation_repo.get_by_stage(topic_id, stage)
        else:
            return self.generation_repo.get_for_topic(topic_id)

    def update_generation_response(
        self,
        generation_id: str,
        response_content: str
    ) -> Generation:
        """
        Update a generation with Claude's response content.

        This marks the generation as COMPLETED and stores the response.
        Called when the user pastes back Claude's response.

        Args:
            generation_id: UUID of the generation to update
            response_content: The markdown response from Claude

        Returns:
            Updated Generation object

        Raises:
            ValueError: If generation not found

        Example:
            gen = service.update_generation_response(gen_id, claude_response)
            print(f"Generation completed: {gen.id}")
        """
        generation = self.generation_repo.get_by_id(generation_id)
        if not generation:
            raise ValueError(f"Generation not found: {generation_id}")

        # Update fields
        generation.response_content = response_content
        generation.status = GenerationStatus.COMPLETED

        # Save to database
        updated = self.generation_repo.update(generation)
        return updated

    def mark_generation_failed(
        self,
        generation_id: str
    ) -> Generation:
        """
        Mark a generation as failed.

        This allows users to mark a generation as failed if Claude's
        response was unsatisfactory or if there were issues.

        Args:
            generation_id: UUID of the generation to mark as failed

        Returns:
            Updated Generation object

        Raises:
            ValueError: If generation not found
        """
        generation = self.generation_repo.get_by_id(generation_id)
        if not generation:
            raise ValueError(f"Generation not found: {generation_id}")

        generation.status = GenerationStatus.FAILED
        updated = self.generation_repo.update(generation)
        return updated

    def get_latest_completed_generation(
        self,
        topic_id: str,
        stage: Stage
    ) -> Optional[Generation]:
        """
        Get the most recent completed generation for a topic and stage.

        Useful for fetching the "current" generation to display in the UI.

        Args:
            topic_id: UUID of the topic
            stage: The generation stage

        Returns:
            Generation object if found, None otherwise

        Example:
            current_mk2 = service.get_latest_completed_generation(
                topic_id, Stage.MK2
            )
            if current_mk2:
                print(f"Latest MK2 version: {current_mk2.version}")
        """
        completed = self.generation_repo.get_completed_for_stage(topic_id, stage)
        if completed:
            return completed[0]  # List is ordered by version DESC
        return None
