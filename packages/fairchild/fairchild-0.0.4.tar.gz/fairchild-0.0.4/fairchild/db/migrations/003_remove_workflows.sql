-- Remove workflow columns (replaced by parent-child job relationships)

-- Drop the workflow index first
DROP INDEX IF EXISTS idx_fairchild_jobs_workflow;

-- Remove workflow columns
ALTER TABLE fairchild_jobs DROP COLUMN IF EXISTS workflow_id;
ALTER TABLE fairchild_jobs DROP COLUMN IF EXISTS workflow_name;
ALTER TABLE fairchild_jobs DROP COLUMN IF EXISTS job_key;
