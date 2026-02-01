from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Record:
    """Wrapper to indicate a task's return value should be persisted.

    Usage:
        @task(queue="default")
        def my_task(item_id: int):
            result = process(item_id)
            return Record({"item_id": item_id, "result": result})

    The recorded value will be stored in the job's `recorded` column
    and can be retrieved by downstream jobs in a workflow.
    """

    value: Any

    def __repr__(self) -> str:
        return f"Record({self.value!r})"
