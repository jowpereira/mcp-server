# mcp-server/tests/conftest.py
import pytest
import shutil
import os
import json
from fastapi.testclient import TestClient
import dotenv

# Carregar .env.test explicitamente para garantir variáveis corretas nos testes
dotenv.load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.test'), override=True)

# Attempt to import the FastAPI app instance and other necessary components
try:
    from app.main import app  # The FastAPI application instance
    from app.utils.password import hash_password as app_hash_password
    FASTAPI_APP_IMPORTED = True
except ImportError as e:
    print(f"Warning: Could not import FastAPI app or app_hash_password: {e}")
    print("Tests requiring the app instance or real hashing for setup might be affected or use dummies.")
    FASTAPI_APP_IMPORTED = False
    app = None # Placeholder if app import fails
    # Define a dummy hash_password if the real one couldn't be imported
    def app_hash_password(password: str) -> str:
        print(f"Warning: Using DUMMY app_hash_password for '{password}'")
        return f"dummy_hashed:{password}"

# Define the paths to the master test data files and the working copies
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # This will be /tests directory
MASTER_RBAC_FILE = os.path.join(BASE_DIR, "data", "test_rbac_master.json")
MASTER_REQUESTS_FILE = os.path.join(BASE_DIR, "data", "test_requests_master.json")

# These are the paths for the working copies used by the app during tests.
# .env.test should point RBAC_FILE and REQUESTS_FILE to these locations.
WORKING_RBAC_FILE = os.path.join(BASE_DIR, "data", "test_rbac.json")
WORKING_REQUESTS_FILE = os.path.join(BASE_DIR, "data", "test_requests.json")


@pytest.fixture(scope="session", autouse=True)
def create_master_test_data_files_if_not_exist():
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Use the imported app_hash_password (real or dummy)
    hasher = app_hash_password

    if not os.path.exists(MASTER_RBAC_FILE):
        initial_rbac_data = {
            "grupos": {
                "group1": {"descricao": "Test Group 1", "admins": ["admin_group1"], "users": ["testuser1", "admin_group1"], "ferramentas": ["tool_x"]},
                "group_for_request": {"descricao": "Group for access requests", "admins": ["admin_group_for_request"], "users": ["admin_group_for_request"], "ferramentas": []}
            },
            "usuarios": {
                "testuser1": {"senha": hasher("password123"), "grupos": ["group1"], "papel": "user"},
                "admin_group1": {"senha": hasher("password_admin_g1"), "grupos": ["group1"], "papel": "admin"},
                "globaladmin": {"senha": hasher("password_global"), "grupos": [], "papel": "global_admin"},
                "plainuser": {"senha": "plainpassword", "grupos": [], "papel": "user"}, 
                "requesteruser": {"senha": hasher("password_requester"), "grupos": [], "papel": "user"},
                "admin_group_for_request": {"senha": hasher("password_admin_req"), "grupos": ["group_for_request"], "papel": "admin"}
            },
            "ferramentas": {
                "tool_x": {"nome": "Ferramenta X", "url_base": "/tools/ferramenta_x", "descricao": "Ferramenta de Teste X"},
                "tool_y": {"nome": "Ferramenta Y", "url_base": "/tools/ferramenta_y", "descricao": "Ferramenta de Teste Y"}
            }
        }
        with open(MASTER_RBAC_FILE, 'w') as f:
            json.dump(initial_rbac_data, f, indent=2)

    if not os.path.exists(MASTER_REQUESTS_FILE):
        initial_requests_data = {"requests": []}
        with open(MASTER_REQUESTS_FILE, 'w') as f:
            json.dump(initial_requests_data, f, indent=2)


@pytest.fixture(autouse=True)
def manage_test_data_files():
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    fallback_rbac = {"grupos": {}, "usuarios": {}, "ferramentas": {}}
    fallback_requests = {"requests": []}

    if os.path.exists(MASTER_RBAC_FILE):
        shutil.copyfile(MASTER_RBAC_FILE, WORKING_RBAC_FILE)
    else:
        with open(WORKING_RBAC_FILE, 'w') as f:
            json.dump(fallback_rbac, f)

    if os.path.exists(MASTER_REQUESTS_FILE):
        shutil.copyfile(MASTER_REQUESTS_FILE, WORKING_REQUESTS_FILE)
    else:
        with open(WORKING_REQUESTS_FILE, 'w') as f:
            json.dump(fallback_requests, f)
            
    yield


@pytest.fixture(scope="module")
def client():
    if not FASTAPI_APP_IMPORTED or app is None:
        pytest.fail("FastAPI app could not be imported. Check PYTHONPATH and imports in conftest.py.")
    
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_token_for_user(client: TestClient):
    def _get_token(username, password):
        response = client.post("/tools/login", json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    return _get_token
