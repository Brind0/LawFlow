# Generation Modal Workflow Documentation

## Overview

The Generation Modal (`ui/components/generation_modal.py`) is the orchestrator for LawFlow's human-in-the-loop AI generation workflow. It guides users through a three-step process to create AI-generated study notes.

## Visual Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER CLICKS "GENERATE"                      │
│                   (from stage_cards.py)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              MODAL: Check for Existing Generation               │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ Session State: gen_id_{topic_id}_{stage} exists?     │    │
│  └─────────────────────┬──────────────────┬──────────────┘    │
│                        │                  │                    │
│                   YES  │                  │  NO                │
│                        ▼                  ▼                    │
│              Fetch Generation      Create New Generation       │
│              from Database         via GenerationService       │
│                        │                  │                    │
│                        └──────────┬───────┘                    │
│                                   │                            │
│                                   ▼                            │
│                    Store generation.id in session state        │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 1: Verify Claude Project Files                │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ render_claude_file_checklist(module_name, file_names) │    │
│  │                                                        │    │
│  │ Shows:                                                 │    │
│  │ - Claude Project name                                  │    │
│  │ - Checklist of required files                          │    │
│  │ - Upload instructions                                  │    │
│  └─────────────────────────┬──────────────────────────────┘    │
│                            │                                   │
│                            ▼                                   │
│              User checks boxes to confirm files                │
│                            │                                   │
│                            ▼                                   │
│                   files_confirmed = True?                      │
│                            │                                   │
│                         NO │ YES                               │
│                            │  │                                │
│           Show warning <───┘  └───> Continue to Step 2        │
│           Block Steps 2-3                                      │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 2: Copy Prompt to Clipboard                   │
│            (Only visible if Step 1 confirmed)                   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ st.expander("View Full Prompt")                       │    │
│  │ - Shows generation.prompt_used                        │    │
│  │ - Scrollable preview (300px height)                   │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ copy_to_clipboard_button(generation.prompt_used)      │    │
│  │ - JavaScript-based clipboard API                      │    │
│  │ - Shows "✓ Copied!" feedback                          │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                 │
│  Instructions:                                                  │
│  "Paste this into your Claude Project chat"                    │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              STEP 3: Paste Claude's Response                    │
│            (Only visible if Step 1 confirmed)                   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ paste_from_clipboard_area(key=f"response_{gen_id}")   │    │
│  │ - Large text area (400px height)                      │    │
│  │ - For pasting markdown from Claude                    │    │
│  └─────────────────────────┬──────────────────────────────┘    │
│                            │                                   │
│                            ▼                                   │
│              response_content = text_area_value                │
│                            │                                   │
│                            ▼                                   │
│              Submit button enabled?                            │
│           (only if response_content not empty)                 │
│                            │                                   │
│                         NO │ YES                               │
│                            │  │                                │
│  Show disabled button <────┘  └───> "Process & Save to Notion"│
│  with warning message                     │                    │
│                                           │                    │
│                                      User clicks               │
│                                           │                    │
└───────────────────────────────────────────┼────────────────────┘
                                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PROCESSING: Save to Notion & Drive              │
