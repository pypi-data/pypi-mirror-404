"""Integration tests for the fairchild CLI."""
import subprocess
import sys
import os


def test_fairchild_run_command():
    """Test the 'fairchild run' command with orchestrator_n example."""
    # Set PYTHONPATH to include current directory
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    # Get the repository root (assuming tests/ is in repo root)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the command
    result = subprocess.run(
        [
            sys.executable, '-m', 'fairchild.cli',
            'run',
            '-i', 'examples.tasks',
            'examples.tasks.orchestrator_n',
            '-a', 'n_items=2'
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env
    )
    
    # Check it ran successfully
    assert result.returncode == 0, f"Command failed with: {result.stderr}"
    
    # Check expected output
    output = result.stdout
    assert "Invoking examples.tasks.orchestrator_n..." in output
    assert "Orchestrator starting with 2 items" in output
    assert "0 * 2 = 0" in output
    assert "1 * 2 = 2" in output
    assert "Summing [0, 2] = 2" in output
    assert "Result: Record({'spawned': 3})" in output or "Result: Record(value={'spawned': 3})" in output


def test_fairchild_run_hello():
    """Test the 'fairchild run' command with a simple hello task."""
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'fairchild.cli',
            'run',
            '-i', 'examples.tasks',
            'examples.tasks.hello',
            '-a', 'name=World'
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env
    )
    
    assert result.returncode == 0, f"Command failed with: {result.stderr}"
    
    output = result.stdout
    assert "Invoking examples.tasks.hello..." in output
    assert "Hello, World!" in output
    assert "Result:" in output
    assert "greeted" in output


def test_fairchild_run_add():
    """Test the 'fairchild run' command with add task."""
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    result = subprocess.run(
        [
            sys.executable, '-m', 'fairchild.cli',
            'run',
            '-i', 'examples.tasks',
            'examples.tasks.add',
            '-a', 'a=5',
            '-a', 'b=3'
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env
    )
    
    assert result.returncode == 0, f"Command failed with: {result.stderr}"
    
    output = result.stdout
    assert "Invoking examples.tasks.add..." in output
    assert "5 + 3 = 8" in output
    assert "result" in output
