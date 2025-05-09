# Global fixtures for tests
import pytest
from fastapi.testclient import TestClient
from app.main import app # Import your FastAPI app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
