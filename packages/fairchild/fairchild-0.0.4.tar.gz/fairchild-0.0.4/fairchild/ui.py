from aiohttp import web
import json
from pathlib import Path

from fairchild.fairchild import Fairchild

# Load templates from files
_TEMPLATE_DIR = Path(__file__).parent / "templates"

# Type-safe app key for storing Fairchild instance
_fairchild_key: web.AppKey[Fairchild] = web.AppKey("fairchild", Fairchild)


def _load_template(name: str) -> str:
    """Load a template file."""
    return (_TEMPLATE_DIR / name).read_text()


def create_app(fairchild: Fairchild) -> web.Application:
    """Create the web UI application."""
    app = web.Application()
    app[_fairchild_key] = fairchild

    app.router.add_get("/", index)
    app.router.add_get("/jobs/{job_id}", job_page)
    app.router.add_get("/api/stats", api_stats)
    app.router.add_get("/api/jobs", api_jobs)
    app.router.add_post("/api/jobs", api_enqueue_job)
    app.router.add_get("/api/jobs/{job_id}", api_job_detail)
    app.router.add_get("/api/jobs/{job_id}/family", api_job_family)
    app.router.add_get("/api/queues", api_queues)
    app.router.add_get("/api/tasks", api_tasks)
    app.router.add_get("/api/timeseries", api_timeseries)
    app.router.add_get("/api/workers", api_workers)
    app.router.add_post("/api/workers/{worker_id}/pause", api_worker_pause)
    app.router.add_post("/api/workers/{worker_id}/resume", api_worker_resume)

    return app


async def index(request: web.Request) -> web.Response:
    """Serve the main dashboard HTML."""
    html = _load_template("dashboard.html")
    return web.Response(text=html, content_type="text/html")


async def job_page(request: web.Request) -> web.Response:
    """Serve the job detail page."""
    job_id = request.match_info["job_id"]
    html = _load_template("job.html").replace("{{JOB_ID}}", job_id)
    return web.Response(text=html, content_type="text/html")


async def api_stats(request: web.Request) -> web.Response:
    """Get overall job statistics."""
    fairchild: Fairchild = request.app[_fairchild_key]

    query = """
        SELECT
            state,
            COUNT(*) as count
        FROM fairchild_jobs
        GROUP BY state
    """

    rows = await fairchild._pool.fetch(query)
    stats = {row["state"]: row["count"] for row in rows}

    return web.json_response(stats)


async def api_queues(request: web.Request) -> web.Response:
    """Get queue statistics."""
    fairchild: Fairchild = request.app[_fairchild_key]

    query = """
        SELECT
            queue,
            state,
            COUNT(*) as count
        FROM fairchild_jobs
        GROUP BY queue, state
        ORDER BY queue, state
    """

    rows = await fairchild._pool.fetch(query)

    queues = {}
    for row in rows:
        queue = row["queue"]
        if queue not in queues:
            queues[queue] = {}
        queues[queue][row["state"]] = row["count"]

    return web.json_response(queues)


async def api_tasks(request: web.Request) -> web.Response:
    """Get list of registered tasks with parameter info."""
    import inspect
    from fairchild.task import _task_registry

    tasks = []
    for name, task in sorted(_task_registry.items()):
        # Extract parameter info from function signature
        sig = inspect.signature(task.fn)
        params = []
        for param_name, param in sig.parameters.items():
            # Skip special injected parameters
            if param_name in ("job", "workflow"):
                continue

            param_info = {"name": param_name}

            # Add type annotation if present
            if param.annotation != inspect.Parameter.empty:
                try:
                    param_info["type"] = param.annotation.__name__
                except AttributeError:
                    param_info["type"] = str(param.annotation)

            # Add default value if present
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
                param_info["required"] = False
            else:
                param_info["required"] = True

            params.append(param_info)

        # Get docstring
        docstring = inspect.getdoc(task.fn)

        tasks.append(
            {
                "name": name,
                "queue": task.queue,
                "priority": task.priority,
                "max_attempts": task.max_attempts,
                "tags": task.tags,
                "params": params,
                "docstring": docstring,
            }
        )

    return web.json_response(tasks)


