from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING
from uuid import UUID
import json


def utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


if TYPE_CHECKING:
    from fairchild.job import Job
    from fairchild.task import Task

# Global Fairchild instance
_instance: "Fairchild | None" = None


def get_fairchild() -> "Fairchild":
    """Get the global Fairchild instance."""
    if _instance is None:
        raise RuntimeError(
            "Fairchild not initialized. Call Fairchild(database_url) first."
        )
    return _instance


class Fairchild:
    """Main entry point for Fairchild job queue.

    Usage:
        fairchild = Fairchild("postgresql://localhost/myapp")

        # Enqueue jobs
        my_task.enqueue(item_id=42)

        # Or use directly
        fairchild.enqueue(my_task, args={"item_id": 42})
    """

    def __init__(self, database_url: str):
        global _instance

        self.database_url = database_url
        self._pool = None

        # Set as global instance
        _instance = self

    async def connect(self) -> None:
        """Initialize the database connection pool."""
        import asyncpg

        self._pool = await asyncpg.create_pool(self.database_url)

    async def disconnect(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _ensure_connected(self) -> None:
        """Ensure we have a database connection."""
        if self._pool is None:
            await self.connect()

    async def enqueue(
        self,
        task: "Task",
        args: dict[str, Any],
        scheduled_at: datetime | None = None,
        priority: int | None = None,
    ) -> "Job":
        """Enqueue a job for execution.

        Returns the created Job.
        """
        from fairchild.job import Job, JobState

        await self._ensure_connected()

        job = Job(
            task_name=task.name,
            queue=task.queue,
            args=args,
            priority=priority if priority is not None else task.priority,
            max_attempts=task.max_attempts,
            tags=task.tags,
            scheduled_at=scheduled_at or utcnow(),
            state=JobState.AVAILABLE if scheduled_at is None else JobState.SCHEDULED,
        )

        await self._insert_job(job)
        return job

    async def _insert_job(self, job: "Job") -> None:
        """Insert a job into the database."""
        query = """
            INSERT INTO fairchild_jobs (
                id, task_name, queue, args,
                parent_id, deps,
                state, priority, scheduled_at,
                attempt, max_attempts, tags, meta,
                inserted_at, updated_at
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6,
                $7, $8, $9,
                $10, $11, $12, $13,
                $14, $15
            )
        """

        await self._pool.execute(
            query,
            job.id,
            job.task_name,
            job.queue,
            json.dumps(job.args),
            job.parent_id,
            job.deps,
            job.state.value,
            job.priority,
            job.scheduled_at,
            job.attempt,
            job.max_attempts,
            job.tags,
            json.dumps(job.meta),
            job.inserted_at,
            job.updated_at,
        )

    async def get_job(self, job_id: UUID) -> "Job | None":
        """Get a job by ID."""
        from fairchild.job import Job

        await self._ensure_connected()

        query = """
            SELECT * FROM fairchild_jobs WHERE id = $1
        """
        row = await self._pool.fetchrow(query, job_id)
        if row is None:
            return None

        return Job.from_row(dict(row))

    async def get_recorded(self, job_id: UUID) -> Any:
        """Get the recorded value from a completed job."""
        await self._ensure_connected()

        query = """
            SELECT recorded FROM fairchild_jobs
            WHERE id = $1
        """

        row = await self._pool.fetchrow(query, job_id)
        if row is None:
            return None

        recorded = row["recorded"]
        if recorded is None:
            return None

        return json.loads(recorded) if isinstance(recorded, str) else recorded
