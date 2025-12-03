from typing import Dict
import sqlite3
from database.repositories.generation_repo import GenerationRepository
from database.repositories.topic_repo import TopicRepository
from database.repositories.module_repo import ModuleRepository
from database.models import GenerationStatus
from integrations.notion_client import NotionClient
from integrations.drive_client import DriveClient
from integrations.markdown_converter import markdown_to_notion_blocks, validate_blocks


class OutputService:
    """
    Service layer for processing Claude's responses and saving to Notion + Drive.
    Orchestrates the multi-step process of converting markdown responses to structured
    Notion pages and Drive backups, then updating the Generation record.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        notion_client: NotionClient,
        drive_client: DriveClient
    ):
        """
        Initialize the OutputService with database connection and external clients.

        Args:
            conn: SQLite database connection
            notion_client: Initialized NotionClient instance
            drive_client: Initialized DriveClient instance
        """
        self.conn = conn
        self.notion_client = notion_client
        self.drive_client = drive_client

        # Initialize repositories
        self.generation_repo = GenerationRepository(conn)
        self.topic_repo = TopicRepository(conn)
        self.module_repo = ModuleRepository(conn)

    def process_response(
        self,
        generation_id: str,
        response_content: str,
        notion_database_id: str
    ) -> Dict[str, str]:
        """
        Processes Claude's response by saving to Notion and Drive, then updating Generation.

        This is an atomic operation - if any step fails, all changes are rolled back.

        Orchestration flow:
        1. Fetch Generation record to get topic_id, stage, version
        2. Fetch Topic and Module info for naming
        3. Convert markdown to Notion blocks
        4. Create Notion page with structured blocks
        5. Upload markdown backup to Drive
        6. Update Generation record with all URLs/IDs
        7. Mark status as COMPLETED

        Args:
            generation_id: The Generation ID (created by GenerationService.start_generation)
            response_content: The markdown text pasted from Claude
            notion_database_id: The Notion database ID to create the page in

        Returns:
            Dictionary with:
            {
                "notion_url": "https://notion.so/...",
                "drive_url": "https://drive.google.com/...",
                "generation_id": "abc-123-..."
            }

        Raises:
            ValueError: If generation not found or already completed
            Exception: If any step in the orchestration fails
        """
        # Step 1: Fetch the Generation record
        generation = self.generation_repo.get_by_id(generation_id)
        if not generation:
            raise ValueError(f"Generation not found: {generation_id}")

        if generation.status == GenerationStatus.COMPLETED:
            raise ValueError(f"Generation already completed: {generation_id}")

        # Step 2: Fetch Topic and Module info for naming
        topic = self.topic_repo.get_by_id(generation.topic_id)
        if not topic:
            raise ValueError(f"Topic not found: {generation.topic_id}")

        module = self.module_repo.get_by_id(topic.module_id)
        if not module:
            raise ValueError(f"Module not found: {topic.module_id}")

        # Prepare variables for rollback
        notion_page_id = None
        drive_file_id = None

        try:
            # Step 3: Convert markdown to Notion blocks
            blocks = markdown_to_notion_blocks(response_content)
            validated_blocks = validate_blocks(blocks)

            # Step 4: Create Notion page
            page_title = f"{module.name} - {topic.name} - {generation.stage.value}"

            notion_result = self.notion_client.create_page(
                database_id=notion_database_id,
                title=page_title,
                properties={
                    "Topic": topic.name,
                    "Stage": generation.stage.value,
                    "Version": generation.version,
                    "Status": "Current"
                },
                content_blocks=validated_blocks
            )

            notion_page_id = notion_result['id']
            notion_page_url = notion_result['url']

            # Step 5: Upload markdown backup to Drive
            # Ensure Drive folder structure exists: LawFlow/{Module}/{Topic}/
            drive_file_name = f"{generation.stage.value}_v{generation.version}.md"

            # Get or create folder structure
            from config.settings import settings
            root_id = self.drive_client.get_or_create_folder(settings.DRIVE_ROOT_FOLDER)
            module_folder_id = self.drive_client.get_or_create_folder(
                module.name,
                parent_id=root_id
            )
            topic_folder_id = self.drive_client.get_or_create_folder(
                topic.name,
                parent_id=module_folder_id
            )

            # Upload markdown content
            markdown_bytes = response_content.encode('utf-8')
            drive_result = self.drive_client.upload_file(
                file_content=markdown_bytes,
                file_name=drive_file_name,
                folder_id=topic_folder_id,
                mime_type='text/markdown'
            )

            drive_file_id = drive_result['id']
            drive_file_url = drive_result['url']

            # Step 6: Update Generation record with all IDs/URLs
            generation.response_content = response_content
            generation.notion_page_id = notion_page_id
            generation.notion_url = notion_page_url
            generation.drive_backup_id = drive_file_id
            generation.drive_backup_url = drive_file_url
            generation.status = GenerationStatus.COMPLETED

            self.generation_repo.update(generation)

            # Commit database changes
            self.conn.commit()

            # Step 7: Return the URLs dictionary
            return {
                "notion_url": notion_page_url,
                "drive_url": drive_file_url,
                "generation_id": generation_id
            }

        except Exception as e:
            # Rollback: Clean up any created resources
            self._rollback(notion_page_id, drive_file_id)

            # Rollback database changes
            self.conn.rollback()

            # Mark generation as FAILED
            try:
                generation.status = GenerationStatus.FAILED
                self.generation_repo.update(generation)
                self.conn.commit()
            except Exception:
                # If we can't even mark as failed, just let it stay PENDING
                pass

            # Re-raise the original exception with context
            raise Exception(
                f"Failed to process response for generation {generation_id}: {str(e)}"
            ) from e

    def _rollback(self, notion_page_id: str = None, drive_file_id: str = None):
        """
        Performs rollback operations by cleaning up created resources.

        Args:
            notion_page_id: Notion page ID to delete (if created)
            drive_file_id: Drive file ID to delete (if created)
        """
        # Delete Notion page if created
        if notion_page_id:
            try:
                # Notion doesn't have a delete API - we archive/trash the page
                # by moving it to trash via update with archived: true
                self.notion_client.client.pages.update(
                    page_id=notion_page_id,
                    archived=True
                )
            except Exception as e:
                # Log but don't fail - we're already in error state
                print(f"Warning: Failed to rollback Notion page {notion_page_id}: {e}")

        # Delete Drive file if created
        if drive_file_id:
            try:
                self.drive_client.delete_file(drive_file_id)
            except Exception as e:
                # Log but don't fail - we're already in error state
                print(f"Warning: Failed to rollback Drive file {drive_file_id}: {e}")