async def api_jobs(request: web.Request) -> web.Response:
    """Get jobs with filtering and pagination."""
    fairchild: Fairchild = request.app[_fairchild_key]

    # Parse query params
    state = request.query.get("state")
    queue = request.query.get("queue")
    limit = int(request.query.get("limit", 50))
    offset = int(request.query.get("offset", 0))

    # Build query
    conditions = []
    params = []
    param_idx = 1

    if state:
        conditions.append(f"state = ${param_idx}")
        params.append(state)
        param_idx += 1

    if queue:
        conditions.append(f"queue = ${param_idx}")
        params.append(queue)
        param_idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT
            id, task_name, queue, args,
            parent_id, deps,
            state, priority, scheduled_at,
            attempted_at, completed_at, attempt, max_attempts,
            recorded, errors, tags,
            inserted_at, updated_at
        FROM fairchild_jobs
        {where}
        ORDER BY inserted_at DESC
        LIMIT ${param_idx} OFFSET ${param_idx + 1}
    """
    params.extend([limit, offset])

    rows = await fairchild._pool.fetch(query, *params)

    jobs = []
    for row in rows:
        job = dict(row)
        job["id"] = str(job["id"])
        job["parent_id"] = str(job["parent_id"]) if job["parent_id"] else None
        job["scheduled_at"] = (
            job["scheduled_at"].isoformat() if job["scheduled_at"] else None
        )
        job["attempted_at"] = (
            job["attempted_at"].isoformat() if job["attempted_at"] else None
        )
        job["completed_at"] = (
            job["completed_at"].isoformat() if job["completed_at"] else None
        )
        job["inserted_at"] = (
            job["inserted_at"].isoformat() if job["inserted_at"] else None
        )
        job["updated_at"] = job["updated_at"].isoformat() if job["updated_at"] else None
        jobs.append(job)

    return web.json_response(jobs)


async def api_enqueue_job(request: web.Request) -> web.Response:
    """Enqueue a new job via JSON API.

    Request body:
        {
            "task": "module.task_name",      # Required: registered task name
            "args": {"key": "value"},        # Optional: task arguments (default: {})
            "queue": "custom_queue",         # Optional: override task's default queue
            "priority": 3,                   # Optional: 0-9, lower = higher priority
            "scheduled_at": "ISO8601"        # Optional: schedule for later execution
        }

    Response:
        {
            "id": "uuid",
            "task": "module.task_name",
            "queue": "default",
            "state": "available",
            "scheduled_at": "ISO8601"
        }
    """
    from datetime import datetime
    from fairchild.task import get_task

    fairchild: Fairchild = request.app[_fairchild_key]

    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    # Validate required fields
    task_name = body.get("task")
    if not task_name:
        return web.json_response({"error": "Missing required field: task"}, status=400)

    # Look up the task
    try:
        task = get_task(task_name)
    except ValueError:
        return web.json_response({"error": f"Unknown task: {task_name}"}, status=404)

    # Parse optional fields
    args = body.get("args", {})
    if not isinstance(args, dict):
        return web.json_response({"error": "args must be an object"}, status=400)

    priority = body.get("priority")
    if priority is not None:
        if not isinstance(priority, int) or not (0 <= priority <= 9):
            return web.json_response(
                {"error": "priority must be an integer 0-9"}, status=400
            )

    scheduled_at = None
    if "scheduled_at" in body:
        try:
            scheduled_at = datetime.fromisoformat(
                body["scheduled_at"].replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            return web.json_response(
                {"error": "scheduled_at must be a valid ISO8601 datetime"}, status=400
            )

    # Enqueue the job
    try:
        job = await fairchild.enqueue(
            task=task,
            args=args,
            priority=priority,
            scheduled_at=scheduled_at,
        )
    except Exception as e:
        return web.json_response({"error": f"Failed to enqueue job: {e}"}, status=500)

    return web.json_response(
        {
            "id": str(job.id),
            "task": job.task_name,
            "queue": job.queue,
            "state": job.state.value,
            "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
        },
        status=201,
    )


async def api_job_detail(request: web.Request) -> web.Response:
    """Get details for a specific job."""
    fairchild: Fairchild = request.app[_fairchild_key]
    job_id = request.match_info["job_id"]

    query = """
        SELECT
            id, task_name, queue, args,
            parent_id, deps,
            state, priority, scheduled_at,
            attempted_at, completed_at, attempt, max_attempts,
            recorded, errors, tags,
            inserted_at, updated_at
        FROM fairchild_jobs
        WHERE id = $1
    """

    row = await fairchild._pool.fetchrow(query, job_id)

    if not row:
        return web.json_response({"error": "Job not found"}, status=404)

    job = dict(row)
    job["id"] = str(job["id"])
    job["parent_id"] = str(job["parent_id"]) if job["parent_id"] else None
    job["scheduled_at"] = (
        job["scheduled_at"].isoformat() if job["scheduled_at"] else None
    )
    job["attempted_at"] = (
        job["attempted_at"].isoformat() if job["attempted_at"] else None
    )
    job["completed_at"] = (
        job["completed_at"].isoformat() if job["completed_at"] else None
    )
    job["inserted_at"] = job["inserted_at"].isoformat() if job["inserted_at"] else None
    job["updated_at"] = job["updated_at"].isoformat() if job["updated_at"] else None

    return web.json_response(job)


async def api_job_family(request: web.Request) -> web.Response:
    """Get the family tree for a job (ancestors and descendants)."""
    from uuid import UUID

    fairchild: Fairchild = request.app[_fairchild_key]
    job_id_str = request.match_info["job_id"]

    try:
        job_id = UUID(job_id_str)
    except ValueError:
        return web.json_response({"error": "Invalid job ID"}, status=400)

    # Find the root job (traverse up to find the topmost parent)
    root_query = """
        WITH RECURSIVE ancestors AS (
            SELECT id, parent_id, 0 as depth
            FROM fairchild_jobs
            WHERE id = $1

            UNION ALL

            SELECT j.id, j.parent_id, a.depth + 1
            FROM fairchild_jobs j
            INNER JOIN ancestors a ON j.id = a.parent_id
        )
        SELECT id FROM ancestors
        WHERE parent_id IS NULL
        LIMIT 1
    """
    root_id = await fairchild._pool.fetchval(root_query, job_id)

    if not root_id:
        return web.json_response({"error": "Job not found"}, status=404)

    # Get all descendants from the root
    family_query = """
        WITH RECURSIVE family AS (
            SELECT id, task_name, parent_id, state, deps, recorded,
                   attempted_at, completed_at, attempt, max_attempts
            FROM fairchild_jobs
            WHERE id = $1

            UNION ALL

            SELECT j.id, j.task_name, j.parent_id, j.state, j.deps, j.recorded,
                   j.attempted_at, j.completed_at, j.attempt, j.max_attempts
            FROM fairchild_jobs j
            INNER JOIN family f ON j.parent_id = f.id
        )
        SELECT * FROM family
    """
    rows = await fairchild._pool.fetch(family_query, root_id)

    jobs = []
    for row in rows:
        job = dict(row)
        job["id"] = str(job["id"])
        job["parent_id"] = str(job["parent_id"]) if job["parent_id"] else None
        job["attempted_at"] = (
            job["attempted_at"].isoformat() if job["attempted_at"] else None
        )
        job["completed_at"] = (
            job["completed_at"].isoformat() if job["completed_at"] else None
        )
        jobs.append(job)

    return web.json_response({"root_id": str(root_id), "jobs": jobs})


async def api_timeseries(request: web.Request) -> web.Response:
    """Get job counts per minute for the last 60 minutes."""
    fairchild: Fairchild = request.app[_fairchild_key]

    # Get jobs created per minute
    query_inserted = """
        SELECT
            date_trunc('minute', inserted_at) as minute,
            COUNT(*) as count
        FROM fairchild_jobs
        WHERE inserted_at > now() - interval '60 minutes'
        GROUP BY minute
        ORDER BY minute
    """

    # Get jobs completed per minute
    query_completed = """
        SELECT
            date_trunc('minute', completed_at) as minute,
            COUNT(*) as count
        FROM fairchild_jobs
        WHERE completed_at > now() - interval '60 minutes'
          AND state = 'completed'
        GROUP BY minute
        ORDER BY minute
    """

    # Get jobs failed/discarded per minute
    query_failed = """
        SELECT
            date_trunc('minute', updated_at) as minute,
            COUNT(*) as count
        FROM fairchild_jobs
        WHERE updated_at > now() - interval '60 minutes'
          AND state IN ('failed', 'discarded')
        GROUP BY minute
        ORDER BY minute
    """

    inserted_rows = await fairchild._pool.fetch(query_inserted)
    completed_rows = await fairchild._pool.fetch(query_completed)
    failed_rows = await fairchild._pool.fetch(query_failed)

    # Build minute-by-minute data
    inserted = {row["minute"].isoformat(): row["count"] for row in inserted_rows}
    completed = {row["minute"].isoformat(): row["count"] for row in completed_rows}
    failed = {row["minute"].isoformat(): row["count"] for row in failed_rows}

    return web.json_response(
        {
            "inserted": inserted,
            "completed": completed,
            "failed": failed,
        }
    )


async def api_workers(request: web.Request) -> web.Response:
    """Get list of active workers."""
    fairchild: Fairchild = request.app[_fairchild_key]

    # Get workers that have heartbeated in the last 30 seconds (alive)
    # or are in stopped state (for recent history)
    query = """
        SELECT
            id, hostname, pid, queues, active_jobs, state,
            started_at, last_heartbeat_at, paused_at
        FROM fairchild_workers
        WHERE last_heartbeat_at > now() - interval '30 seconds'
           OR state = 'stopped'
        ORDER BY started_at DESC
    """

    rows = await fairchild._pool.fetch(query)

    workers = []
    for row in rows:
        worker = dict(row)
        worker["id"] = str(worker["id"])
        worker["started_at"] = (
            worker["started_at"].isoformat() if worker["started_at"] else None
        )
        worker["last_heartbeat_at"] = (
            worker["last_heartbeat_at"].isoformat()
            if worker["last_heartbeat_at"]
            else None
        )
        worker["paused_at"] = (
            worker["paused_at"].isoformat() if worker["paused_at"] else None
        )
        # Check if worker is actually alive (heartbeat within 15s)
        from datetime import datetime, timezone

        if worker["last_heartbeat_at"]:
            last_hb = datetime.fromisoformat(worker["last_heartbeat_at"])
            if last_hb.tzinfo is None:
                last_hb = last_hb.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - last_hb).total_seconds()
            worker["alive"] = age < 15 and worker["state"] != "stopped"
        else:
            worker["alive"] = False
        workers.append(worker)

    return web.json_response(workers)


async def api_worker_pause(request: web.Request) -> web.Response:
    """Pause a worker."""
    fairchild: Fairchild = request.app[_fairchild_key]
    worker_id = request.match_info["worker_id"]

    query = """
        UPDATE fairchild_workers
        SET state = 'paused', paused_at = now()
        WHERE id = $1 AND state = 'running'
        RETURNING id
    """

    result = await fairchild._pool.fetchval(query, worker_id)

    if not result:
        return web.json_response(
            {"error": "Worker not found or not running"}, status=404
        )

    return web.json_response({"status": "paused", "id": worker_id})


async def api_worker_resume(request: web.Request) -> web.Response:
    """Resume a paused worker."""
    fairchild: Fairchild = request.app[_fairchild_key]
    worker_id = request.match_info["worker_id"]

    query = """
        UPDATE fairchild_workers
        SET state = 'running', paused_at = NULL
        WHERE id = $1 AND state = 'paused'
        RETURNING id
    """

    result = await fairchild._pool.fetchval(query, worker_id)

    if not result:
        return web.json_response(
            {"error": "Worker not found or not paused"}, status=404
        )

    return web.json_response({"status": "running", "id": worker_id})
