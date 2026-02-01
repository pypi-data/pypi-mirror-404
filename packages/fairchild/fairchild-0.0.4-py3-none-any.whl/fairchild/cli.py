import asyncio
import importlib
import click
import os

from fairchild.fairchild import Fairchild


def import_module(module_path: str) -> None:
    """Import a module by its dotted path."""
    try:
        importlib.import_module(module_path)
    except ImportError as e:
        raise click.ClickException(f"Failed to import '{module_path}': {e}")


def get_database_url() -> str:
    """Get database URL from environment."""
    url = os.environ.get("FAIRCHILD_DATABASE_URL")
    if not url:
        raise click.ClickException(
            "FAIRCHILD_DATABASE_URL environment variable is required"
        )
    return url


@click.group()
def cli():
    """Fairchild - PostgreSQL-backed job queue and workflow engine."""
    pass


@cli.command()
@click.option(
    "--force",
    is_flag=True,
    help="Drop all tables and reinstall from scratch (DESTRUCTIVE)",
)
def install(force):
    """Install Fairchild schema (runs all migrations on a fresh database)."""
    asyncio.run(_install(force))


async def _install(force: bool = False):
    from fairchild.db.migrations import migrate, drop_all

    url = get_database_url()
    fairchild = Fairchild(url)
    await fairchild.connect()

    try:
        # Check if table exists
        row = await fairchild._pool.fetchrow("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'fairchild_jobs'
            )
        """)

        if row["exists"]:
            if not force:
                click.echo(
                    "Fairchild is already installed. Use 'migrate' to update schema, or --force to reinstall."
                )
                return

            click.echo("Dropping all Fairchild tables...")
            await drop_all(fairchild._pool)

        await migrate(fairchild._pool)
        click.echo("Fairchild installed successfully.")
    finally:
        await fairchild.disconnect()


@cli.command()
def migrate():
    """Run database migrations."""
    asyncio.run(_migrate())


async def _migrate():
    from fairchild.db.migrations import migrate

    url = get_database_url()
    fairchild = Fairchild(url)
    await fairchild.connect()

    try:
        await migrate(fairchild._pool)
        click.echo("Migrations complete.")
    finally:
        await fairchild.disconnect()


@cli.command()
@click.option(
    "--queues",
    "-q",
    default="default:1",
    help='Queue configuration, e.g., "default:2,processing:4"',
)
@click.option(
    "--import",
    "-i",
    "imports",
    multiple=True,
    help='Module to import for task registration, e.g., "myapp.tasks"',
)
def worker(queues: str, imports: tuple[str, ...]):
    """Start workers to process jobs.

    Queue format: "queue_name:num_workers,queue_name:num_workers"

    Examples:

        fairchild worker --import myapp.tasks --queues "default:2"

        fairchild worker -i myapp.tasks -i myapp.workflows -q "default:2,processing:4"
    """
    # Import task modules to register them
    for module_path in imports:
        import_module(module_path)
        click.echo(f"Imported {module_path}")

    queue_config = parse_queue_config(queues)
    click.echo(f"Starting workers: {queue_config}")
    asyncio.run(_run_workers(queue_config))


def parse_queue_config(config: str) -> dict[str, int]:
    """Parse queue configuration string into dict."""
    result = {}
    for part in config.split(","):
        part = part.strip()
        if ":" in part:
            queue, count = part.rsplit(":", 1)
            result[queue.strip()] = int(count)
        else:
            result[part] = 1
    return result


async def _run_workers(queue_config: dict[str, int]):
    from fairchild.worker import WorkerPool

    url = get_database_url()
    fairchild = Fairchild(url)
    await fairchild.connect()

    pool = WorkerPool(fairchild, queue_config)

    try:
        await pool.run()
    except KeyboardInterrupt:
        click.echo("\nShutting down workers...")
    finally:
        await pool.shutdown()
        await fairchild.disconnect()


@cli.command()
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=4000, help="Port to bind to")
@click.option(
    "--import",
    "-i",
    "imports",
    multiple=True,
    help='Module to import for task registration, e.g., "myapp.tasks"',
)
def ui(host: str, port: int, imports: tuple[str, ...]):
    """Start the web UI dashboard."""
    # Import task modules
    for module_path in imports:
        import_module(module_path)

    click.echo(f"Starting Fairchild UI at http://{host}:{port}")
    asyncio.run(_run_ui(host, port))


async def _run_ui(host: str, port: int):
    from fairchild.ui import create_app
    from aiohttp import web

    url = get_database_url()
    fairchild = Fairchild(url)
    await fairchild.connect()

    app = create_app(fairchild)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)

    try:
        await site.start()
        # Keep running until interrupted
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()
        await fairchild.disconnect()


@cli.command()
@click.argument("task_name")
@click.option(
    "--import",
    "-i",
    "imports",
    multiple=True,
    help='Module to import for task registration, e.g., "myapp.tasks"',
)
@click.option(
    "--arg",
    "-a",
    "args",
    multiple=True,
    help="Task argument as key=value, e.g., -a name=World -a count=5",
)
@click.option(
    "--in",
    "delay",
    default=None,
    help='Delay before running, e.g., "5m", "1h", "30s"',
)
def enqueue(
    task_name: str, imports: tuple[str, ...], args: tuple[str, ...], delay: str | None
):
    """Enqueue a task for execution.

    Examples:

        fairchild enqueue -i myapp.tasks myapp.tasks.hello -a name=World

        fairchild enqueue -i myapp.tasks myapp.tasks.process --in 5m -a id=123
    """
    # Import task modules to register them
    for module_path in imports:
        import_module(module_path)

    # Parse arguments
    parsed_args = {}
    for arg in args:
        if "=" not in arg:
            raise click.ClickException(f"Invalid argument format: {arg}. Use key=value")
        key, value = arg.split("=", 1)
        # Try to parse as JSON for numbers, bools, etc.
        try:
            import json

            parsed_args[key] = json.loads(value)
        except json.JSONDecodeError:
            parsed_args[key] = value

    # Parse delay
    delay_seconds = 0
    if delay:
        delay_seconds = parse_delay(delay)

    asyncio.run(_enqueue(task_name, parsed_args, delay_seconds))


def parse_delay(delay: str) -> int:
    """Parse delay string like '5m', '1h', '30s' into seconds."""
    import re

    match = re.match(r"^(\d+)([smhd])$", delay.lower())
    if not match:
        raise click.ClickException(
            f"Invalid delay format: {delay}. Use e.g., '5m', '1h', '30s'"
        )

    value = int(match.group(1))
    unit = match.group(2)

    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return value * multipliers[unit]


async def _enqueue(task_name: str, args: dict, delay_seconds: int):
    from datetime import datetime, timedelta, timezone
    from fairchild.task import get_task

    url = get_database_url()
    fairchild = Fairchild(url)
    await fairchild.connect()

    try:
        task = get_task(task_name)

        if delay_seconds > 0:
            job = await fairchild.enqueue(
                task=task,
                args=args,
                scheduled_at=datetime.now(timezone.utc)
                + timedelta(seconds=delay_seconds),
            )
            click.echo(f"Enqueued job {job.id} (scheduled in {delay_seconds}s)")
        else:
            job = await fairchild.enqueue(task=task, args=args)
            click.echo(f"Enqueued job {job.id}")
    finally:
        await fairchild.disconnect()


@cli.command()
@click.argument("task_name")
@click.option(
    "--import",
    "-i",
    "imports",
    multiple=True,
    help='Module to import for task registration, e.g., "myapp.tasks"',
)
@click.option(
    "--arg",
    "-a",
    "args",
    multiple=True,
    help="Task argument as key=value, e.g., -a name=World -a count=5",
)
def run(task_name: str, imports: tuple[str, ...], args: tuple[str, ...]):
    """Run a task locally for testing (does not enqueue).

    Runs the task function directly in the current process and prints the result.
    Useful for testing tasks without involving the database or workers.

    Examples:

        fairchild run -i myapp.tasks myapp.tasks.hello -a name=World

        fairchild run -i myapp.tasks myapp.tasks.add -a a=2 -a b=3
    """
    # Import task modules to register them
    for module_path in imports:
        import_module(module_path)

    # Parse arguments
    parsed_args = {}
    for arg in args:
        if "=" not in arg:
            raise click.ClickException(f"Invalid argument format: {arg}. Use key=value")
        key, value = arg.split("=", 1)
        # Try to parse as JSON for numbers, bools, etc.
        try:
            import json

            parsed_args[key] = json.loads(value)
        except json.JSONDecodeError:
            parsed_args[key] = value

    asyncio.run(_invoke(task_name, parsed_args))


async def _invoke(task_name: str, args: dict):
    import inspect
    import traceback
    from fairchild.task import get_task

    task = get_task(task_name)
    click.echo(f"Invoking {task_name}...")

    try:
        # Call the underlying function directly (bypasses worker context check)
        result = task.fn(**args)

        # Handle async functions
        if inspect.isawaitable(result):
            result = await result

        click.echo(f"Result: {result}")
    except Exception as e:
        click.echo(traceback.format_exc(), err=True)
        raise click.ClickException(f"Task failed: {e}")


def main():
    cli()


if __name__ == "__main__":
    main()
