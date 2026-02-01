import asyncio
import json
import os
import socket
import traceback
from datetime import datetime
from typing import Any
from uuid import uuid4

from fairchild.context import set_current_job, get_pending_children
from fairchild.fairchild import Fairchild
from fairchild.job import Job, JobState
from fairchild.record import Record
from fairchild.task import get_task, get_task_schemas


class Worker:
    """A worker that processes jobs from a specific queue."""

    def __init__(
        self,
        fairchild: Fairchild,
        queue: str,
        worker_id: int,
        pool: "WorkerPool | None" = None,
    ):
        self.fairchild = fairchild
        self.queue = queue
        self.worker_id = worker_id
        self.pool = pool
        self._running = False
        self._current_job: Job | None = None

    @property
    def name(self) -> str:
        return f"{self.queue}:{self.worker_id}"

    async def run(self):
        """Main worker loop."""
        self._running = True
        print(f"[{self.name}] Started")

        while self._running:
            try:
                # Check if pool is paused
                if self.pool and self.pool.is_paused:
                    await asyncio.sleep(1.0)
                    continue

                job = await self._fetch_job()

                if job is None:
                    # No job available, wait before polling again
                    await asyncio.sleep(1.0)
                    continue

                self._current_job = job
                await self._execute_job(job)
                self._current_job = None

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[{self.name}] Error in worker loop: {e}")
                await asyncio.sleep(1.0)

        print(f"[{self.name}] Stopped")

    async def _fetch_job(self) -> Job | None:
        """Fetch the next available job from the queue."""
        # Find and lock a ready job
        # Jobs are available if:
        # 1. state = 'available' and scheduled_at <= now()
        # 2. All deps (job IDs) are completed
        select_query = """
            SELECT id FROM fairchild_jobs
            WHERE queue = $1
              AND state = 'available'
              AND scheduled_at <= now()
              AND (
                  -- Either no deps or all deps completed
                  deps = '{}'
                  OR NOT EXISTS (
                      SELECT 1 FROM fairchild_jobs dep
                      WHERE dep.id::text = ANY(fairchild_jobs.deps)
                        AND dep.state != 'completed'
                  )
              )
            ORDER BY priority, scheduled_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """

        # Then update and return it
        update_query = """
            UPDATE fairchild_jobs
            SET state = 'running',
                attempted_at = now(),
                attempt = attempt + 1,
                updated_at = now()
            WHERE id = $1
            RETURNING *
        """

        async with self.fairchild._pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(select_query, self.queue)
                if row is None:
                    return None

                row = await conn.fetchrow(update_query, row["id"])

        return Job.from_row(dict(row))

    async def _resolve_future_args(self, args: dict) -> dict:
        """Resolve any __future__ markers in args to their actual values."""

        async def _resolve(obj):
            if isinstance(obj, dict):
                # Check if this is a future marker
                if "__future__" in obj and len(obj) == 1:
                    job_id = obj["__future__"]
                    # Fetch the recorded result from the completed job
                    query = """
                        SELECT recorded FROM fairchild_jobs
                        WHERE id = $1 AND state = 'completed'
                    """
                    from uuid import UUID

                    result = await self.fairchild._pool.fetchval(query, UUID(job_id))
                    if result is not None:
                        import json

                        return json.loads(result)
                    return None
                # Regular dict - recurse
                return {k: await _resolve(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [await _resolve(item) for item in obj]
            return obj

        return await _resolve(args)

    async def _execute_job(self, job: Job):
        """Execute a job."""
        print(f"[{self.name}] Processing job {job.id} ({job.task_name})")

        try:
            task = get_task(job.task_name)
        except ValueError as e:
            await self._fail_job(job, str(e), discard=True)
            return

        try:
            # Build arguments, resolving any futures
            kwargs = await self._resolve_future_args(dict(job.args))

            # Inject job if the task accepts it
            if task._accepts_job:
                kwargs["job"] = job

            # Set context so spawned tasks know they're inside a worker
            set_current_job(job, self.fairchild)

            try:
                # Execute the task
                result = task.fn(**kwargs)

                # Handle async tasks
                if asyncio.iscoroutine(result):
                    result = await result

                # Get any child jobs that were queued during execution
                pending_children = get_pending_children()
            finally:
                # Always clear context after execution
                set_current_job(None)

            # Insert any child jobs that were spawned
            for child_job in pending_children:
                await self.fairchild._insert_job(child_job)

            # Handle Record() return values
            recorded_value = None
            if isinstance(result, Record):
                recorded_value = result.value

            # Check if this job spawned children - if so, wait for them
            has_children = len(pending_children) > 0
            if has_children:
                # Keep job in running state, it will be completed when children finish
                await self._mark_waiting_for_children(job, recorded_value)
                print(f"[{self.name}] Job {job.id} waiting for children to complete")
            else:
                await self._complete_job(job, recorded_value)
                print(f"[{self.name}] Completed job {job.id}")

        except Exception as e:
            error_info = {
                "attempt": job.attempt,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "at": datetime.utcnow().isoformat(),
            }

            if job.attempt >= job.max_attempts:
                await self._fail_job(job, str(e), error_info=error_info, discard=True)
                print(
                    f"[{self.name}] Discarded job {job.id} after {job.attempt} attempts: {e}"
                )
            else:
                await self._fail_job(job, str(e), error_info=error_info, discard=False)
                print(
                    f"[{self.name}] Job {job.id} failed (attempt {job.attempt}/{job.max_attempts}): {e}"
                )

    async def _complete_job(self, job: Job, recorded: Any | None):
        """Mark a job as completed."""
        query = """
            UPDATE fairchild_jobs
            SET state = 'completed',
                completed_at = now(),
                recorded = $2,
                updated_at = now()
            WHERE id = $1
        """

        recorded_json = json.dumps(recorded) if recorded is not None else None
        await self.fairchild._pool.execute(query, job.id, recorded_json)

        # Check if this completion unblocks jobs waiting on this one
        await self._check_child_deps(job)

        # Check if this completion allows a parent job to complete
        if job.parent_id:
            await self._check_parent_completion(job.parent_id)

    async def _has_pending_children(self, job: Job) -> bool:
        """Check if this job has any pending (non-completed) children."""
        query = """
            SELECT EXISTS(
                SELECT 1 FROM fairchild_jobs
                WHERE parent_id = $1
                  AND state != 'completed'
            )
        """
        return await self.fairchild._pool.fetchval(query, job.id)

    async def _mark_waiting_for_children(self, job: Job, recorded: Any | None):
        """Mark a job as waiting for children (stays in running state but stores result)."""
        # Store the recorded value so we can use it when completing later
        query = """
            UPDATE fairchild_jobs
            SET recorded = $2,
                updated_at = now()
            WHERE id = $1
        """
        recorded_json = json.dumps(recorded) if recorded is not None else None
        await self.fairchild._pool.execute(query, job.id, recorded_json)

    async def _check_parent_completion(self, parent_id):
        """Check if a parent job can be completed (all children done)."""
        # Check if all children are completed
        query = """
            SELECT NOT EXISTS(
                SELECT 1 FROM fairchild_jobs
                WHERE parent_id = $1
                  AND state != 'completed'
            )
        """
        all_children_done = await self.fairchild._pool.fetchval(query, parent_id)

        if all_children_done:
            # Complete the parent job
            complete_query = """
                UPDATE fairchild_jobs
                SET state = 'completed',
                    completed_at = now(),
                    updated_at = now()
                WHERE id = $1
                  AND state = 'running'
            """
            await self.fairchild._pool.execute(complete_query, parent_id)

            # Check if the parent itself has a parent
            parent_parent_query = """
                SELECT parent_id FROM fairchild_jobs WHERE id = $1
            """
            parent_parent_id = await self.fairchild._pool.fetchval(
                parent_parent_query, parent_id
            )
            if parent_parent_id:
                await self._check_parent_completion(parent_parent_id)

    async def _check_child_deps(self, completed_job: Job):
        """Check if completing this job unblocks jobs waiting on it as a dependency."""
        # Find jobs that have this job's ID in their deps array and are scheduled
        # If all their deps are now completed, make them available
        job_id_str = str(completed_job.id)
        query = """
            UPDATE fairchild_jobs
            SET state = 'available', updated_at = now()
            WHERE state = 'scheduled'
              AND $1 = ANY(deps)
              AND NOT EXISTS (
                  SELECT 1 FROM fairchild_jobs dep
                  WHERE dep.id::text = ANY(fairchild_jobs.deps)
                    AND dep.state != 'completed'
              )
        """
        await self.fairchild._pool.execute(query, job_id_str)

    async def _fail_job(
        self,
        job: Job,
        error: str,
        error_info: dict | None = None,
        discard: bool = False,
    ):
        """Mark a job as failed or discarded."""
        new_state = "discarded" if discard else "available"

        if error_info:
            # Append error to errors array
            query = """
                UPDATE fairchild_jobs
                SET state = $2,
                    errors = errors || $3::jsonb,
                    updated_at = now()
                WHERE id = $1
            """
            await self.fairchild._pool.execute(
                query,
                job.id,
                new_state,
                json.dumps(error_info),
            )
        else:
            query = """
                UPDATE fairchild_jobs
                SET state = $2, updated_at = now()
                WHERE id = $1
            """
            await self.fairchild._pool.execute(query, job.id, new_state)

    def stop(self):
        """Signal the worker to stop."""
        self._running = False


class WorkerPool:
    """Manages multiple workers across queues."""

    def __init__(self, fairchild: Fairchild, queue_config: dict[str, int]):
        """
        Args:
            fairchild: Fairchild instance
            queue_config: Dict mapping queue name to worker count
        """
        self.fairchild = fairchild
        self.queue_config = queue_config
        self.workers: list[Worker] = []
        self._tasks: list[asyncio.Task] = []
        self._heartbeat_task: asyncio.Task | None = None

        # Worker pool identity
        self.id = uuid4()
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self._paused = False

    async def run(self):
        """Start all workers and wait for them."""
        # Register this worker pool
        await self._register()

        # Create workers
        for queue, count in self.queue_config.items():
            for i in range(count):
                worker = Worker(self.fairchild, queue, i, pool=self)
                self.workers.append(worker)

        # Start worker tasks
        self._tasks = [asyncio.create_task(worker.run()) for worker in self.workers]

        # Start heartbeat task
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        total = sum(self.queue_config.values())
        print(f"Started {total} workers across {len(self.queue_config)} queues")

        # Wait for all tasks (they run until cancelled)
        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            pass

    async def _register(self):
        """Register this worker pool in the database."""
        query = """
            INSERT INTO fairchild_workers (id, hostname, pid, queues, tasks, state)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, 'running')
            ON CONFLICT (id) DO UPDATE SET
                hostname = EXCLUDED.hostname,
                pid = EXCLUDED.pid,
                queues = EXCLUDED.queues,
                tasks = EXCLUDED.tasks,
                state = 'running',
                last_heartbeat_at = now()
        """
        # asyncpg requires JSON as a string for jsonb columns
        import json as json_module

        tasks = get_task_schemas()
        await self.fairchild._pool.execute(
            query,
            self.id,
            self.hostname,
            self.pid,
            json_module.dumps(self.queue_config),
            json_module.dumps(tasks),
        )
        print(f"Registered worker pool {self.id} ({self.hostname}:{self.pid})")
        print(f"  Tasks: {[t['name'] for t in tasks]}")

    async def _heartbeat_loop(self):
        """Periodically send heartbeats and check for pause state."""
        while True:
            try:
                await asyncio.sleep(5)  # Heartbeat every 5 seconds
                await self._send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat error: {e}")

    async def _send_heartbeat(self):
        """Send a heartbeat and check pause state."""
        active_jobs = sum(1 for w in self.workers if w._current_job is not None)

        query = """
            UPDATE fairchild_workers
            SET last_heartbeat_at = now(),
                active_jobs = $2
            WHERE id = $1
            RETURNING state
        """
        state = await self.fairchild._pool.fetchval(query, self.id, active_jobs)

        # Update pause state based on database
        new_paused = state == "paused"
        if new_paused != self._paused:
            self._paused = new_paused
            if self._paused:
                print(f"Worker pool {self.id} paused")
            else:
                print(f"Worker pool {self.id} resumed")

    @property
    def is_paused(self) -> bool:
        return self._paused

    async def _unregister(self):
        """Mark this worker pool as stopped."""
        query = """
            UPDATE fairchild_workers
            SET state = 'stopped', active_jobs = 0
            WHERE id = $1
        """
        await self.fairchild._pool.execute(query, self.id)

    async def shutdown(self):
        """Gracefully shutdown all workers."""
        print("Shutting down workers...")

        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Signal all workers to stop
        for worker in self.workers:
            worker.stop()

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to finish
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Unregister from database
        await self._unregister()

        print("All workers stopped")
