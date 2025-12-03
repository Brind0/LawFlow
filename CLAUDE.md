# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LawFlow is a local-first academic workflow orchestrator for law students. It acts as a Content Vault that ingests lecture PDFs, transcripts, and source materials, then uses a human-in-the-loop AI workflow to synthesize them into structured, exam-ready notes in Notion.

**Key Concepts:**
- **Content Vault**: Centralized management for academic materials, backed by Google Drive
- **Generation Stages**: Three-stage AI synthesis pipeline (MK1 → MK2 → MK3)
  - MK1: Initial summary/extraction
  - MK2: Detailed structured notes
  - MK3: Exam-focused questions and practice materials
- **Human-in-the-Loop**: Prompts are engineered to be copy-pasted to Claude via Projects API to minimize API costs while maintaining quality
- **Local-First**: SQLite for metadata and state, ensuring fast offline access

## Development Commands

### Running the Application
```bash
streamlit run app.py
```

### Database Management
```bash
# Seed database with default modules and topics
python scripts/seed_data.py
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov

# Run specific test file
pytest tests/test_content_service.py

# Run integration tests (require API credentials)
python tests/backtest_notion.py
python tests/backtest_drive.py
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8
```

## Architecture

### Layered Architecture Pattern
```
UI Layer (Streamlit)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database Layer (SQLite)
```

**Key Directories:**
- `ui/`: Streamlit components and pages
  - `ui/pages/`: Full page views (dashboard, topic, settings)
  - `ui/components/`: Reusable UI components (sidebar, vault)
- `services/`: Business logic layer that orchestrates repositories and integrations
- `database/repositories/`: Data access layer using Repository pattern with `BaseRepository[T]`
- `integrations/`: External API clients (Google Drive, Notion)
- `config/`: Application settings and prompt templates
- `tests/`: Unit tests and integration backtests

### Database Schema
Four core tables:
- `modules`: Law subjects (e.g., Land Law, Tort Law)
- `topics`: Subtopics within modules (e.g., Easements, Negligence)
- `content_items`: Uploaded files with Drive metadata
- `generations`: AI-generated content with versioning and stage tracking

### State Management
Streamlit session state manages navigation:
- `current_module_id`: Selected module
- `current_topic_id`: Selected topic
- `current_view`: Page routing ('dashboard', 'topic', 'settings')

### Connection Pattern
Database connections use context managers:
```python
with get_connection() as conn:
    repo = SomeRepository(conn)
    # Use repo
```
The connection is passed down from `app.py` through the UI layer to services/repositories.

## Integration Setup

### Google Drive (OAuth 2.0)
1. Download `google_credentials.json` from Google Cloud Console
2. Place in `data/credentials/google_credentials.json`
3. First run triggers OAuth flow, generates `data/credentials/token.pickle`
4. Folder structure: `LawFlow/{Module}/{Topic}/`

**Important:** The DriveClient uses lazy authentication - call `authenticate()` explicitly or it happens on first API call.

### Notion API
1. Create integration at https://www.notion.so/my-integrations
2. Set `NOTION_TOKEN` in `.env`
3. The markdown converter uses `markdown-it-py` to parse Markdown, then maps to Notion Block Objects

## Testing Patterns

- **Unit Tests** (`test_*.py`): Use pytest fixtures from `conftest.py` for test database isolation
- **Integration Tests** (`backtest_*.py`): Manual scripts for testing external APIs, not part of automated test suite
- Tests use temporary databases via `tmp_path` fixture to avoid polluting main DB

## Important Patterns

### Repository Pattern
All repositories extend `BaseRepository[T]` with generic CRUD operations. They use `sqlite3.Row` factory for dict-like row access.

### Service Layer
Services orchestrate multiple repositories and integrations. Example: `ContentService` coordinates `ContentRepository` + `DriveClient` for atomic upload operations (Drive upload + DB record creation).

### Error Handling
- Google Drive operations may require re-authentication if token expires
- Notion operations should gracefully handle API rate limits
- Content deletion is **soft delete** (sets `is_active = False`) to maintain referential integrity

## Development Notes

- The app uses Streamlit's script rerun model - the entire `app.py` reruns on each interaction
- Database triggers auto-update `updated_at` timestamps on modules and topics
- Content types are enum-validated: `LECTURE_PDF`, `SOURCE_MATERIAL`, `TUTORIAL_PDF`, `TRANSCRIPT`
- Generation status tracking: `PENDING` → `COMPLETED` or `FAILED`
- All IDs are UUIDs generated via `uuid.uuid4()`

## Current Development Phase

Per the roadmap, the project has completed:
- ✅ Phase 1-3: Foundation, Integrations, Content Vault (~40% of total project)
- 🔴 Phase 4: Generation Logic (**NOT STARTED - NEXT PRIORITY**)
  - This is the core feature that delivers user value
  - Estimated 30-35 hours of focused work
  - See roadmap.md for detailed breakdown
- ⏳ Phase 5-6: Enhancements, Polish, Production Readiness

**Important:** Phase 4 (Generation System) is critical - the product has 0% user value until this is complete. All work so far has been infrastructure to support this core feature.

### Next Immediate Tasks:
1. Create `database/repositories/generation_repo.py`
2. Create prompt templates in `config/prompts/` (mk1, mk2, mk3 YAML files)
3. Build `services/prompt_service.py` using Jinja2
4. Build `services/generation_service.py` with stage unlock logic
5. Build `ui/components/clipboard.py` (MUST use JavaScript bridge - see PRD Section 7.3)
6. Build generation modal UI workflow

See roadmap.md Phase 4 for complete implementation checklist with PRD references.
