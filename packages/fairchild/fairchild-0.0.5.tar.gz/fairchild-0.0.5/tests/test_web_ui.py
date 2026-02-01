"""Integration tests for the Fairchild web UI."""

import os
import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer

# Skip if no database URL is provided
pytestmark = pytest.mark.skipif(
    not os.environ.get("FAIRCHILD_DATABASE_URL"),
    reason="FAIRCHILD_DATABASE_URL not set",
)


@pytest.fixture
def db_url():
    """Get database URL from environment, converting to test database."""
    url = os.environ.get("FAIRCHILD_DATABASE_URL")
    # Replace _development with _test to avoid blowing away dev data
    if url and "_development" in url:
        url = url.replace("_development", "_test")
    return url


@pytest_asyncio.fixture
async def fairchild_app(db_url):
    """Create a Fairchild instance and web app for testing."""
    from fairchild.fairchild import Fairchild
    from fairchild.ui import create_app
    from fairchild.db.migrations import migrate, drop_all

    fairchild = Fairchild(db_url)
    await fairchild.connect()

    # Install schema (force to ensure clean state)
    await drop_all(fairchild._pool)
    await migrate(fairchild._pool)

    app = create_app(fairchild)

    yield app

    await fairchild.disconnect()


@pytest_asyncio.fixture
async def client(fairchild_app):
    """Create a test client for the web app."""
    async with TestClient(TestServer(fairchild_app)) as client:
        yield client


@pytest_asyncio.fixture
async def client_with_worker(fairchild_app):
    """Create a test client with a simulated worker registration."""
    import json
    from uuid import uuid4
    from fairchild.task import get_task_schemas
    from fairchild.ui import _fairchild_key

    # Import tasks to register them in _task_registry
    import examples.tasks  # noqa: F401

    fairchild = fairchild_app[_fairchild_key]

    # Register a fake worker with task schemas (simulates what real workers do)
    worker_id = uuid4()
    tasks = get_task_schemas()
    query = """
        INSERT INTO fairchild_workers (id, hostname, pid, queues, tasks, state)
        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, 'running')
    """
    await fairchild._pool.execute(
        query,
        worker_id,
        "test-host",
        12345,
        json.dumps({"default": 1}),
        json.dumps(tasks),
    )

    async with TestClient(TestServer(fairchild_app)) as client:
        yield client


@pytest.mark.asyncio
async def test_dashboard_returns_html(client):
    """Test that the dashboard endpoint returns HTML."""
    resp = await client.get("/")
    assert resp.status == 200
    assert resp.content_type == "text/html"
    text = await resp.text()
    assert "<html" in text.lower()


@pytest.mark.asyncio
async def test_api_stats_returns_json(client):
    """Test that the stats API returns JSON with job counts."""
    resp = await client.get("/api/stats")
    assert resp.status == 200
    assert resp.content_type == "application/json"
    data = await resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_api_jobs_returns_list(client):
    """Test that the jobs API returns a list."""
    resp = await client.get("/api/jobs")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_api_queues_returns_dict(client):
    """Test that the queues API returns a dict."""
    resp = await client.get("/api/queues")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_api_tasks_returns_list(client):
    """Test that the tasks API returns a list of registered tasks."""
    # Import tasks to register them
    import examples.tasks  # noqa: F401

    resp = await client.get("/api/tasks")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_api_workers_returns_list(client):
    """Test that the workers API returns a list."""
    resp = await client.get("/api/workers")
    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_api_timeseries_returns_data(client):
    """Test that the timeseries API returns time series data."""
    resp = await client.get("/api/timeseries")
    assert resp.status == 200
    data = await resp.json()
    assert "inserted" in data
    assert "completed" in data
    assert "failed" in data


@pytest.mark.asyncio
async def test_enqueue_job_via_api(client_with_worker):
    """Test enqueuing a job through the JSON API."""
    resp = await client_with_worker.post(
        "/api/jobs", json={"task": "examples.tasks.add", "args": {"a": 10, "b": 20}}
    )
    assert resp.status == 201
    data = await resp.json()
    assert "id" in data
    assert data["task"] == "examples.tasks.add"
    assert data["state"] == "available"


@pytest.mark.asyncio
async def test_enqueue_and_fetch_job(client_with_worker):
    """Test enqueuing a job and fetching its details."""
    # Enqueue a job
    resp = await client_with_worker.post(
        "/api/jobs", json={"task": "examples.tasks.hello", "args": {"name": "TestUser"}}
    )
    assert resp.status == 201
    enqueue_data = await resp.json()
    job_id = enqueue_data["id"]

    # Fetch the job details
    resp = await client_with_worker.get(f"/api/jobs/{job_id}")
    assert resp.status == 200
    job_data = await resp.json()
    assert job_data["id"] == job_id
    assert job_data["task_name"] == "examples.tasks.hello"
    # args may be returned as JSON string or dict depending on DB driver
    args = job_data["args"]
    if isinstance(args, str):
        import json

        args = json.loads(args)
    assert args["name"] == "TestUser"


@pytest.mark.asyncio
async def test_job_page_returns_html(client_with_worker):
    """Test that the job detail page returns HTML."""
    # First enqueue a job to get a valid ID
    resp = await client_with_worker.post(
        "/api/jobs", json={"task": "examples.tasks.add", "args": {"a": 1, "b": 2}}
    )
    data = await resp.json()
    job_id = data["id"]

    # Fetch the job page
    resp = await client_with_worker.get(f"/jobs/{job_id}")
    assert resp.status == 200
    assert resp.content_type == "text/html"
    text = await resp.text()
    assert job_id in text


@pytest.mark.asyncio
async def test_enqueue_invalid_task_returns_404(client):
    """Test that enqueuing an unknown task returns 404."""
    resp = await client.post("/api/jobs", json={"task": "nonexistent.task", "args": {}})
    assert resp.status == 404
    data = await resp.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_enqueue_missing_task_returns_400(client):
    """Test that enqueuing without a task name returns 400."""
    resp = await client.post("/api/jobs", json={"args": {"a": 1}})
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_get_nonexistent_job_returns_404(client):
    """Test that fetching a nonexistent job returns 404."""
    resp = await client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert resp.status == 404
    data = await resp.json()
    assert "error" in data
