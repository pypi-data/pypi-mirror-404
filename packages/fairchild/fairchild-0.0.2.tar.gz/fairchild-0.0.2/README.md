# Fairchild

A PostgreSQL-backed job queue and simple workflow engine. Inspired by [Oban](https://oban.pro) and [Faktory](https://contribsys.com/faktory/), among others.

## Installation

```bash
pip install fairchild
```

Requires PostgreSQL 12+.

## Quick Start

1. Define a task:

```python
# tasks.py
from fairchild import task, Record

@task(queue="default")
def send_email(to: str, subject: str, body: str):
    # Your email sending logic here
    print(f"Sending email to {to}: {subject}")
    return Record({"sent": True})
```

2. Set up the database and enqueue a job:

```python
import asyncio
from fairchild import Fairchild
import tasks  # Import to register tasks

async def main():
    fairchild = Fairchild("postgresql://localhost/myapp")
    await fairchild.connect()
    
    # Create the jobs table
    await fairchild.install()
    
    # Enqueue a job
    tasks.send_email.enqueue(
        to="user@example.com",
        subject="Hello",
        body="Welcome to Fairchild!"
    )

asyncio.run(main())
```

3. Run a worker:

```bash
export FAIRCHILD_DATABASE_URL="postgresql://localhost/myapp"
fairchild worker --import tasks
```

## Defining Tasks

Use the `@task` decorator to define a task:

```python
from fairchild import task

@task(
    queue="default",      # Queue name (default: "default")
    max_attempts=3,       # Retry attempts on failure (default: 3)
    priority=5,           # 0-9, lower = higher priority (default: 5)
    tags=["email"],       # Tags for filtering/categorization
)
def my_task(arg1: str, arg2: int):
    # Task logic here
    pass
```

### Returning Results

Use `Record()` to persist a task's result for use by downstream workflow jobs:

```python
from fairchild import task, Record

@task()
def fetch_data(url: str):
    data = requests.get(url).json()
    return Record(data)  # Stored in the database
```

## Enqueuing Jobs

### Basic Enqueue

```python
my_task.enqueue(arg1="hello", arg2=42)
```

### Schedule for Later

```python
# Run in 30 minutes
my_task.enqueue_in(minutes=30, arg1="hello", arg2=42)

# Run at a specific time
from datetime import datetime, timezone
my_task.enqueue_at(
    datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
    arg1="hello",
    arg2=42
)
```

### With Options

```python
my_task.enqueue(
    arg1="hello",
    arg2=42,
    _priority=1,          # Override default priority
    _queue="high",        # Override default queue
)
```

## Dynamic Workflows

Fairchild uses a futures-based approach to workflows. Instead of explicitly declaring a DAG, you write natural Python code—call tasks, get futures, pass them around. Dependencies are inferred automatically.

### How It Works

When a task calls another task from inside a worker:
1. A child job is spawned (not executed immediately)
2. A `Future` is returned representing the pending result
3. If you pass that `Future` to another task, a dependency is created
4. The downstream task won't run until the upstream job completes

### Basic Example

```python
from fairchild import task, Record

@task()
def fetch_data(url: str):
    data = requests.get(url).json()
    return Record(data)

@task()
def process(data: dict):
    # Process the data
    return Record({"processed": True})

@task()
def orchestrator():
    # Calling a task returns a Future
    data = fetch_data(url="https://api.example.com/data")
    
    # Passing the Future creates a dependency
    # process() won't run until fetch_data() completes
    result = process(data=data)
    
    return Record({"started": True})
```

### Fan-Out / Fan-In (Map-Reduce)

The futures model makes parallel processing with aggregation natural:

```python
@task()
def multiply(x: int, y: int):
    return Record(x * y)

@task()
def sum_results(values: list):
    return Record(sum(values))

@task()
def orchestrator(items: list[int]):
    # Fan-out: spawn parallel tasks, collect futures
    futures = []
    for item in items:
        future = multiply(x=item, y=2)
        futures.append(future)
    
    # Fan-in: pass all futures to aggregator
    # sum_results won't run until ALL multiply jobs complete
    total = sum_results(values=futures)
    
    return Record({"spawned": len(items) + 1})
```

When `orchestrator([1, 2, 3])` runs, it creates this DAG:

```
orchestrator
    ├── multiply(1, 2) ──┐
    ├── multiply(2, 2) ──┼── sum_results([...])
    └── multiply(3, 2) ──┘
```

### Nested Workflows

Since it's just function calls, workflows can be arbitrarily nested:

```python
@task()
def process_batch(batch_id: int):
    # This task can spawn its own sub-workflow
    futures = [process_item(item_id=i) for i in get_items(batch_id)]
    return aggregate(results=futures)

@task()
def run_all_batches():
    # Top-level orchestrator spawns batch processors
    futures = [process_batch(batch_id=i) for i in range(10)]
    return final_summary(batch_results=futures)
```

### Accessing Results

When a Future is passed to a downstream task, Fairchild automatically resolves it to the actual value before the task runs:

```python
@task()
def fetch_price(symbol: str):
    price = get_stock_price(symbol)
    return Record({"symbol": symbol, "price": price})

@task()
def calculate_total(prices: list):
    # By the time this runs, prices is a list of actual values,
    # not Futures - Fairchild resolves them automatically
    total = sum(p["price"] for p in prices)
    return Record({"total": total})

@task()
def portfolio_value(symbols: list[str]):
    futures = [fetch_price(symbol=s) for s in symbols]
    return calculate_total(prices=futures)
```

## Workers

### CLI

```bash
# Basic worker
fairchild worker --import myapp.tasks

# Multiple queues with concurrency
fairchild worker --import myapp.tasks --queues default,high,low --concurrency 10

# Specific queues only
fairchild worker --import myapp.tasks --queues critical
```

### Programmatic

```python
from fairchild import Fairchild
from fairchild.worker import WorkerPool

async def main():
    fairchild = Fairchild("postgresql://localhost/myapp")
    await fairchild.connect()
    
    pool = WorkerPool(
        fairchild,
        queues=["default", "high"],
        concurrency=5,
    )
    
    await pool.start()

asyncio.run(main())
```

## Web UI

Fairchild includes a web dashboard for monitoring jobs and workflows.

```bash
fairchild ui --import myapp.tasks --port 8080
```

Then open http://localhost:8080

The UI provides:

- **Dashboard**: Job stats, queues, recent jobs, jobs-per-minute chart
- **Workflow view**: DAG visualization, job states, timing
- **Job details**: Arguments, results, errors, timeline

### Theming

The UI supports light and dark modes. It respects your system preference and includes a manual toggle.

## HTTP API

The web UI also exposes a JSON API.

### Enqueue a Job

```bash
POST /api/jobs
Content-Type: application/json

{
    "task": "myapp.tasks.send_email",
    "args": {
        "to": "user@example.com",
        "subject": "Hello"
    },
    "priority": 1,
    "scheduled_at": "2024-01-15T10:00:00Z"
}
```

Response:
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "task": "myapp.tasks.send_email",
    "queue": "default",
    "state": "available",
    "scheduled_at": "2024-01-15T10:00:00+00:00"
}
```

### Other Endpoints

- `GET /api/stats` - Job counts by state
- `GET /api/jobs` - List jobs (supports `?state=` and `?queue=` filters)
- `GET /api/jobs/{id}` - Job details
- `GET /api/queues` - Queue statistics
- `GET /api/workflows` - List workflows
- `GET /api/workflows/{id}` - Workflow details with all jobs

## CLI Reference

### `fairchild install`

Create the `fairchild_jobs` table:

```bash
fairchild install
```

### `fairchild migrate`

Run pending migrations:

```bash
fairchild migrate
```

### `fairchild worker`

Start a worker process:

```bash
fairchild worker [OPTIONS]

