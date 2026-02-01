-- Add tasks column to workers table
-- Workers publish their registered tasks (with schemas) on startup
ALTER TABLE fairchild_workers ADD COLUMN IF NOT EXISTS tasks JSONB DEFAULT '[]';
