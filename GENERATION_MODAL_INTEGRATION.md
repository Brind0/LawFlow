# Generation Modal Integration Guide

This guide shows how to integrate the `generation_modal.py` component into `ui/pages/topic.py` to complete the Phase 4 implementation.

## Quick Reference

**File Created:** `/Users/charliebrind/Documents/university/LawFlow/ui/components/generation_modal.py`

**Function Signature:**
```python
def show_generation_modal(
    topic_id: str,
    stage: Stage,
    module_name: str,
    notion_database_id: str,
    conn: sqlite3.Connection
) -> bool
```

## Integration into topic.py

### Current State (Before Integration)

```python
# ui/pages/topic.py
import streamlit as st
from database.repositories.topic_repo import TopicRepository
from database.repositories.module_repo import ModuleRepository
from ui.components.vault import render_vault

def render(conn, topic_id: str):
    topic_repo = TopicRepository(conn)
    module_repo = ModuleRepository(conn)
    topic = topic_repo.get_by_id(topic_id)
    if not topic:
        st.error("Topic not found!")
        return

    module = module_repo.get_by_id(topic.module_id)

    st.title(f"{module.name} / {topic.name}")

    tab1, tab2 = st.tabs(["📚 Content Vault", "✨ Generations"])

    with tab1:
        render_vault(conn, module, topic)

    with tab2:
        st.header("Generations")
        st.info("Generation features coming in Sprint 5!")
```

### Proposed State (After Integration)

