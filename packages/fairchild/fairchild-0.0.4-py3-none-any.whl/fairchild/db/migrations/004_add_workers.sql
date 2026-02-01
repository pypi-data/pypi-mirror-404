-- Workers table to track active workers
CREATE TABLE IF NOT EXISTS fairchild_workers (
    id UUID PRIMARY KEY,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    queues JSONB NOT NULL DEFAULT '{}',  -- {"queue_name": num_slots, ...}
    active_jobs INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'running',  -- running, paused, stopped
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    paused_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_fairchild_workers_state ON fairchild_workers(state);
CREATE INDEX IF NOT EXISTS idx_fairchild_workers_heartbeat ON fairchild_workers(last_heartbeat_at);
