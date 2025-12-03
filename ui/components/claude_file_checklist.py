"""
Claude File Checklist component for LawFlow's human-in-the-loop workflow.

This component addresses the UX friction of double-handling files:
- Users upload files to LawFlow (for Drive storage and tracking)
- Users ALSO upload to Claude Projects (for AI processing)

Before copying a prompt, users verify that all required files are in Claude Project.
This prevents errors from missing files during AI generation.
"""

import streamlit as st
from typing import List


def render_claude_file_checklist(module_name: str, file_names: List[str]) -> bool:
    """
    Renders a checklist of files to verify in Claude Projects.

    This component ensures users have uploaded all required files to their
    Claude Project before copying the generation prompt. It prevents the
    common error of missing files during AI generation.

    Args:
        module_name: The module name (e.g., "Land Law") - used to show which
            Claude Project the files should be in
        file_names: List of file names that should be uploaded to Claude Project

    Returns:
        True if user has confirmed all files are uploaded, False otherwise

    Example Usage:
        >>> files_confirmed = render_claude_file_checklist(
        ...     module_name="Land Law",
        ...     file_names=["Week_5_Lecture.pdf", "Tutorial_Week_5.pdf"]
        ... )
        >>> if files_confirmed:
        ...     copy_to_clipboard_button(prompt)
        ... else:
        ...     st.warning("Please confirm files before proceeding")

    UI Pattern:
        1. Shows Claude Project name in info box
        2. Lists all required files with checkboxes
        3. Shows warning if files not confirmed
        4. Shows success message when all confirmed
        5. Returns boolean for workflow control

    Session State:
        Uses unique keys per file to track confirmation state across reruns.
        Keys format: "claude_file_check_{module_name}_{file_name}"
    """

    # Step 1: Show which Claude Project to use
    st.markdown("### Step 1: Verify Claude Project Files")
    st.info(f"📁 Open your Claude Project: **{module_name}**")

    # Helper text
    st.markdown(
        """
        Before generating content, verify that all required files are uploaded
        to your Claude Project. This ensures Claude can access the source materials
        when you paste the prompt.
        """
    )

    st.markdown("**Required files in Claude Project:**")

    # Step 2: Render checklist with individual checkboxes
    all_checked = True
    for file_name in file_names:
        # Use unique session state key per file and module
        # This allows state to persist across Streamlit reruns
        checkbox_key = f"claude_file_check_{module_name}_{file_name}"

        checked = st.checkbox(
            f"📄 {file_name}",
            key=checkbox_key,
            help=f"Check this box after uploading {file_name} to Claude Project"
        )

        if not checked:
            all_checked = False

    # Step 3: Provide feedback based on confirmation state
    if not all_checked:
        st.warning(
            """
            ⚠️ Please upload missing files to your Claude Project before proceeding.

            **How to upload files to Claude Projects:**
            1. Open [Claude.ai](https://claude.ai/)
            2. Navigate to your project: **{module}**
            3. Click "Add content" → "Upload files"
            4. Upload the unchecked files above
            5. Return here and check the boxes to confirm
            """.format(module=module_name)
        )
        return False

    # All files confirmed!
    st.success("✅ All files confirmed! You can now copy the prompt.")

    # Helper text for next steps
    st.markdown(
        """
        **Next steps:**
        1. Copy the prompt below
        2. Paste it into your Claude Project chat
        3. Claude will process the uploaded files and generate content
        4. Copy the response back to LawFlow
        """
    )

    return True
