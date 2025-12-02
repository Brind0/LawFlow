⚖️ LawFlow
A local-first academic workflow orchestrator designed to streamline the chaotic law school study process.

🚀 What is this?
LawFlow is a productivity tool that solves the "fragmented content" problem faced by law students. Instead of manually juggling lecture PDFs, transcripts, and tutorial readings across different folders and weeks, LawFlow acts as a Content Vault.

It orchestrates a "human-in-the-loop" AI workflow to progressively synthesize these inputs into structured, exam-ready notes in Notion.

✨ Key Features
📂 Content Vault: Centralized management for Lecture PDFs, Source Materials, and Transcripts, backed by Google Drive.

🧠 Human-in-the-Loop AI: Smart prompt engineering generates structured revision notes via Claude, bypassing expensive API costs while maintaining high-quality output.

📝 Notion Integration: Converts raw Markdown into complex Notion Block Objects (using martian-py) to create beautiful, formatted pages automatically.

🔒 Local-First Architecture: Uses SQLite for metadata and state management, ensuring data persistence and speed.

🛠️ Tech Stack
Frontend/Backend: Streamlit (Python)

Database: SQLite

Integrations: Google Drive API (OAuth 2.0), Notion API

Templating: Jinja2 (for dynamic prompt generation)
