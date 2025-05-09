import pytest
import json
import uuid
from fastapi.testclient import TestClient
from app.main import app # Assuming your FastAPI app instance is here
from app.config import settings

# Fixtures como client, auth_token_for_user, manage_test_data_files são de conftest.py

def load_requests_data():
    with open(settings.REQUESTS_FILE, "r") as f:
        return json.load(f)

def save_requests_data(data):
    with open(settings.REQUESTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_rbac_data():
    with open(settings.RBAC_FILE, "r") as f:
        return json.load(f)

def save_rbac_data(data):
    with open(settings.RBAC_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Testes para API de Solicitações de Acesso a Grupos ---

# TODO: Implementar testes para:
# 1. POST /grupos/{group_name}/solicitar_acesso
# 2. GET /grupos/solicitacoes/pendentes
# 3. POST /grupos/solicitacoes/{request_id}/aprovar
# 4. POST /grupos/solicitacoes/{request_id}/rejeitar
# 5. GET /grupos/solicitacoes/minhas
