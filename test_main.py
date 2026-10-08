from database import Base, engine, get_db
from fastapi.testclient import TestClient
from main import app
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


def override_get_db():
  try:
    db = TestingSessionLocal()
    yield db
  finally:
    db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
  Base.metadata.create_all(bind=test_engine)
  yield
  Base.metadata.drop_all(bind=test_engine)


def test_create_and_track_job():
  payload = {
      "recipients": [{
          "name": "John Doe",
          "email": "john@example.com",
          "course_name": "FastAPI Masterclass",
      }]
  }
  response = client.post("/jobs/", json=payload)
  assert response.status_code == 201
  data = response.json()
  assert data["total_recipients"] == 1
  assert "id" in data

  job_id = data["id"]

  # Check job status endpoint
  status_response = client.get(f"/jobs/{job_id}")
  assert status_response.status_code == 200
  status_data = status_response.json()
  assert status_data["id"] == job_id


def test_invalid_email_validation():
  payload = {
      "recipients": [{
          "name": "Jane Doe",
          "email": "invalid-email-format",
          "course_name": "Python 101",
      }]
  }
  response = client.post("/jobs/", json=payload)
  assert response.status_code == 422  # Unprocessable Entity via Pydantic