"""
Generation Modal component for LawFlow's human-in-the-loop workflow.

This modal orchestrates the complete three-step generation process:
1. Verify files are uploaded to Claude Project
2. Copy generated prompt to clipboard
3. Paste Claude's response and process to Notion/Drive

The modal handles all state management, error handling, and success feedback
for the generation workflow.
"""

import streamlit as st
import sqlite3
from typing import Optional

from database.models import Stage, GenerationStatus
from services.generation_service import GenerationService
from services.content_service import ContentService
from services.output_service import OutputService
from integrations.notion_client import NotionClient
from integrations.drive_client import DriveClient
from ui.components.clipboard import copy_to_clipboard_button, paste_from_clipboard_area
from ui.components.claude_file_checklist import render_claude_file_checklist
from config.settings import settings


def show_generation_modal(
    topic_id: str,
    stage: Stage,
    module_name: str,
    conn: sqlite3.Connection
) -> bool:
    """
    Orchestrates the complete generation workflow modal.

    This modal guides users through a three-step process:
    1. Verify Claude Project files (checklist)
    2. Copy prompt to clipboard
    3. Paste Claude's response and submit

    The modal handles:
    - Creating new generations or resuming pending ones
    - Progressive disclosure (only show next step when previous is complete)
    - Success/error feedback with actionable messages
    - Links to created Notion pages and Drive backups

    Args:
        topic_id: The topic UUID to generate for
        stage: The generation stage (MK1, MK2, or MK3)
        module_name: Module name for Claude Project reference
        conn: Active database connection

    Returns:
        True if generation completed successfully, False otherwise

    Session State Keys Used:
        - f"gen_id_{topic_id}_{stage.value}": Active generation ID
        - f"gen_success_{topic_id}_{stage.value}": Success flag
        - Individual file checkboxes in claude_file_checklist component

    Example Usage:
        In ui/pages/topic.py:
        ```
        clicked_stage = render_stage_cards(topic.id, module.name, conn)
        if clicked_stage:
            success = show_generation_modal(
                topic_id=topic.id,
                stage=clicked_stage,
                module_name=module.name,
                conn=conn
            )
            if success:
                st.balloons()
                st.rerun()
        ```
    """

    # Initialize services
    from database.repositories.topic_repo import TopicRepository
    from database.repositories.module_repo import ModuleRepository

    gen_service = GenerationService(conn)
    content_service = ContentService(conn)
    topic_repo = TopicRepository(conn)
    module_repo = ModuleRepository(conn)

    # Fetch topic and module to get notion_database_id
    topic = topic_repo.get_by_id(topic_id)
    if not topic:
        st.error(f"⚠️ Topic not found: {topic_id}")
        return False

    module = module_repo.get_by_id(topic.module_id)
    if not module:
        st.error(f"⚠️ Module not found for topic")
        return False

    # Get notion_database_id from module
    notion_database_id = module.notion_database_id

    # Validate notion_database_id is configured
    if not notion_database_id:
        st.error(f"⚠️ Notion Database ID not configured for module '{module.name}'")
        st.info("""
        **Configuration Required:**

        This module doesn't have a Notion database configured. To set it up:
        1. Create a Notion database for this module
        2. Copy the database ID from the Notion URL
        3. Update the module configuration

        For now, you can update it directly in the database or contact your administrator.
        """)
        return False

    # Session state keys for this generation
    gen_id_key = f"gen_id_{topic_id}_{stage.value}"
    success_key = f"gen_success_{topic_id}_{stage.value}"

    # Modal title
    stage_names = {
        Stage.MK1: "MK-1 Foundation",
        Stage.MK2: "MK-2 Tutorial Prep",
        Stage.MK3: "MK-3 Exam Revision"
    }
    st.markdown(f"## Generate {stage_names[stage]}")
    st.divider()

    # Check for existing pending generation or create new one
    generation_id = st.session_state.get(gen_id_key)
    generation = None

    if generation_id:
        # Try to fetch existing generation
        generation = gen_service.generation_repo.get_by_id(generation_id)

    # If no generation exists or it's completed, create a new one
    if not generation or generation.status == GenerationStatus.COMPLETED:
        try:
            generation = gen_service.start_generation(topic_id, stage)
            st.session_state[gen_id_key] = generation.id
            # Clear success flag for new generation
            if success_key in st.session_state:
                del st.session_state[success_key]
        except ValueError as e:
            st.error(f"Cannot start generation: {e}")
            return False

    # ========================================
    # STEP 1: Verify Claude Project Files
    # ========================================

    # Get content files for this topic
    content_items = content_service.get_topic_content(topic_id)
    file_names = [item.file_name for item in content_items]

    # Render file checklist
    files_confirmed = render_claude_file_checklist(module_name, file_names)

    st.divider()

    # ========================================
    # STEP 2: Copy Prompt to Clipboard
    # ========================================

    # Only show Step 2 if Step 1 is confirmed
    if files_confirmed:
        st.markdown("### Step 2: Copy Prompt to Claude")
        st.info(
            f"Copy this prompt and paste it into your **{module_name}** Claude Project chat. "
            "Claude will process the uploaded files and generate your content."
        )

        # Show prompt preview (expandable for long prompts)
        with st.expander("📄 View Full Prompt", expanded=False):
            st.text_area(
                "Prompt Preview",
                value=generation.prompt_used,
                height=300,
                disabled=True,
                key=f"prompt_preview_{generation.id}",
                label_visibility="collapsed"
            )

        # Copy button
        copy_to_clipboard_button(
            text=generation.prompt_used,
            button_label="📋 Copy Prompt to Clipboard"
        )

        st.divider()

        # ========================================
        # STEP 3: Paste Claude's Response
        # ========================================

        st.markdown("### Step 3: Paste Claude's Response")
        st.markdown(
            """
            After pasting the prompt into Claude and receiving a response:
            1. Copy Claude's **entire response** (all the markdown content)
            2. Paste it in the text area below
            3. Click "Process & Save to Notion"
            """
        )

        # Paste area
        response_content = paste_from_clipboard_area(
            key=f"response_{generation.id}"
        )

        # Submit button (only enabled if response is not empty)
        submit_disabled = not response_content or len(response_content.strip()) == 0

        # Add helpful message if button is disabled
        if submit_disabled:
            st.caption("⚠️ Paste Claude's response above to enable the submit button")

        # Process button
        if st.button(
            "Process & Save to Notion",
            type="primary",
            disabled=submit_disabled,
            key=f"submit_{generation.id}",
            use_container_width=True
        ):
            # Show loading state
            with st.spinner("Processing response and saving to Notion & Drive..."):
                try:
                    # Initialize clients
                    notion_client = NotionClient(settings.NOTION_TOKEN)
                    drive_client = DriveClient(
                        credentials_path=str(settings.GOOGLE_CREDENTIALS_PATH),
                        token_path=str(settings.GOOGLE_TOKEN_PATH)
                    )
                    drive_client.authenticate()

                    # Process the response
                    output_service = OutputService(conn, notion_client, drive_client)
                    result = output_service.process_response(
                        generation_id=generation.id,
                        response_content=response_content,
                        notion_database_id=notion_database_id
                    )

                    # Mark success in session state
                    st.session_state[success_key] = True
                    st.session_state[f"result_{generation.id}"] = result

                except Exception as e:
                    st.error(
                        f"""
                        **Failed to process response:**

                        {str(e)}

                        **Troubleshooting:**
                        - Check your Notion token is valid in settings
                        - Ensure your Google Drive credentials are configured
                        - Verify the Notion database ID is correct
                        - Check your internet connection

                        **You can try again** - your response has been saved in the text area above.
                        """
                    )
                    return False

    # ========================================
    # SUCCESS STATE
    # ========================================

    # Check if this generation completed successfully
    if st.session_state.get(success_key):
        st.divider()

        # Success banner
        st.success("✅ **Generation Complete!**")

        # Retrieve result from session state
        result = st.session_state.get(f"result_{generation.id}")

        if result:
            st.markdown(
                """
                Your content has been successfully generated and saved:
                - ✓ Converted to Notion blocks
                - ✓ Created as Notion page
                - ✓ Backed up to Google Drive
                """
            )

            # Links to Notion and Drive
            col1, col2 = st.columns(2)

            with col1:
                notion_url = result.get("notion_url")
                if notion_url:
                    st.markdown(f"### [📝 View in Notion]({notion_url})")
                else:
                    st.caption("📝 Notion URL not available")

            with col2:
                drive_url = result.get("drive_url")
                if drive_url:
                    st.markdown(f"### [📁 View in Drive]({drive_url})")
                else:
                    st.caption("📁 Drive URL not available")

        # Close button
        if st.button("Close & Refresh", type="primary", use_container_width=True):
            # Clear session state for this generation
            if gen_id_key in st.session_state:
                del st.session_state[gen_id_key]
            if success_key in st.session_state:
                del st.session_state[success_key]
            if f"result_{generation.id}" in st.session_state:
                del st.session_state[f"result_{generation.id}"]

            # Return True to signal completion
            return True

        # If success state is showing, we're effectively "done"
        return True

    # Still in progress
    return False
