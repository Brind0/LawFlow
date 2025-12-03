"""
Clipboard component for LawFlow's human-in-the-loop workflow.

CRITICAL: This uses JavaScript bridge via streamlit.components.v1
DO NOT use pyperclip - it doesn't work in Streamlit browser context!

This component enables:
1. Copy-to-clipboard for generated prompts (JavaScript-based)
2. Paste area for Claude responses (text area)

Browser Requirements:
- Secure context (HTTPS or localhost) - Streamlit localhost ✅
- Modern Clipboard API (Chrome 66+, Firefox 63+, Safari 13.1+)
- User gesture required - button click satisfies this ✅
"""

import streamlit as st
import streamlit.components.v1 as components


def copy_to_clipboard_button(text: str, button_label: str = "📋 Copy to Clipboard"):
    """
    Creates a button that copies text to clipboard using JavaScript bridge.

    IMPORTANT: pyperclip does NOT work in browser context!
    This uses JavaScript via streamlit components.

    Args:
        text: The text to copy (e.g., generated prompt)
        button_label: Label for the button (default: "📋 Copy to Clipboard")

    Implementation:
        - Uses navigator.clipboard.writeText() API
        - Shows "✓ Copied!" feedback for 2 seconds
        - Handles clipboard API failures gracefully
        - Works in Chrome, Firefox, Safari (modern versions)

    Example:
        >>> copy_to_clipboard_button(
        ...     text=generation.prompt_used,
        ...     button_label="📋 Copy Prompt"
        ... )
    """

    # Escape text for JavaScript template literal
    # Must escape: backslashes, backticks, and dollar signs
    escaped_text = text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

    # JavaScript to copy to clipboard using modern Clipboard API
    copy_js = f"""
    <script>
    function copyToClipboard() {{
        const text = `{escaped_text}`;
        navigator.clipboard.writeText(text).then(function() {{
            // Success: Show confirmation feedback
            document.getElementById('copy-status').innerText = '✓ Copied!';
            setTimeout(function() {{
                document.getElementById('copy-status').innerText = '';
            }}, 2000);
        }}, function(err) {{
            // Failure: Show error feedback
            document.getElementById('copy-status').innerText = 'Failed to copy';
        }});
    }}
    </script>

    <button onclick="copyToClipboard()" style="
        padding: 0.5rem 1rem;
        background-color: #FF4B4B;
        color: white;
        border: none;
        border-radius: 0.25rem;
        cursor: pointer;
        font-size: 1rem;
    ">{button_label}</button>
    <span id="copy-status" style="margin-left: 1rem; color: green;"></span>
    """

    # Render the HTML/JS component
    # Height=50 provides enough space for button + status message
    components.html(copy_js, height=50)


def paste_from_clipboard_area(key: str) -> str:
    """
    Provides a text area for pasting Claude's response.

    Args:
        key: Unique Streamlit widget key for session state

    Returns:
        The pasted text content (empty string if nothing pasted)

    Implementation:
        - Uses st.text_area() with 400px height for multi-line content
        - Includes helper text to guide users
        - Supports full markdown formatting
        - Returns text for processing by generation service

    Example:
        >>> response = paste_from_clipboard_area(key="claude_response_mk1")
        >>> if response:
        ...     output_service.process_response(gen_id, response)
    """
    return st.text_area(
        "Paste Claude's response here:",
        height=400,
        key=key,
        help="Copy the entire response from Claude and paste it here"
    )