Options:
  --import TEXT        Python module(s) to import (registers tasks)
  --queues TEXT        Comma-separated queue names (default: all)
  --concurrency INT    Number of concurrent jobs (default: 10)
```

### `fairchild ui`

Start the web UI:

```bash
fairchild ui [OPTIONS]

Options:
  --import TEXT   Python module(s) to import (registers tasks)
  --host TEXT     Host to bind (default: localhost)
  --port INT      Port to bind (default: 8080)
```

### `fairchild enqueue`

Enqueue a job from the command line:

```bash
fairchild enqueue myapp.tasks.my_task --args '{"key": "value"}'
```

### `fairchild run`

Run a task locally for testing (does not enqueue):

```bash
fairchild run [OPTIONS] TASK_NAME

Options:
  -i, --import TEXT   Python module(s) to import (registers tasks)
  -a, --arg TEXT      Task argument as key=value
```

Examples:
```bash
# Simple invocation
fairchild run -i myapp.tasks myapp.tasks.hello -a name=World

# Multiple arguments
fairchild run -i myapp.tasks myapp.tasks.add -a a=2 -a b=3
```

This runs the task function directly in the current process without involving the database or workers. Useful for testing and debugging—full tracebacks are printed on errors.

## Testing

### Running Tests Locally

1. Create a test database:

```bash
createdb fairchild_test
```

2. Run the tests with your development database URL - the tests will automatically use `_test` instead of `_development`:

```bash
FAIRCHILD_DATABASE_URL=postgres://postgres@localhost/fairchild_development uv run pytest
```

Or run specific test files:

```bash
# Unit tests only (no database required)
uv run pytest tests/test_task.py tests/test_job.py tests/test_record.py

# Integration tests (requires database)
FAIRCHILD_DATABASE_URL=postgres://postgres@localhost/fairchild_development uv run pytest tests/test_integration.py

# Web UI tests (requires database)
FAIRCHILD_DATABASE_URL=postgres://postgres@localhost/fairchild_development uv run pytest tests/test_web_ui.py
```

**Note:** Integration tests automatically convert `_development` to `_test` in the database URL to protect your development data.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FAIRCHILD_DATABASE_URL` | PostgreSQL connection URL | (required) |

### Database URL Format

```
postgresql://user:password@host:port/database
```

Examples:
```bash
# Local development
export FAIRCHILD_DATABASE_URL="postgresql://localhost/myapp_development"

# With credentials
export FAIRCHILD_DATABASE_URL="postgresql://myuser:mypass@localhost/myapp"

# Remote server
export FAIRCHILD_DATABASE_URL="postgresql://user:pass@db.example.com:5432/myapp"
```