│                                                                 │
│  st.spinner("Processing response...")                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ 1. Initialize NotionClient(settings.NOTION_TOKEN)     │    │
│  │ 2. Initialize DriveClient(credentials_path, token)    │    │
│  │ 3. Call drive_client.authenticate()                   │    │
│  │ 4. Create OutputService(conn, notion, drive)          │    │
│  │ 5. Call output_service.process_response(...)          │    │
│  │                                                        │    │
│  │    OutputService internally:                          │    │
│  │    - Converts markdown to Notion blocks               │    │
│  │    - Creates Notion page                              │    │
│  │    - Uploads markdown to Drive                        │    │
│  │    - Updates Generation record                        │    │
│  │    - Returns {notion_url, drive_url, generation_id}   │    │
│  └─────────────────────────┬──────────────────────────────┘    │
│                            │                                   │
│                      SUCCESS │ ERROR                           │
│                            │  │                                │
│                            │  └───> Show error message         │
│                            │        with troubleshooting       │
│                            │        Keep modal open            │
│                            │        Return False               │
│                            │                                   │
│                            ▼                                   │
│              Store result in session state                     │
│              Set gen_success_{topic_id}_{stage} = True         │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUCCESS STATE DISPLAY                        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ ✅ Generation Complete!                               │    │
│  │                                                        │    │
│  │ ✓ Converted to Notion blocks                          │    │
│  │ ✓ Created as Notion page                              │    │
│  │ ✓ Backed up to Google Drive                           │    │
│  │                                                        │    │
│  │ [📝 View in Notion]  [📁 View in Drive]               │    │
│  │                                                        │    │
│  │ [ Close & Refresh ]  ← Button                         │    │
│  └─────────────────────────┬──────────────────────────────┘    │
│                            │                                   │
│                      User clicks                               │
│                            │                                   │
│                            ▼                                   │
│              Clear session state:                              │
│              - gen_id_{topic_id}_{stage}                       │
│              - gen_success_{topic_id}_{stage}                  │
│              - result_{generation_id}                          │
│                            │                                   │
│                            ▼                                   │
│                      Return True                               │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 CALLER (topic.py) RECEIVES True                 │
│                                                                 │
│  if success:                                                    │
│      st.balloons()    # Celebrate!                              │
│      st.rerun()       # Refresh page to show updated cards      │
└─────────────────────────────────────────────────────────────────┘
```

## State Management

### Session State Keys

The modal uses three session state keys per generation:

1. **`gen_id_{topic_id}_{stage.value}`**
   - Stores the active Generation ID
   - Persists across Streamlit reruns
   - Allows resuming if user navigates away
   - Cleared when generation completes

2. **`gen_success_{topic_id}_{stage.value}`**
   - Boolean flag indicating success
   - Controls display of success banner
   - Cleared when modal closes

3. **`result_{generation_id}`**
   - Stores result dictionary from OutputService
   - Contains `notion_url`, `drive_url`, `generation_id`
   - Used to display links in success state
   - Cleared when modal closes

### State Lifecycle

```
User clicks Generate
    │
    ├─> gen_id_* created (stores new Generation ID)
    │
User completes workflow
    │
    ├─> gen_success_* = True
    ├─> result_* = {notion_url, drive_url, ...}
    │
User clicks "Close & Refresh"
    │
    ├─> gen_id_* deleted
    ├─> gen_success_* deleted
    ├─> result_* deleted
    │
    └─> st.rerun() triggers page refresh
```

## Progressive Disclosure Pattern

The modal uses progressive disclosure to guide users through the workflow:

```python
# ALWAYS visible
files_confirmed = render_claude_file_checklist(...)

# Only visible if files confirmed
if files_confirmed:
    # Step 2: Copy prompt
    copy_to_clipboard_button(...)

    # Step 3: Paste response
    response = paste_from_clipboard_area(...)

    # Submit button (disabled until response entered)
    submit_button(disabled=not response)
```

This prevents:
- Copying prompt before confirming files
- Submitting without pasting response
- Confusion about which step to do next

## Error Handling

### Error Types

1. **Cannot Start Generation**
   - Requirements not met (missing files, MK2 not completed)
   - Shows error message and returns False
   - User must upload required files first

2. **Processing Errors**
   - Notion API errors (invalid token, rate limit)
   - Drive API errors (auth failure, quota exceeded)
   - Markdown conversion errors (invalid syntax)
   - Shows detailed error message with troubleshooting
   - Keeps modal open so user can retry
   - Response text preserved in text area

3. **Configuration Errors**
   - Missing Notion Database ID
   - Missing Notion token
   - Missing Drive credentials
   - Shows error message in topic.py before modal

### Error Recovery

```
Error occurs during processing
    │
    ├─> Catch exception
    ├─> Display error message
    ├─> Show troubleshooting tips
    ├─> Keep text area with user's response
    ├─> Allow user to fix issue (e.g., check token)
    ├─> User can retry submit
    │
    └─> If retry succeeds, continue to success state
