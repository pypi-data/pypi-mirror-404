import subprocess
import time
from pathlib import Path
import pytest
from onako.tmux_orchestrator import TmuxOrchestrator

SESSION_NAME = "onako-test"


@pytest.fixture(autouse=True)
def cleanup(tmp_path):
    """Kill test tmux session before and after each test."""
    subprocess.run(["tmux", "kill-session", "-t", SESSION_NAME], capture_output=True)
    yield
    subprocess.run(["tmux", "kill-session", "-t", SESSION_NAME], capture_output=True)


@pytest.fixture
def orch(tmp_path):
    return TmuxOrchestrator(session_name=SESSION_NAME, db_path=tmp_path / "test.db")


def test_create_task_returns_id(orch):
    task = orch.create_task("echo hello")
    assert task["id"].startswith("task-")
    assert task["status"] == "running"
    assert task["prompt"] == "echo hello"


def test_list_tasks_shows_created_task(orch):
    task = orch.create_task("echo hello")
    tasks = orch.list_tasks()
    assert any(t["id"] == task["id"] for t in tasks)


def test_get_output_captures_pane(orch):
    task = orch.create_task("echo hello-from-test")
    time.sleep(1)
    output = orch.get_output(task["id"])
    assert "hello-from-test" in output


def test_get_raw_output(orch):
    task = orch.create_task("echo raw-test")
    time.sleep(1)
    raw = orch.get_raw_output(task["id"])
    assert "raw-test" in raw


def test_send_message(orch):
    task = orch.create_task("cat")  # cat waits for stdin
    time.sleep(0.5)
    orch.send_message(task["id"], "hello-input")
    time.sleep(1)
    output = orch.get_output(task["id"])
    assert "hello-input" in output


def test_kill_task(orch):
    task = orch.create_task("sleep 999")
    orch.kill_task(task["id"])
    tasks = orch.list_tasks()
    assert not any(t["id"] == task["id"] and t["status"] == "running" for t in tasks)


def test_create_multiple_tasks(orch):
    t1 = orch.create_task("echo one")
    t2 = orch.create_task("echo two")
    tasks = orch.list_tasks()
    ids = [t["id"] for t in tasks]
    assert t1["id"] in ids
    assert t2["id"] in ids
    assert t1["id"] != t2["id"]
