import re
import secrets
import shlex
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path.home() / ".onako" / "onako.db"


class TmuxOrchestrator:
    def __init__(self, session_name: str = "onako", db_path: Path | None = None):
        self.session_name = session_name
        self.db_path = db_path or DB_PATH
        self.tasks: dict[str, dict] = {}
        self._init_db()
        self._load_tasks()
        self._ensure_session()
        self.rediscover_tasks()

    def _ensure_session(self):
        result = subprocess.run(
            ["tmux", "has-session", "-t", self.session_name],
            capture_output=True,
        )
        if result.returncode != 0:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", self.session_name],
                check=True,
            )

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                prompt TEXT,
                status TEXT,
                started_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _load_tasks(self):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT id, prompt, status, started_at FROM tasks").fetchall()
        conn.close()
        for row in rows:
            self.tasks[row[0]] = {
                "id": row[0],
                "prompt": row[1],
                "status": row[2],
                "started_at": row[3],
            }

    def _save_task(self, task: dict):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO tasks (id, prompt, status, started_at) VALUES (?, ?, ?, ?)",
            (task["id"], task["prompt"], task["status"], task["started_at"]),
        )
        conn.commit()
        conn.close()

    def _run_tmux(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["tmux", *args], capture_output=True, text=True)

    def create_task(self, command: str, working_dir: str | None = None, prompt: str | None = None) -> dict:
        self._ensure_session()
        task_id = f"task-{secrets.token_hex(4)}"
        self._run_tmux(
            "new-window", "-t", self.session_name, "-n", task_id,
        )
        if working_dir:
            self._run_tmux(
                "send-keys", "-t", f"{self.session_name}:{task_id}",
                f"cd {shlex.quote(working_dir)}", "Enter",
            )
        self._run_tmux(
            "send-keys", "-t", f"{self.session_name}:{task_id}",
            command, "Enter",
        )
        task = {
            "id": task_id,
            "prompt": prompt or command,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        self.tasks[task_id] = task
        self._save_task(task)
        return task

    def list_tasks(self) -> list[dict]:
        self._sync_task_status()
        return list(self.tasks.values())

    def get_output(self, task_id: str) -> str:
        raw = self.get_raw_output(task_id)
        cleaned = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", raw)
        return self._strip_claude_chrome(cleaned)

    @staticmethod
    def _strip_claude_chrome(text: str) -> str:
        lines = text.split("\n")
        # Strip from the bottom: Claude Code's TUI draws box-drawing chars,
        # the › prompt, and status lines like "accept edits on..."
        while lines:
            line = lines[-1].strip()
            if (
                not line
                or all(c in "─━╭╮╰╯│┃┌┐└┘├┤┬┴┼╋═║ ›❯▸▶" for c in line)
                or "accept edits" in line
                or "esc to interrupt" in line
                or "shift+tab to cycle" in line
                or "ctrl+" in line.lower()
                or line == "›"
            ):
                lines.pop()
            else:
                break
        return "\n".join(lines)

    def get_raw_output(self, task_id: str) -> str:
        result = self._run_tmux(
            "capture-pane", "-t", f"{self.session_name}:{task_id}",
            "-p", "-S", "-",
        )
        return result.stdout

    def send_message(self, task_id: str, message: str):
        self._run_tmux(
            "send-keys", "-t", f"{self.session_name}:{task_id}",
            "-l", message,
        )
        self._run_tmux(
            "send-keys", "-t", f"{self.session_name}:{task_id}",
            "Enter",
        )

    def kill_task(self, task_id: str):
        self._run_tmux("kill-window", "-t", f"{self.session_name}:{task_id}")
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "done"
            self._save_task(self.tasks[task_id])

    def _sync_task_status(self):
        result = self._run_tmux(
            "list-windows", "-t", self.session_name, "-F", "#{window_name}",
        )
        active_windows = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
        for task_id, task in self.tasks.items():
            if task["status"] == "running" and task_id not in active_windows:
                task["status"] = "done"
                self._save_task(task)

    def rediscover_tasks(self):
        """Rediscover tasks from existing tmux windows on server restart."""
        result = self._run_tmux(
            "list-windows", "-t", self.session_name, "-F", "#{window_name}",
        )
        if not result.stdout.strip():
            return
        for window_name in result.stdout.strip().split("\n"):
            if window_name.startswith("task-") and window_name not in self.tasks:
                task = {
                    "id": window_name,
                    "prompt": "(rediscovered)",
                    "status": "running",
                    "started_at": None,
                }
                self.tasks[window_name] = task
                self._save_task(task)
