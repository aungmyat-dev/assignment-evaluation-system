import os
os.environ["DATABASE_URL"] = "sqlite:///./test_assignment_evaluation.db"
os.environ["JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_create_assignment():
    teacher_email = "teacher-smoke@example.com"
    response = client.post("/api/auth/register", json={"full_name": "Smoke Teacher", "email": teacher_email, "password": "password123", "role": "teacher"})
    if response.status_code == 409:
        response = client.post("/api/auth/login", json={"email": teacher_email, "password": "password123"})
    assert response.status_code in (200, 201)
    token = response.json()["access_token"]
    created = client.post("/api/assignments", headers={"Authorization": f"Bearer {token}"}, json={"title": "Smoke assignment", "description": "Test", "keywords": ["evidence"], "reference_answer": "Evidence matters.", "min_words": 1, "max_words": 100})
    assert created.status_code == 201
    assert created.json()["title"] == "Smoke assignment"
