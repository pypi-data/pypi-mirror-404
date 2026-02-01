import os
import shlex

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from onako.tmux_orchestrator import TmuxOrchestrator

app = FastAPI()
orch = TmuxOrchestrator()
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class CreateTaskRequest(BaseModel):
    prompt: str
    working_dir: str | None = None


class SendMessageRequest(BaseModel):
    message: str


@app.get("/")
def dashboard():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tasks")
def create_task(req: CreateTaskRequest):
    command = f"claude {shlex.quote(req.prompt)}"
    task = orch.create_task(command, working_dir=req.working_dir, prompt=req.prompt)
    return task


@app.get("/tasks")
def list_tasks():
    return orch.list_tasks()


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    if task_id not in orch.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    task = orch.tasks[task_id].copy()
    task["output"] = orch.get_output(task_id)
    return task


@app.get("/tasks/{task_id}/raw")
def get_task_raw(task_id: str):
    if task_id not in orch.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    task = orch.tasks[task_id].copy()
    task["output"] = orch.get_raw_output(task_id)
    return task


@app.post("/tasks/{task_id}/message")
def send_message(task_id: str, req: SendMessageRequest):
    if task_id not in orch.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    orch.send_message(task_id, req.message)
    return {"status": "sent"}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    if task_id not in orch.tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    orch.kill_task(task_id)
    return {"status": "deleted"}


app.mount("/static", StaticFiles(directory=static_dir), name="static")
