-- Add parent_id column for spawned tasks (parent-child job relationships)

ALTER TABLE fairchild_jobs
ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES fairchild_jobs(id);

CREATE INDEX IF NOT EXISTS idx_fairchild_jobs_parent
    ON fairchild_jobs (parent_id)
    WHERE parent_id IS NOT NULL;