```

## Integration Points

### Services Used

1. **GenerationService**
   - `start_generation(topic_id, stage)` - Creates pending generation
   - `generation_repo.get_by_id(id)` - Fetches existing generation

2. **ContentService**
   - `get_topic_content(topic_id)` - Gets uploaded files for checklist

3. **OutputService**
   - `process_response(gen_id, response, db_id)` - Processes Claude's response
   - Creates Notion page, uploads to Drive, updates Generation

### Components Used

1. **clipboard.py**
   - `copy_to_clipboard_button(text, label)` - JavaScript-based copy
   - `paste_from_clipboard_area(key)` - Large text area for pasting

2. **claude_file_checklist.py**
   - `render_claude_file_checklist(module, files)` - File verification UI

3. **stage_cards.py**
   - Returns clicked Stage, triggering modal
   - Not directly imported, but integrated via topic.py

### External Clients

1. **NotionClient**
   - Initialized with `settings.NOTION_TOKEN`
   - Creates pages in specified database

2. **DriveClient**
   - Initialized with credentials and token paths
   - Requires explicit `authenticate()` call
   - Uploads markdown backups to Drive

## Return Value Semantics

```python
success = show_generation_modal(...)

if success:
    # True means: Generation completed AND user closed modal
    st.balloons()
    st.rerun()
else:
    # False means: Still in progress OR error occurred
    # Modal stays open, no action needed
    pass
```

The caller should only act on `True`:
- Show celebration (balloons)
- Refresh page to update stage cards
- Clear any temporary state

## Performance Considerations

### Lazy Initialization

External clients are only initialized when needed (Step 3):

```python
# NOT initialized until user submits
if st.button("Process & Save to Notion"):
    notion_client = NotionClient(...)  # Initialize here
    drive_client = DriveClient(...)
    drive_client.authenticate()
```

This avoids:
- Unnecessary OAuth flows
- API calls on every render
- Slow page loads

### Caching

Session state acts as a cache:
- Generation ID cached (avoids re-creating)
- Result data cached (avoids re-fetching)
- File confirmation state cached (persists across reruns)

## Security Considerations

### Credential Handling

- Notion token from `settings.NOTION_TOKEN` (env var)
- Drive credentials from file paths in settings
- Never hardcode tokens in UI code
- Never log or display sensitive data

### Input Validation

- Response content validated by OutputService
- Markdown parsed and sanitized before Notion upload
- Generation ID validated (must exist in database)
- Stage validated (must be valid enum)

## Testing Strategy

### Unit Tests

Test the modal's logic in isolation:
- Session state management
- Progressive disclosure logic
- Error handling paths

### Integration Tests

Test the complete workflow:
1. Create topic with content
2. Trigger modal
3. Confirm files
4. Copy prompt
5. Paste response
6. Submit and verify Notion/Drive

### Manual Tests

Test the UI/UX:
- Visual layout on different screen sizes
- Button states (enabled/disabled)
- Loading spinners
- Error messages
- Success state links

## Future Enhancements

### Potential Improvements

1. **Auto-detect clipboard content**
   - Pre-fill response if markdown detected on clipboard
   - Reduce manual paste step

2. **Prompt preview improvements**
   - Syntax highlighting for better readability
   - Collapsible sections (variables, instructions, etc.)

3. **Progress tracking**
   - Step indicators (1/3, 2/3, 3/3)
   - Progress bar during processing

4. **Retry mechanism**
   - Automatic retry on transient errors
   - Exponential backoff for rate limits

5. **Batch operations**
   - Generate multiple stages at once
   - Queue system for sequential processing

6. **AI validation**
   - Pre-check response format before submitting
   - Warn if markdown seems invalid

## Related Documentation

- `/Users/charliebrind/Documents/university/LawFlow/GENERATION_MODAL_INTEGRATION.md` - Integration guide
- `/Users/charliebrind/Documents/university/LawFlow/GENERATION_SERVICE_USAGE.md` - Service layer docs
- `/Users/charliebrind/Documents/university/LawFlow/docs/GENERATION_SERVICE_ARCHITECTURE.md` - Architecture docs
- `/Users/charliebrind/Documents/university/LawFlow/roadmap.md` - Phase 4 implementation plan
- `/Users/charliebrind/Documents/university/LawFlow/CLAUDE.md` - Project overview

## File Location

**Created:** `/Users/charliebrind/Documents/university/LawFlow/ui/components/generation_modal.py`

**Lines of Code:** 296

**Dependencies:**
- Streamlit (UI framework)
- GenerationService (business logic)
- ContentService (file queries)
- OutputService (response processing)
- NotionClient (external API)
- DriveClient (external API)
- clipboard.py (copy/paste components)
- claude_file_checklist.py (file verification)