```python
# ui/pages/topic.py
import streamlit as st
from database.repositories.topic_repo import TopicRepository
from database.repositories.module_repo import ModuleRepository
from ui.components.vault import render_vault
from ui.components.stage_cards import render_stage_cards
from ui.components.generation_modal import show_generation_modal
from config.settings import settings

def render(conn, topic_id: str):
    topic_repo = TopicRepository(conn)
    module_repo = ModuleRepository(conn)
    topic = topic_repo.get_by_id(topic_id)
    if not topic:
        st.error("Topic not found!")
        return

    module = module_repo.get_by_id(topic.module_id)

    st.title(f"{module.name} / {topic.name}")

    tab1, tab2 = st.tabs(["📚 Content Vault", "✨ Generations"])

    with tab1:
        render_vault(conn, module, topic)

    with tab2:
        st.header("Generations")

        # Render the three-stage pipeline cards
        clicked_stage = render_stage_cards(
            topic_id=topic.id,
            module_name=module.name,
            conn=conn
        )

        # If user clicked a Generate/Regenerate button, show the modal
        if clicked_stage:
            st.divider()

            # TODO: Add Notion Database ID to settings.py
            # For now, you can hardcode it or prompt user in settings page
            notion_db_id = getattr(settings, 'NOTION_DATABASE_ID', '')

            if not notion_db_id:
                st.error(
                    """
                    **Notion Database ID not configured!**

                    Please add your Notion database ID in the Settings page.

                    To find your database ID:
                    1. Open your Notion workspace
                    2. Create or open a database for LawFlow generations
                    3. Copy the database ID from the URL:
                       `https://notion.so/<workspace>/<DATABASE_ID>?v=...`
                    """
                )
            else:
                # Show the generation modal
                success = show_generation_modal(
                    topic_id=topic.id,
                    stage=clicked_stage,
                    module_name=module.name,
                    notion_database_id=notion_db_id,
                    conn=conn
                )

                # If generation completed, celebrate and refresh
                if success:
                    st.balloons()
                    st.rerun()
```

## Configuration Updates Required

### 1. Add Notion Database ID to settings.py

```python
# config/settings.py
@dataclass
class Settings:
    # ... existing fields ...

    # Notion
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")  # ADD THIS

    # ... rest of file ...
```

### 2. Add to .env file

```bash
# .env
NOTION_TOKEN=your_notion_token_here
NOTION_DATABASE_ID=your_database_id_here
```

### 3. Update settings page to allow configuration

You can add a form in `ui/pages/settings.py` to let users configure the Notion Database ID via the UI, or they can set it directly in the `.env` file.

## How the Modal Works

### Three-Step Workflow

**Step 1: Verify Claude Project Files**
- Displays checklist of files user should upload to Claude Project
- Uses `render_claude_file_checklist()` component
- Progressive disclosure: Steps 2-3 only show when files confirmed

**Step 2: Copy Prompt to Clipboard**
- Shows expandable preview of the generated prompt
- Uses `copy_to_clipboard_button()` with JavaScript bridge
- Provides instructions for pasting into Claude

**Step 3: Paste Claude's Response**
- Large text area using `paste_from_clipboard_area()`
- Submit button (disabled until text pasted)
- Loading spinner during processing

### State Management

The modal uses Streamlit session state to track:
- `gen_id_{topic_id}_{stage}`: Active generation ID
- `gen_success_{topic_id}_{stage}`: Success flag
- `result_{generation_id}`: Result data (Notion/Drive URLs)

This allows:
- Resuming pending generations (if user refreshes page)
- Showing success state across reruns
- Preventing duplicate generation creation

### Error Handling

The modal catches exceptions from `OutputService.process_response()` and displays:
- The specific error message
- Troubleshooting tips (check tokens, credentials, internet)
- Actionable next steps (try again)
- Preserves user's pasted response (not lost on error)

### Success State

When processing succeeds:
- Green success banner
- Checklist of completed steps
- Clickable links to Notion page and Drive backup
- "Close & Refresh" button to update stage cards
- Celebration (balloons) when closed

## Usage Flow

1. User clicks "Generate" on a ready stage card
2. Modal appears with Step 1 (file checklist)
3. User confirms files are in Claude Project
4. Step 2 appears with copy button
5. User clicks copy, pastes into Claude
6. User copies Claude's response
7. Step 3 appears, user pastes response
8. User clicks "Process & Save to Notion"
9. Loading spinner shows while processing
10. Success banner with links appears
11. User clicks "Close & Refresh"
12. Modal closes, stage card updates to "generated" state

## Testing Checklist

### Manual Testing
- [ ] Create a topic with lecture PDF
- [ ] Click "Generate" on MK-1 card
- [ ] Verify modal appears with file checklist
- [ ] Check all files in checklist
- [ ] Verify Step 2 appears
- [ ] Click copy button, verify prompt copied
- [ ] Paste prompt into Claude, get response
- [ ] Paste response into Step 3 text area
- [ ] Verify submit button enables
- [ ] Click submit, verify loading spinner
- [ ] Verify success message appears
- [ ] Check links to Notion and Drive work
- [ ] Click "Close & Refresh"
- [ ] Verify stage card now shows "generated" state
- [ ] Verify Notion page exists and has content
- [ ] Verify Drive backup exists

### Error Cases
- [ ] Test with invalid Notion token (should show error)
- [ ] Test with invalid Drive credentials (should show error)
- [ ] Test with empty response (submit should be disabled)
- [ ] Test with invalid markdown (should handle gracefully)
- [ ] Test closing modal mid-workflow (should resume on reopen)

### Edge Cases
- [ ] Test regenerating (v2, v3, etc.)
- [ ] Test MK-2 (requires source materials)
- [ ] Test MK-3 (includes previous MK-2 content)
- [ ] Test with very long prompts (scrollable preview)
- [ ] Test with very long responses (large text area)

## Common Issues & Solutions

### Issue: Notion Database ID not found
**Solution:** Add to `.env` file or settings page

### Issue: "Generation already completed" error
**Solution:** The session state still has the old gen ID. Clear session state or reload page.

### Issue: Copy button doesn't work
**Solution:** Ensure running on localhost (required for Clipboard API). Check browser console for errors.

### Issue: Drive authentication fails
**Solution:** Run `drive_client.authenticate()` to re-trigger OAuth flow. Delete `token.pickle` and re-authenticate.

### Issue: Modal doesn't close after success
**Solution:** Click "Close & Refresh" button. The modal intentionally stays open to show links.

## Architecture Notes

### Why Streamlit Session State?
- Streamlit reruns the entire script on each interaction
- Session state persists data across reruns
- Allows resuming workflows if user navigates away

### Why Progressive Disclosure?
- Reduces cognitive load (only show what's needed)
- Prevents errors (can't copy prompt before confirming files)
- Guides user through linear workflow

### Why Not st.dialog()?
- Streamlit's experimental dialog feature is unstable
- Using containers + dividers provides better control
- Allows more complex state management

### Why JavaScript for Clipboard?
- Python's `pyperclip` doesn't work in browser context
- Browser Clipboard API requires user gesture (button click)
- JavaScript bridge via `streamlit.components.v1` is the solution

## Next Steps

After integrating this modal:
1. Update `ui/pages/topic.py` as shown above
2. Add `NOTION_DATABASE_ID` to `config/settings.py`
3. Test the complete workflow end-to-end
4. Add error handling for edge cases
5. Polish UI (colors, spacing, messaging)
6. Complete Phase 4 testing checklist (roadmap.md lines 216-226)

## Related Files

- `/Users/charliebrind/Documents/university/LawFlow/ui/components/generation_modal.py` (this component)
- `/Users/charliebrind/Documents/university/LawFlow/ui/components/clipboard.py` (copy/paste helpers)
- `/Users/charliebrind/Documents/university/LawFlow/ui/components/claude_file_checklist.py` (Step 1)
- `/Users/charliebrind/Documents/university/LawFlow/ui/components/stage_cards.py` (triggers modal)
- `/Users/charliebrind/Documents/university/LawFlow/services/generation_service.py` (creates generations)
- `/Users/charliebrind/Documents/university/LawFlow/services/output_service.py` (processes responses)
- `/Users/charliebrind/Documents/university/LawFlow/config/settings.py` (configuration)

## PRD References

- **Section 7.4** (lines 1320-1404): Generation Modal UI specifications
- **Section 7.3**: Clipboard integration requirements
- **Section 7.1**: Three-stage generation pipeline
- **Section 5**: Human-in-the-loop workflow rationale
