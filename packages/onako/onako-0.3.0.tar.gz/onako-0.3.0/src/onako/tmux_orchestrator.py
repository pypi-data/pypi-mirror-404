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
        self._window_ids: dict[str, str] = {}  # window_name -> @id
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
                ["tmux", "new-session", "-d", "-s", self.session_name, "-n", "onako-main"],
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
                started_at TEXT,
                origin TEXT DEFAULT 'managed'
            )
        """)
        # Migrate existing DBs that lack the origin column
        cursor = conn.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        if "origin" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN origin TEXT DEFAULT 'managed'")
        conn.commit()
        conn.close()

    def _load_tasks(self):
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT id, prompt, status, started_at, origin FROM tasks").fetchall()
        conn.close()
        for row in rows:
            self.tasks[row[0]] = {
                "id": row[0],
                "prompt": row[1],
                "status": row[2],
                "started_at": row[3],
                "origin": row[4] or "managed",
            }

    def _save_task(self, task: dict):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO tasks (id, prompt, status, started_at, origin) VALUES (?, ?, ?, ?, ?)",
            (task["id"], task["prompt"], task["status"], task["started_at"], task.get("origin", "managed")),
        )
        conn.commit()
        conn.close()

    def _run_tmux(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["tmux", *args], capture_output=True, text=True)

    def _task_target(self, task_id: str) -> str:
        """Return a safe tmux target for a task, using window ID when available."""
        window_id = self._window_ids.get(task_id)
        if window_id:
            return window_id
        return f"{self.session_name}:{task_id}"

    def create_task(self, command: str, working_dir: str | None = None, prompt: str | None = None) -> dict:
        self._ensure_session()
        task_id = f"task-{secrets.token_hex(4)}"
        self._run_tmux(
            "new-window", "-t", self.session_name, "-n", task_id,
        )
        # Look up the window ID for safe targeting
        result = self._run_tmux(
            "list-windows", "-t", self.session_name, "-F", "#{window_name}|#{window_id}",
        )
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                name, _, wid = line.partition("|")
                if name == task_id and wid:
                    self._window_ids[task_id] = wid
                    break
        if working_dir:
            self._run_tmux(
                "send-keys", "-t", self._task_target(task_id),
                f"cd {shlex.quote(working_dir)}", "Enter",
            )
        self._run_tmux(
            "send-keys", "-t", self._task_target(task_id),
            command, "Enter",
        )
        task = {
            "id": task_id,
            "prompt": prompt or command,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "origin": "managed",
        }
        self.tasks[task_id] = task
        self._save_task(task)
        return task

    def list_tasks(self) -> list[dict]:
        self.rediscover_tasks()
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
            "capture-pane", "-t", self._task_target(task_id),
            "-p", "-S", "-",
        )
        return result.stdout

    def send_message(self, task_id: str, message: str):
        self._run_tmux(
            "send-keys", "-t", self._task_target(task_id),
            "-l", message,
        )
        self._run_tmux(
            "send-keys", "-t", self._task_target(task_id),
            "Enter",
        )

    def kill_task(self, task_id: str):
        self._run_tmux("kill-window", "-t", self._task_target(task_id))
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "done"
            self._save_task(self.tasks[task_id])

    def _sync_task_status(self):
        result = self._run_tmux(
            "list-windows", "-t", self.session_name, "-F", "#{window_name}|#{window_id}",
        )
        active_windows = set()
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.split("|", 1)
                active_windows.add(parts[0])
                if len(parts) > 1:
                    self._window_ids[parts[0]] = parts[1]
        for task_id, task in self.tasks.items():
            if task["status"] == "running" and task_id not in active_windows:
                task["status"] = "done"
                self._save_task(task)

    def rediscover_tasks(self):
        """Rediscover tasks from existing tmux windows on server restart."""
        result = self._run_tmux(
            "list-windows", "-t", self.session_name, "-F", "#{window_name}|#{window_id}",
        )
        if not result.stdout.strip():
            return
        for line in result.stdout.strip().split("\n"):
            parts = line.split("|", 1)
            window_name = parts[0]
            window_id = parts[1] if len(parts) > 1 else None
            if window_id:
                self._window_ids[window_name] = window_id
            if window_name not in self.tasks:
                is_managed = window_name.startswith("task-")
                task = {
                    "id": window_name,
                    "prompt": "(rediscovered)" if is_managed else window_name,
                    "status": "running",
                    "started_at": None,
                    "origin": "managed" if is_managed else "external",
                }
                self.tasks[window_name] = task
                self._save_task(task)
            elif self.tasks[window_name]["status"] == "done":
                self.tasks[window_name]["status"] = "running"
                self._save_task(self.tasks[window_name])
