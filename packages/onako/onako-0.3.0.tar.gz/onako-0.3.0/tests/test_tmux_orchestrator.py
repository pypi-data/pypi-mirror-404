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


def test_created_task_has_managed_origin(orch):
    task = orch.create_task("echo hello")
    assert task["origin"] == "managed"


def test_rediscover_external_window(orch):
    """Windows not created by onako are discovered with origin=external."""
    subprocess.run([
        "tmux", "new-window", "-t", SESSION_NAME, "-n", "my-feature",
    ], check=True)
    time.sleep(0.5)
    orch.rediscover_tasks()
    tasks = orch.list_tasks()
    external = [t for t in tasks if t["id"] == "my-feature"]
    assert len(external) == 1
    assert external[0]["origin"] == "external"


def test_external_window_output(orch):
    """Can read output from externally created windows."""
    subprocess.run([
        "tmux", "new-window", "-t", SESSION_NAME, "-n", "ext-test",
    ], check=True)
    subprocess.run([
        "tmux", "send-keys", "-t", f"{SESSION_NAME}:ext-test",
        "echo external-output", "Enter",
    ], check=True)
    time.sleep(1)
    orch.rediscover_tasks()
    output = orch.get_output("ext-test")
    assert "external-output" in output


def test_external_window_send_message(orch):
    """Can send messages to externally created windows."""
    subprocess.run([
        "tmux", "new-window", "-t", SESSION_NAME, "-n", "ext-msg",
    ], check=True)
    subprocess.run([
        "tmux", "send-keys", "-t", f"{SESSION_NAME}:ext-msg",
        "cat", "Enter",
    ], check=True)
    time.sleep(0.5)
    orch.rediscover_tasks()
    orch.send_message("ext-msg", "hello-external")
    time.sleep(1)
    output = orch.get_output("ext-msg")
    assert "hello-external" in output


def test_external_window_kill(orch):
    """Can kill externally created windows."""
    subprocess.run([
        "tmux", "new-window", "-t", SESSION_NAME, "-n", "ext-kill",
    ], check=True)
    time.sleep(0.5)
    orch.rediscover_tasks()
    orch.kill_task("ext-kill")
    tasks = orch.list_tasks()
    assert not any(t["id"] == "ext-kill" and t["status"] == "running" for t in tasks)
