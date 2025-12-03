import streamlit as st
import sqlite3
import humanize
from typing import Optional, List, Dict
from datetime import datetime

from database.models import Stage, ContentType, Generation
from services.generation_service import GenerationService
from services.content_service import ContentService


# Stage metadata
STAGE_METADATA = {
    Stage.MK1: {
        "name": "MK-1 Foundation",
        "description": "Initial lecture summary and extraction"
    },
    Stage.MK2: {
        "name": "MK-2 Tutorial Prep",
        "description": "Detailed structured notes with source material"
    },
    Stage.MK3: {
        "name": "MK-3 Exam Revision",
        "description": "Exam-focused questions and practice materials"
    }
}


def _determine_card_state(
    latest_generation: Optional[Generation],
    can_generate: bool
) -> str:
    """
    Determine the visual state of a stage card.

    Args:
        latest_generation: Most recent completed generation, or None
        can_generate: Whether all requirements are met

    Returns:
        One of: "generated", "ready", "locked"
    """
    if latest_generation:
        return "generated"
    elif can_generate:
        return "ready"
    else:
        return "locked"


def _render_requirements_section(
    stage: Stage,
    uploaded_content: List,
    missing_requirements: List[str]
) -> None:
    """
    Render the requirements section showing which files are uploaded.

    Args:
        stage: The generation stage
        uploaded_content: List of ContentItem objects for the topic
        missing_requirements: List of missing requirement messages
    """
    from services.prompt_service import PromptService

    prompt_service = PromptService()
    required_types = prompt_service.get_required_files_for_stage(stage)

    # Get uploaded types
    uploaded_types = {item.content_type for item in uploaded_content}

    st.markdown("**Requirements:**")

    # Check each required type
    for content_type in required_types:
        type_name = content_type.value.replace('_', ' ').title()
        has_file = content_type in uploaded_types

        if has_file:
            st.markdown(f"✓ {type_name}")
        else:
            st.markdown(f"✗ {type_name}")

    # For MK3, also check MK2 completion
    if stage == Stage.MK3:
        mk2_completed = "Missing completed MK2 generation" not in missing_requirements
        if mk2_completed:
            st.markdown("✓ MK-2 completed")
        else:
            st.markdown("✗ MK-2 completed")


def _render_locked_card(
    stage: Stage,
    topic_id: str,
    missing_requirements: List[str],
    uploaded_content: List
) -> None:
    """
    Render a locked card (gray, requirements not met).

    Args:
        stage: The generation stage
        topic_id: Current topic ID
        missing_requirements: List of missing requirement messages
        uploaded_content: List of ContentItem objects for the topic
    """
    metadata = STAGE_METADATA[stage]

    st.markdown(f"### 🔒 {metadata['name']}")
    st.caption(metadata['description'])
    st.divider()

    # Requirements section
    _render_requirements_section(stage, uploaded_content, missing_requirements)

    st.divider()

    # Missing requirements
    st.markdown("**Missing:**")
    for requirement in missing_requirements:
        # Clean up the message
        clean_msg = requirement.replace("Missing ", "")
        st.markdown(f"• {clean_msg}")

    st.divider()

    # Disabled button
    st.button(
        "Generate",
        key=f"gen_btn_{stage.value}_{topic_id}",
        disabled=True,
        use_container_width=True,
        help="Upload required files to unlock"
    )


def _render_ready_card(
    stage: Stage,
    topic_id: str,
    uploaded_content: List,
    missing_requirements: List[str]
) -> Optional[Stage]:
    """
    Render a ready card (green, can generate).

    Args:
        stage: The generation stage
        topic_id: Current topic ID
        uploaded_content: List of ContentItem objects for the topic
        missing_requirements: Empty list (included for consistency)

    Returns:
        The stage if user clicked Generate, None otherwise
    """
    metadata = STAGE_METADATA[stage]

    st.markdown(f"### ✅ {metadata['name']}")
    st.caption(metadata['description'])
    st.divider()

    # Requirements section
    _render_requirements_section(stage, uploaded_content, missing_requirements)

    st.divider()

    # Ready message
    st.success("✅ Ready to generate!")

    st.divider()

    # Generate button
    if st.button(
        "Generate",
        key=f"gen_btn_{stage.value}_{topic_id}",
        type="primary",
        use_container_width=True
    ):
        return stage

    return None


