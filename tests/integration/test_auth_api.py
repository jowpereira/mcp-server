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
    response = client.post("/tools/login", json={"username": "testuser1", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_success_plain_password_legacy(client: TestClient):
    # 'plainuser' has a plain text password 'plainpassword'
    response = client.post("/tools/login", json={"username": "plainuser", "password": "plainpassword"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure_wrong_password(client: TestClient):
    response = client.post("/tools/login", json={"username": "testuser1", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos"}

def test_login_failure_user_not_found(client: TestClient):
    response = client.post("/tools/login", json={"username": "nonexistentuser", "password": "password"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos"}

def test_login_failure_missing_username(client: TestClient):
    response = client.post("/tools/login", json={"password": "password123"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Usuário e senha obrigatórios."}

def test_login_failure_missing_password(client: TestClient):
    response = client.post("/tools/login", json={"username": "testuser1"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Usuário e senha obrigatórios."}

def test_login_failure_empty_data(client: TestClient):
    response = client.post("/tools/login", json={})
    assert response.status_code == 400
    assert response.json() == {"detail": "Usuário e senha obrigatórios."}

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
    assert response.status_code == 403
    assert response.json().get("detail") == "Not authenticated" # Changed from "Não autenticado"

def test_refresh_token_invalid_token_format(client: TestClient):
    headers = {"Authorization": "NotBearer token"}
    response = client.post("/tools/refresh-token", headers=headers)
    assert response.status_code == 403
    assert response.json().get("detail") == "Invalid authentication credentials" # Changed to specific message

def test_refresh_token_malformed_jwt(client: TestClient):
    headers = {"Authorization": "Bearer invalidjwtstring"}
    response = client.post("/tools/refresh-token", headers=headers)
    assert response.status_code == 401
    assert response.json().get("detail") == "Token inválido"
