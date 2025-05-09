# mcp-server/tests/integration/test_auth_api.py
from fastapi.testclient import TestClient
import pytest

# Test the health endpoint first
def test_health_check(client: TestClient):
    response = client.get("/tools/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Tests for /tools/login
def test_login_success_hashed_password(client: TestClient):
    # 'testuser1' has a hashed password 'password123' in test_rbac_master.json
    response = client.post("/tools/login", data={"username": "testuser1", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_success_plain_password_legacy(client: TestClient):
    # 'plainuser' has a plain text password 'plainpassword'
    response = client.post("/tools/login", data={"username": "plainuser", "password": "plainpassword"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure_wrong_password(client: TestClient):
    response = client.post("/tools/login", data={"username": "testuser1", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos"}

def test_login_failure_user_not_found(client: TestClient):
    response = client.post("/tools/login", data={"username": "nonexistentuser", "password": "password"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos"}

def test_login_failure_missing_username(client: TestClient):
    response = client.post("/tools/login", data={"password": "password123"})
    assert response.status_code == 422 # FastAPI validation error for missing form field 'username'

def test_login_failure_missing_password(client: TestClient):
    response = client.post("/tools/login", data={"username": "testuser1"})
    assert response.status_code == 422 # FastAPI validation error for missing form field 'password'

def test_login_failure_empty_data(client: TestClient):
    response = client.post("/tools/login", data={})
    assert response.status_code == 422

# Tests for /tools/refresh-token
def test_refresh_token_success(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("testuser1", "password123")
    assert token is not None, "Failed to get initial token for test_refresh_token_success"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/tools/refresh-token", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"] != token # New token should be different

def test_refresh_token_no_token_provided(client: TestClient):
    response = client.post("/tools/refresh-token")
    assert response.status_code == 401 # FastAPI's dependency injection for security
    assert response.json().get("detail") == "Não autenticado" # Actual message might vary

def test_refresh_token_invalid_token_format(client: TestClient):
    headers = {"Authorization": "NotBearer token"}
    response = client.post("/tools/refresh-token", headers=headers)
    assert response.status_code == 401 # FastAPI's dependency injection for security
    # The detail message can vary based on how FastAPI processes the malformed header.
    # Common messages include "Não autenticado" or "Not authenticated" or "Invalid token format".
    # Let's check for a common one, but this might need adjustment based on actual behavior.
    assert response.json().get("detail") in ["Não autenticado", "Not authenticated", "Token inválido ou expirado"]


def test_refresh_token_malformed_jwt(client: TestClient):
    headers = {"Authorization": "Bearer invalidjwtstring"}
    response = client.post("/tools/refresh-token", headers=headers)
    assert response.status_code == 401
    assert response.json().get("detail") == "Token inválido ou expirado"
