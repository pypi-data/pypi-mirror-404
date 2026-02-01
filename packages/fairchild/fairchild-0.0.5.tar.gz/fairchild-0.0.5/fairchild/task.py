from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable
from uuid import uuid4
import inspect

# Global task registry
_task_registry: dict[str, "Task"] = {}


def get_task(name: str) -> "Task":
    """Get a registered task by name."""
    if name not in _task_registry:
        raise ValueError(f"Unknown task: {name}")
    return _task_registry[name]


def get_task_schemas() -> list[dict]:
    """Get schemas for all registered tasks.

    Returns a list of task info dicts suitable for storing in the database.
    """
    tasks = []
    for name, task in sorted(_task_registry.items()):
        sig = inspect.signature(task.fn)
        params = []
        for param_name, param in sig.parameters.items():
            if param_name in ("job", "workflow"):
                continue

            param_info = {"name": param_name}

            if param.annotation != inspect.Parameter.empty:
                try:
                    param_info["type"] = param.annotation.__name__
                except AttributeError:
                    param_info["type"] = str(param.annotation)

            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
                param_info["required"] = False
            else:
                param_info["required"] = True

            params.append(param_info)

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

    return tasks


def task(
    queue: str = "default",
    max_attempts: int = 3,
    priority: int = 5,
    unique: bool = False,
    unique_period: timedelta | None = None,
    tags: list[str] | None = None,
) -> Callable[[Callable], "Task"]:
    """Decorator to define a task.

    Usage:
        @task(queue="default")
        def my_task(item_id: int):
            return Record({"result": item_id * 2})

        # Enqueue
        my_task.enqueue(item_id=42)

        # Schedule for later
        my_task.enqueue_in(minutes=30, item_id=42)

    Args:
        queue: Queue name for this task
        max_attempts: Maximum retry attempts
        priority: 0-9, lower = higher priority
        unique: If True, prevent duplicate jobs with same args
        unique_period: Time window for uniqueness check
        tags: Tags for categorizing/filtering jobs
    """

    def decorator(fn: Callable) -> "Task":
        task_obj = Task(
            fn=fn,
            queue=queue,
            max_attempts=max_attempts,
            priority=priority,
            unique=unique,
            unique_period=unique_period,
            tags=tags or [],
        )
        _task_registry[task_obj.name] = task_obj
        return task_obj

    return decorator


class Task:
    """A registered task that can be enqueued."""

    def __init__(
        self,
        fn: Callable,
        queue: str,
        max_attempts: int,
        priority: int,
        unique: bool,
        unique_period: timedelta | None,
        tags: list[str],
    ):
        self.fn = fn
        self.queue = queue
        self.max_attempts = max_attempts
        self.priority = priority
        self.unique = unique
        self.unique_period = unique_period
        self.tags = tags

        # Derive task name from module and function name
        self.name = f"{fn.__module__}.{fn.__qualname__}"

        # Check if function accepts a 'job' parameter
        sig = inspect.signature(fn)
        self._accepts_job = "job" in sig.parameters

        # Preserve function metadata
        wraps(fn)(self)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the task - either spawn as child job or execute directly.

        If called from inside a running task (in a worker), this spawns
        a child job and returns a Future. Otherwise, it executes the
        function directly.
        """
        from fairchild.context import (
            is_inside_task,
            get_current_job,
            add_pending_child,
        )
        from fairchild.future import Future, extract_futures
        from fairchild.job import Job, JobState

        # If we're inside a worker executing a task, spawn a child job
        if is_inside_task():
            parent_job = get_current_job()

            # Convert positional args to kwargs using function signature
            if args:
                sig = inspect.signature(self.fn)
                param_names = [
                    p for p in sig.parameters.keys() if p not in ("job", "workflow")
                ]
                for i, arg in enumerate(args):
                    if i < len(param_names):
                        kwargs[param_names[i]] = arg

            # Extract any futures from the args - these become dependencies
            futures_in_args = extract_futures(kwargs)
            deps = [str(f.job_id) for f in futures_in_args]

            # Determine initial state based on dependencies
            has_deps = len(deps) > 0
            state = JobState.SCHEDULED if has_deps else JobState.AVAILABLE

            # Create the child job
            job_id = uuid4()
            child_job = Job(
                id=job_id,
                task_name=self.name,
                queue=self.queue,
                args=self._serialize_args(kwargs),
                priority=self.priority,
                max_attempts=self.max_attempts,
                tags=self.tags,
                parent_id=parent_job.id,
                deps=deps,
                state=state,
            )

            # Queue the child job to be inserted after task completes
            add_pending_child(child_job)

            # Return a future representing this job's result
            return Future(job_id=job_id)

        # Not inside a task - execute directly
        from fairchild.record import Record

        result = self.fn(*args, **kwargs)
        # Unwrap Record so local runs behave like resolved futures
        if isinstance(result, Record):
            return result.value
        return result

    def _serialize_args(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Serialize arguments, converting Futures to their job IDs."""
        from fairchild.future import Future

        def _convert(obj: Any) -> Any:
            if isinstance(obj, Future):
                # Store as a reference that can be resolved later
                return {"__future__": str(obj.job_id)}
            elif isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_convert(item) for item in obj]
            elif isinstance(obj, tuple):
                return [_convert(item) for item in obj]
            return obj

        return _convert(kwargs)

    def _get_fairchild(self) -> Any:
        """Get the Fairchild instance."""
        from fairchild.fairchild import get_fairchild

        return get_fairchild()

    def enqueue(self, **kwargs: Any) -> Any:
        """Enqueue this task for immediate execution.

        Returns the created Job.
        """
        return self._get_fairchild().enqueue(
            task=self,
            args=kwargs,
        )

    def enqueue_at(self, at: datetime, **kwargs: Any) -> Any:
        """Enqueue this task to run at a specific time.

        Returns the created Job.
        """
        return self._get_fairchild().enqueue(
            task=self,
            args=kwargs,
            scheduled_at=at,
        )

    def enqueue_in(
        self,
        *,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        **kwargs: Any,
    ) -> Any:
        """Enqueue this task to run after a delay.

        Returns the created Job.
        """
        delay = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        scheduled_at = datetime.utcnow() + delay
        return self.enqueue_at(at=scheduled_at, **kwargs)

    def __repr__(self) -> str:
        return f"Task({self.name!r}, queue={self.queue!r})"
