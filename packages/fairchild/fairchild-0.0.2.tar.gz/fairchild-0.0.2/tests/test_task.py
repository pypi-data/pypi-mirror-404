"""Tests for task registration and task decorator."""
from fairchild import task, Record


def test_task_decorator():
    """Test that the @task decorator creates a Task object."""
    
    @task(queue="test", priority=1)
    def simple_task(x: int) -> Record:
        return Record({"result": x * 2})
    
    # Check that task has expected attributes
    assert simple_task.queue == "test"
    assert simple_task.priority == 1
    assert simple_task.max_attempts == 3  # default
    # Task name includes full module path
    assert "simple_task" in simple_task.name
    assert simple_task.name.endswith(".simple_task")
    

def test_task_with_custom_settings():
    """Test task with all custom settings."""
    
    @task(
        queue="custom",
        priority=9,
        max_attempts=5,
        tags=["test", "custom"]
    )
    def custom_task() -> None:
        pass
    
    assert custom_task.queue == "custom"
    assert custom_task.priority == 9
    assert custom_task.max_attempts == 5
    assert custom_task.tags == ["test", "custom"]


def test_task_execution_without_worker():
    """Test that tasks can be called directly when not in a worker context."""
    
    @task()
    def add_numbers(a: int, b: int) -> Record:
        return Record({"sum": a + b})
    
    # When called directly (not in a worker), should execute the function
    result = add_numbers(5, 3)
    
    # Record should be unwrapped in direct calls
    assert result == {"sum": 8}


def test_task_name_derivation():
    """Test that task names are derived from module and function."""
    
    @task()
    def my_function():
        pass
    
    # Should include module and function name
    assert "my_function" in my_function.name
    assert my_function.name.endswith(".my_function")
