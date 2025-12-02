-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Modules table
CREATE TABLE IF NOT EXISTS modules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    claude_project_name TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Topics table
CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    module_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    UNIQUE(module_id, name)
);

-- Content items table
CREATE TABLE IF NOT EXISTS content_items (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (
        content_type IN ('LECTURE_PDF', 'SOURCE_MATERIAL', 'TUTORIAL_PDF', 'TRANSCRIPT')
    ),
    file_name TEXT NOT NULL,
    drive_file_id TEXT,
    drive_url TEXT,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- Generations table
CREATE TABLE IF NOT EXISTS generations (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    stage TEXT NOT NULL CHECK (stage IN ('MK1', 'MK2', 'MK3')),
    version INTEGER NOT NULL DEFAULT 1,
    prompt_used TEXT NOT NULL,
    response_content TEXT,
    notion_page_id TEXT,
    notion_url TEXT,
    drive_backup_id TEXT,
    drive_backup_url TEXT,
    previous_generation_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'COMPLETED', 'FAILED')
    ),
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
    FOREIGN KEY (previous_generation_id) REFERENCES generations(id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_topics_module ON topics(module_id);
CREATE INDEX IF NOT EXISTS idx_content_topic ON content_items(topic_id);
CREATE INDEX IF NOT EXISTS idx_content_type ON content_items(content_type);
CREATE INDEX IF NOT EXISTS idx_content_active ON content_items(is_active);
CREATE INDEX IF NOT EXISTS idx_generations_topic ON generations(topic_id);
CREATE INDEX IF NOT EXISTS idx_generations_stage ON generations(stage);
CREATE INDEX IF NOT EXISTS idx_generations_status ON generations(status);

-- Trigger to update 'updated_at' on modules
CREATE TRIGGER IF NOT EXISTS update_modules_timestamp 
    AFTER UPDATE ON modules
    FOR EACH ROW
BEGIN
    UPDATE modules SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Trigger to update 'updated_at' on topics
CREATE TRIGGER IF NOT EXISTS update_topics_timestamp 
    AFTER UPDATE ON topics
    FOR EACH ROW
BEGIN
    UPDATE topics SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