def _render_generated_card(
    stage: Stage,
    topic_id: str,
    latest_generation: Generation,
    generation_history: List[Generation],
    uploaded_content: List,
    missing_requirements: List[str]
) -> Optional[Stage]:
    """
    Render a generated card (blue, has completed generation).

    Args:
        stage: The generation stage
        topic_id: Current topic ID
        latest_generation: Most recent completed generation
        generation_history: All generations for this stage
        uploaded_content: List of ContentItem objects for the topic
        missing_requirements: Empty list (included for consistency)

    Returns:
        The stage if user clicked Regenerate, None otherwise
    """
    metadata = STAGE_METADATA[stage]

    st.markdown(f"### ✨ {metadata['name']}")
    st.caption(metadata['description'])
    st.divider()

    # Latest generation info
    st.markdown(f"**Latest:** v{latest_generation.version}")
    created_time = humanize.naturaltime(latest_generation.created_at)
    st.caption(f"Created {created_time}")

    st.divider()

    # Links to Notion and Drive
    col1, col2 = st.columns(2)

    with col1:
        if latest_generation.notion_url:
            st.markdown(f"[📝 Notion]({latest_generation.notion_url})")
        else:
            st.caption("📝 Notion (pending)")

    with col2:
        if latest_generation.drive_backup_url:
            st.markdown(f"[📁 Drive]({latest_generation.drive_backup_url})")
        else:
            st.caption("📁 Drive (pending)")

    st.divider()

    # Regenerate button
    next_version = latest_generation.version + 1
    clicked = st.button(
        f"Regenerate v{next_version}",
        key=f"regen_btn_{stage.value}_{topic_id}",
        type="primary",
        use_container_width=True
    )

    # History expander
    if len(generation_history) > 1:
        with st.expander(f"📜 View history ({len(generation_history)} versions)"):
            for gen in reversed(generation_history):  # Show oldest first
                st.markdown(f"**v{gen.version}** - {gen.created_at.strftime('%b %d, %Y')}")

                # Links for this version
                history_col1, history_col2 = st.columns(2)
                with history_col1:
                    if gen.notion_url:
                        st.markdown(f"[📝 Notion]({gen.notion_url})")
                with history_col2:
                    if gen.drive_backup_url:
                        st.markdown(f"[📁 Drive]({gen.drive_backup_url})")

                if gen != generation_history[-1]:  # Don't add divider after last item
                    st.divider()

    if clicked:
        return stage

    return None


def render_stage_cards(
    topic_id: str,
    module_name: str,
    conn: sqlite3.Connection
) -> Optional[Stage]:
    """
    Render the three-stage generation pipeline cards.

    Displays MK1, MK2, and MK3 cards with visual state indicators:
    - 🔒 Locked (gray): Requirements not met
    - ✅ Ready (green): Can generate
    - ✨ Generated (blue): Has completed generation(s)

    Args:
        topic_id: The current topic ID
        module_name: The module name (for Claude Project reference)
        conn: Database connection for querying

    Returns:
        The Stage that was clicked for generation/regeneration, or None

    Example:
        stage_to_generate = render_stage_cards(topic.id, module.name, conn)
        if stage_to_generate:
            show_generation_modal(stage_to_generate)
    """
    gen_service = GenerationService(conn)
    content_service = ContentService(conn)

    # Get uploaded content for requirements checking
    uploaded_content = content_service.get_topic_content(topic_id)

    # Query state for all three stages
    stages_data = {}
    for stage in [Stage.MK1, Stage.MK2, Stage.MK3]:
        can_gen, missing = gen_service.can_generate_stage(topic_id, stage)
        latest = gen_service.get_latest_completed_generation(topic_id, stage)
        history = gen_service.get_generation_history(topic_id, stage)

        stages_data[stage] = {
            "can_generate": can_gen,
            "missing": missing,
            "latest": latest,
            "history": history,
            "state": _determine_card_state(latest, can_gen)
        }

    # Render three columns
    col1, col2, col3 = st.columns(3)

    clicked_stage = None

    # Render MK1 card
    with col1:
        with st.container():
            data = stages_data[Stage.MK1]

            if data["state"] == "locked":
                _render_locked_card(
                    Stage.MK1,
                    topic_id,
                    data["missing"],
                    uploaded_content
                )
            elif data["state"] == "ready":
                result = _render_ready_card(
                    Stage.MK1,
                    topic_id,
                    uploaded_content,
                    data["missing"]
                )
                if result:
                    clicked_stage = result
            else:  # generated
                result = _render_generated_card(
                    Stage.MK1,
                    topic_id,
                    data["latest"],
                    data["history"],
                    uploaded_content,
                    data["missing"]
                )
                if result:
                    clicked_stage = result

    # Render MK2 card
    with col2:
        with st.container():
            data = stages_data[Stage.MK2]

            if data["state"] == "locked":
                _render_locked_card(
                    Stage.MK2,
                    topic_id,
                    data["missing"],
                    uploaded_content
                )
            elif data["state"] == "ready":
                result = _render_ready_card(
                    Stage.MK2,
                    topic_id,
                    uploaded_content,
                    data["missing"]
                )
                if result:
                    clicked_stage = result
            else:  # generated
                result = _render_generated_card(
                    Stage.MK2,
                    topic_id,
                    data["latest"],
                    data["history"],
                    uploaded_content,
                    data["missing"]
                )
                if result:
                    clicked_stage = result

    # Render MK3 card
    with col3:
        with st.container():
            data = stages_data[Stage.MK3]

            if data["state"] == "locked":
                _render_locked_card(
                    Stage.MK3,
                    topic_id,
                    data["missing"],
                    uploaded_content
                )
            elif data["state"] == "ready":
                result = _render_ready_card(
                    Stage.MK3,
                    topic_id,
                    uploaded_content,
                    data["missing"]
                )
                if result:
                    clicked_stage = result
            else:  # generated
                result = _render_generated_card(
                    Stage.MK3,
                    topic_id,
                    data["latest"],
                    data["history"],
                    uploaded_content,
                    data["missing"]
                )
                if result:
                    clicked_stage = result

    return clicked_stage
