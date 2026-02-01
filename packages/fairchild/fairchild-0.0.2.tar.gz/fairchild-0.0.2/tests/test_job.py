"""Tests for Job class."""
from datetime import datetime, timezone
from uuid import uuid4

from fairchild.job import Job, JobState


def test_job_creation():
    """Test creating a Job instance."""
    job = Job(
        task_name="test.task",
        queue="default",
        args={"key": "value"},
        priority=5,
        max_attempts=3,
        tags=["test"],
    )
    
    assert job.task_name == "test.task"
    assert job.queue == "default"
    assert job.args == {"key": "value"}
    assert job.priority == 5
    assert job.max_attempts == 3
    assert job.tags == ["test"]
    assert job.state == JobState.AVAILABLE
    assert job.attempt == 0


def test_job_with_id():
    """Test creating a Job with a specific ID."""
    job_id = uuid4()
    job = Job(
        id=job_id,
        task_name="test.task",
        queue="default",
        args={},
    )
    
    assert job.id == job_id


def test_job_state():
    """Test job state enum."""
    assert JobState.AVAILABLE.value == "available"
    assert JobState.SCHEDULED.value == "scheduled"
    assert JobState.RUNNING.value == "running"
    assert JobState.COMPLETED.value == "completed"
    assert JobState.FAILED.value == "failed"
    assert JobState.CANCELLED.value == "cancelled"


def test_job_timestamps():
    """Test that job timestamps are set."""
    job = Job(
        task_name="test.task",
        queue="default",
        args={},
    )
    
    assert job.inserted_at is not None
    assert job.updated_at is not None
    assert isinstance(job.inserted_at, datetime)
    assert isinstance(job.updated_at, datetime)


def test_job_scheduled_at():
    """Test job with scheduled_at."""
    scheduled_time = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
    job = Job(
        task_name="test.task",
        queue="default",
        args={},
        scheduled_at=scheduled_time,
    )
    
    assert job.scheduled_at == scheduled_time
