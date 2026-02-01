from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
import json


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_json(value: Any) -> Any:
    """Parse JSON string if needed, otherwise return as-is."""
    if isinstance(value, str):
        return json.loads(value)
    return value


class JobState(str, Enum):
    AVAILABLE = "available"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DISCARDED = "discarded"


@dataclass
class Job:
    """Represents a job in the queue."""

    # Task identification
    task_name: str
    queue: str = "default"
    args: dict[str, Any] = field(default_factory=dict)

    # Identity
    id: UUID = field(default_factory=uuid4)

    # Parent-child relationship (for spawned tasks)
    parent_id: UUID | None = None
    deps: list[str] = field(default_factory=list)  # Job IDs this job depends on

    # State
    state: JobState = JobState.AVAILABLE

    # Scheduling & priority
    priority: int = 5  # 0-9, lower = higher priority
    scheduled_at: datetime = field(default_factory=_utcnow)

    # Execution tracking
    attempted_at: datetime | None = None
    completed_at: datetime | None = None
    attempt: int = 0
    max_attempts: int = 3

    # Results & errors
    recorded: Any | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)

    # Metadata
    tags: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    inserted_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self):
        # Ensure state is JobState enum
        if isinstance(self.state, str):
            self.state = JobState(self.state)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Job":
        """Create a Job instance from a database row."""
        return cls(
            id=row["id"],
            task_name=row["task_name"],
            queue=row["queue"],
            args=_parse_json(row["args"]) or {},
            parent_id=row.get("parent_id"),
            deps=row.get("deps") or [],
            state=JobState(row["state"]),
            priority=row["priority"],
            scheduled_at=row["scheduled_at"],
            attempted_at=row["attempted_at"],
            completed_at=row["completed_at"],
            attempt=row["attempt"],
            max_attempts=row["max_attempts"],
            recorded=_parse_json(row["recorded"]),
            errors=_parse_json(row["errors"]) or [],
            tags=row.get("tags") or [],
            meta=_parse_json(row.get("meta")) or {},
            inserted_at=row["inserted_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            "id": self.id,
            "task_name": self.task_name,
            "queue": self.queue,
            "args": self.args,
            "parent_id": self.parent_id,
            "deps": self.deps,
            "state": self.state.value,
            "priority": self.priority,
            "scheduled_at": self.scheduled_at,
            "attempted_at": self.attempted_at,
            "completed_at": self.completed_at,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "recorded": self.recorded,
            "errors": self.errors,
            "tags": self.tags,
            "meta": self.meta,
            "inserted_at": self.inserted_at,
            "updated_at": self.updated_at,
        }
