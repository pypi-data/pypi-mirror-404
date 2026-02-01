"""Future represents a pending task result."""

from uuid import UUID
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from fairchild.job import Job


class Future:
    """Represents the pending result of a spawned task.

    When a task calls another task from within a worker, it gets back
    a Future instead of the actual result. The Future:

    1. Tracks the child job that was spawned
    2. Can be passed to other tasks to establish dependencies
    3. Resolves to the actual result when the child job completes

    Usage:
        @task
        def parent_task():
            # This returns a Future, not the actual result
            result = child_task(arg1, arg2)

            # Pass the future to another task - creates a dependency
            another_task(result)
    """

    def __init__(self, job_id: UUID, job_key: str | None = None):
        self.job_id = job_id
        self.job_key = job_key
        self._result: Any = None
        self._resolved = False

    def __repr__(self) -> str:
        if self._resolved:
            return f"Future({self.job_key or self.job_id}, resolved={self._result!r})"
        return f"Future({self.job_key or self.job_id}, pending)"

    def resolve(self, result: Any) -> None:
        """Set the resolved value of this future."""
        self._result = result
        self._resolved = True

    @property
    def result(self) -> Any:
        """Get the resolved result. Raises if not yet resolved."""
        if not self._resolved:
            raise RuntimeError(f"Future {self.job_id} has not been resolved yet")
        return self._result

    @property
    def is_resolved(self) -> bool:
        return self._resolved


def is_future(obj: Any) -> bool:
    """Check if an object is a Future."""
    return isinstance(obj, Future)


def extract_futures(args: dict) -> list[Future]:
    """Extract all Future objects from a dict of arguments (including nested)."""
    futures = []

    def _extract(obj: Any) -> None:
        if isinstance(obj, Future):
            futures.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                _extract(v)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                _extract(item)

    _extract(args)
    return futures
