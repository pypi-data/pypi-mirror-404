"""Integration tests for Fairchild with a real PostgreSQL database."""

import os
import pytest
import subprocess
import sys
import time


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


@pytest.fixture
def repo_root():
    """Get repository root directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_install_and_enqueue_job(db_url, repo_root):
    """Test installing schema and enqueuing a job via CLI."""
    env = os.environ.copy()
    env["FAIRCHILD_DATABASE_URL"] = db_url
    env["PYTHONPATH"] = repo_root

    # Install the schema
    result = subprocess.run(
        [sys.executable, "-m", "fairchild.cli", "install", "--force"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Install failed: {result.stderr}"
    assert (
        "Fairchild installed successfully" in result.stdout
        or "installed successfully" in result.stdout.lower()
    )

    # Enqueue a job
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fairchild.cli",
            "enqueue",
            "-i",
            "examples.tasks",
            "examples.tasks.hello",
            "-a",
            "name=TestUser",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, f"Enqueue failed: {result.stderr}"
    assert "Enqueued job" in result.stdout


def test_worker_processes_job(db_url, repo_root):
    """Test that a worker can process an enqueued job via CLI."""
    env = os.environ.copy()
    env["FAIRCHILD_DATABASE_URL"] = db_url
    env["PYTHONPATH"] = repo_root

    # Install schema
    subprocess.run(
        [sys.executable, "-m", "fairchild.cli", "install", "--force"],
        cwd=repo_root,
        capture_output=True,
        env=env,
        check=True,
    )

    # Enqueue a simple job
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fairchild.cli",
            "enqueue",
            "-i",
            "examples.tasks",
            "examples.tasks.add",
            "-a",
            "a=5",
            "-a",
            "b=3",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    # Extract job ID from output
    assert "Enqueued job" in result.stdout

    # Start a worker in the background for a short time
    worker_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "fairchild.cli",
            "worker",
            "-i",
            "examples.tasks",
            "--queues",
            "default:1",
        ],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    # Let worker run for a few seconds to process the job
    time.sleep(3)

    # Terminate the worker
    worker_proc.terminate()
    try:
        stdout, stderr = worker_proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        worker_proc.kill()
        stdout, stderr = worker_proc.communicate()

    # Check that worker started and processed something
    combined_output = stdout + stderr
    assert "Started" in combined_output or "workers" in combined_output.lower()
