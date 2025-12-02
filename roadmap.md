# LawFlow Project Roadmap 🗺️

This document tracks the development progress of **LawFlow**, an AI-powered legal study assistant. It serves as a source of truth for the current state and future plans.

## 🟢 Completed Phases

### Phase 1: Foundation (Sprint 1)
- [x] **Project Structure**: Created standard Python project layout (`config`, `database`, `ui`, `services`).
- [x] **Database**: SQLite schema implemented with `modules`, `topics`, `content_items`, and `generations` tables.
- [x] **UI Shell**: Streamlit app initialized with Sidebar navigation and placeholder pages.
- [x] **Data Seeding**: Script created (`scripts/seed_data.py`) to populate default modules (Land, Tort, Employment, Legal Practice).

### Phase 2: Integrations (Sprints 2 & 3)
- [x] **Notion Integration**:
    -   `NotionClient` implemented for page creation and block appending.
    -   Markdown-to-Notion conversion logic using `markdown-it-py`.
- [x] **Google Drive Integration**:
    -   `DriveClient` implemented with OAuth 2.0 (`google_credentials.json`).
    -   Supports Folder creation (hierarchical) and File upload/deletion.
    -   **Credentials**: Stored in `data/credentials/`.

### Phase 3: Content Vault (Sprint 4)
- [x] **Service Layer**: `ContentService` orchestrates Drive uploads and Database records.
- [x] **UI Component**: `Vault` component allows file uploads (PDF/TXT) directly from the Topic page.
- [x] **Verification**: Unit tests (`tests/test_content_service.py`) and Browser tests verified the flow.

---

## 🟡 Current Focus

### Phase 4: Generation Logic (Sprint 5)
**Goal**: Implement the AI generation pipelines (Mk-1, Mk-2, Mk-3) using Claude.

- [ ] **Generation Service**:
    -   Create `services/generation_service.py`.
    -   Implement `generate_notes(content_id, stage)` method.
- [ ] **Prompts**:
    -   Define prompt templates for each stage (Summary, Detailed Notes, Exam Questions).
- [ ] **UI Integration**:
    -   Add "Generate" buttons to the `Vault` items.
    -   Display generated content in the "Generations" tab.

---

## 🔴 Future Roadmap

### Phase 5: Notion Sync (Sprint 6)
**Goal**: Push generated content to Notion.
- [ ] **Sync Service**: Orchestrate `Generation` -> `NotionClient`.
- [ ] **UI**: Add "Export to Notion" button.

### Phase 6: Refinement & Polish
- [ ] **Error Handling**: Robust error boundaries for API failures.
- [ ] **Async Processing**: Move generation/upload tasks to background threads (if needed).
- [ ] **Deployment**: Dockerize the application.

---

## 🛠️ Technical Context for AI Developers

-   **Stack**: Python 3.9+, Streamlit, SQLite.
-   **Key Libraries**: `google-api-python-client`, `notion-client`, `anthropic` (upcoming).
-   **Architecture**:
    -   **UI**: `ui/` (Streamlit components).
    -   **Service Layer**: `services/` (Business logic, orchestrates Repos and Integrations).
    -   **Data Layer**: `database/repositories/` (SQL queries).
    -   **Integrations**: `integrations/` (External API wrappers).
-   **Testing**: `pytest` for unit tests. `tests/backtest_*.py` for integration scripts.
