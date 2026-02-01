-- Initial Fairchild schema

CREATE TABLE IF NOT EXISTS fairchild_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Task identification
    task_name VARCHAR(255) NOT NULL,
    queue VARCHAR(255) NOT NULL DEFAULT 'default',
    args JSONB NOT NULL DEFAULT '{}',

    -- Workflow membership
    workflow_id UUID,
    workflow_name VARCHAR(255),
    job_key VARCHAR(255),
    deps VARCHAR(255)[] DEFAULT '{}',

    -- State
    state VARCHAR(50) NOT NULL DEFAULT 'available',

    -- Scheduling & priority
    priority SMALLINT NOT NULL DEFAULT 5,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Execution
    attempted_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    attempt INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,

    -- Results & errors
    recorded JSONB,
    errors JSONB DEFAULT '[]',

    -- Metadata
    tags VARCHAR(255)[] DEFAULT '{}',
    meta JSONB DEFAULT '{}',

    inserted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for fetching available jobs from a queue
CREATE INDEX IF NOT EXISTS idx_fairchild_jobs_fetchable
    ON fairchild_jobs (queue, state, priority, scheduled_at)
    WHERE state = 'available';

-- Index for workflow lookups
CREATE INDEX IF NOT EXISTS idx_fairchild_jobs_workflow
    ON fairchild_jobs (workflow_id, job_key)
    WHERE workflow_id IS NOT NULL;

-- Index for finding jobs by state
CREATE INDEX IF NOT EXISTS idx_fairchild_jobs_state
    ON fairchild_jobs (state);

-- Index for scheduled jobs that need to become available
CREATE INDEX IF NOT EXISTS idx_fairchild_jobs_scheduled
    ON fairchild_jobs (scheduled_at)
    WHERE state = 'scheduled';
