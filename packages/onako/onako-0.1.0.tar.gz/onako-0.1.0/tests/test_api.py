import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    import importlib
    from onako import server
    importlib.reload(server)
    client = TestClient(server.app)
    yield client
    response = client.get("/tasks")
    for task in response.json():
        client.delete(f"/tasks/{task['id']}")


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_task(client):
    r = client.post("/tasks", json={"prompt": "echo api-test"})
    assert r.status_code == 200
    assert r.json()["id"].startswith("task-")


def test_list_tasks(client):
    client.post("/tasks", json={"prompt": "echo one"})
    client.post("/tasks", json={"prompt": "echo two"})
    r = client.get("/tasks")
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_get_task(client):
    create = client.post("/tasks", json={"prompt": "echo detail-test"})
    task_id = create.json()["id"]
    import time
    time.sleep(1)
    r = client.get(f"/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json()["id"] == task_id
    assert "output" in r.json()


def test_get_task_raw(client):
    create = client.post("/tasks", json={"prompt": "echo raw-api-test"})
    task_id = create.json()["id"]
    import time
    time.sleep(1)
    r = client.get(f"/tasks/{task_id}/raw")
    assert r.status_code == 200
    assert "output" in r.json()


def test_send_message(client):
    create = client.post("/tasks", json={"prompt": "cat"})
    task_id = create.json()["id"]
    r = client.post(f"/tasks/{task_id}/message", json={"message": "hello"})
    assert r.status_code == 200


def test_delete_task(client):
    create = client.post("/tasks", json={"prompt": "sleep 999"})
    task_id = create.json()["id"]
    r = client.delete(f"/tasks/{task_id}")
    assert r.status_code == 200


def test_get_nonexistent_task(client):
    r = client.get("/tasks/task-nonexistent")
    assert r.status_code == 404
