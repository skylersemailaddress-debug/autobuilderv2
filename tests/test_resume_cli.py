import json
import subprocess
import sys
from pathlib import Path
import tempfile
import os


def test_resume_cli_execution():
    """Test resuming a run that was interrupted during execution."""
    project_root = Path(__file__).resolve().parents[1]
    run_script = project_root / "cli" / "run.py"
    resume_script = project_root / "cli" / "resume.py"
    run_dir = project_root / "runs"
    run_dir.mkdir(exist_ok=True)
    
    # Create a run that will be interrupted (simulate by modifying saved record)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    # Run a normal execution
    result = subprocess.run(
        [sys.executable, str(run_script)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_root),
    )
    
    assert result.returncode == 0
    run_id_line = [line for line in result.stdout.splitlines() if line.startswith("run_id=")][0]
    run_id = run_id_line.split("=", 1)[1].strip()
    
    # Load and modify the record to simulate interruption during execution
    run_file = run_dir / f"{run_id}.json"
    record = json.loads(run_file.read_text())
    
    # Simulate incomplete execution by marking a task as pending
    record["tasks"][0]["status"] = "pending"
    record["tasks"][0]["result"] = None
    record["status"] = "execute"  # Simulate being in execute state
    
    # Save the modified record
    run_file.write_text(json.dumps(record, indent=2))
    
    # Now resume the run
    resume_result = subprocess.run(
        [sys.executable, str(resume_script), run_id],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_root),
    )
    
    assert resume_result.returncode == 0
    assert f"Resuming run {run_id} from stage: execute" in resume_result.stdout
    
    # Verify the resumed run completed
    updated_record = json.loads(run_file.read_text())
    assert updated_record["resumed"] is True
    assert updated_record["status"] == "complete"
    assert all(task["status"] == "complete" for task in updated_record["tasks"])
    
    run_file.unlink()


def test_resume_cli_completed_run():
    """Test that resuming a completed run does nothing."""
    project_root = Path(__file__).resolve().parents[1]
    run_script = project_root / "cli" / "run.py"
    resume_script = project_root / "cli" / "resume.py"
    run_dir = project_root / "runs"
    run_dir.mkdir(exist_ok=True)
    
    # Run a normal execution
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    result = subprocess.run(
        [sys.executable, str(run_script)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_root),
    )
    
    assert result.returncode == 0
    run_id_line = [line for line in result.stdout.splitlines() if line.startswith("run_id=")][0]
    run_id = run_id_line.split("=", 1)[1].strip()
    
    # Try to resume the completed run
    resume_result = subprocess.run(
        [sys.executable, str(resume_script), run_id],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_root),
    )
    
    assert resume_result.returncode == 0
    assert f"Run {run_id} is already complete or failed, cannot resume" in resume_result.stdout
    
    # Clean up
    run_file = run_dir / f"{run_id}.json"
    run_file.unlink()
