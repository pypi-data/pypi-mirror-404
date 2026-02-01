"""Execution context for tracking the currently running job.

This module provides a way to track which job is currently being executed
by a worker. When a task calls another task, we check this context to
determine whether to spawn a child job (if inside a worker) or execute
directly (if called from outside).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fairchild.job import Job
    from fairchild.fairchild import Fairchild

# The currently executing job (set by worker during task execution)
_current_job: "Job | None" = None
_current_fairchild: "Fairchild | None" = None
_pending_children: list["Job"] = []


def set_current_job(job: "Job | None", fairchild: "Fairchild | None" = None) -> None:
    """Set the currently executing job. Called by worker."""
    global _current_job, _current_fairchild, _pending_children
    _current_job = job
    _current_fairchild = fairchild
    _pending_children = []  # Reset pending children for new job


def get_current_job() -> "Job | None":
    """Get the currently executing job, or None if not in a worker."""
    return _current_job


def get_current_fairchild() -> "Fairchild | None":
    """Get the Fairchild instance for the current context."""
    return _current_fairchild


def is_inside_task() -> bool:
    """Check if code is currently running inside a task (in a worker)."""
    return _current_job is not None


def add_pending_child(job: "Job") -> None:
    """Add a child job to be inserted after the current task completes."""
    _pending_children.append(job)


def get_pending_children() -> list["Job"]:
    """Get all pending child jobs and clear the list."""
    global _pending_children
    children = _pending_children
    _pending_children = []
    return children
