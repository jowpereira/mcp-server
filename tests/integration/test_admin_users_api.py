import pytest
import json
from fastapi.testclient import TestClient
from app.main import app  # Assuming your FastAPI app instance is here
from app.auth import create_access_token # For direct token creation if needed, though fixture is preferred
from app.utils.rbac_manager import RBACManager
from app.config import settings

# TestClient instance is typically handled by a fixture in conftest.py
# from ..conftest import client, auth_token_for_user, manage_test_data_files

# For these tests, we assume the following users exist in test_rbac_master.json:
# - "admin_global" (role: "global_admin")
# - "user_comum" (role: "user")
# - "admin_grupo_A" (role: "admin", admin_of_groups: ["grupo_A"])

def load_rbac_data():
    with open(settings.RBAC_FILE, "r") as f:
        return json.load(f)

def save_rbac_data(data):
    with open(settings.RBAC_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Testes para POST /tools/usuarios (Criar Usuário) ---

def test_create_user_success_global_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a criação bem-sucedida de um novo usuário por um admin global.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    new_user_data = {
        "username": "novo_usuario_teste",
        "password": "password123",
        "papel": "user",
        "grupos": []
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["username"] == "novo_usuario_teste"
    assert created_user["papel"] == "user"
    assert "hashed_password" not in created_user # Password should not be returned

    # Verifica se o usuário foi adicionado ao rbac.json
    rbac_data = load_rbac_data()
    assert "novo_usuario_teste" in rbac_data["users"]
    assert rbac_data["users"]["novo_usuario_teste"]["papel"] == "user"

def test_create_user_with_initial_groups_success(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a criação bem-sucedida de um novo usuário com grupos iniciais por um admin global.
    Assume que 'grupo_existente' foi criado previamente ou existe no master_rbac.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure 'grupo_existente' exists for the test
    rbac_data = load_rbac_data()
    if "grupo_existente" not in rbac_data["groups"]:
        rbac_data["groups"]["grupo_existente"] = {
            "description": "Grupo para teste de criação de usuário",
            "admins": [],
            "members": [],
            "tools": []
        }
        save_rbac_data(rbac_data)

    new_user_data = {
        "username": "usuario_com_grupo",
        "password": "password123",
        "papel": "user",
        "grupos": ["grupo_existente"]
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["username"] == "usuario_com_grupo"
    assert created_user["papel"] == "user"
    assert created_user["grupos"] == ["grupo_existente"]

    rbac_data_after = load_rbac_data()
    assert "usuario_com_grupo" in rbac_data_after["users"]
    assert rbac_data_after["users"]["usuario_com_grupo"]["papel"] == "user"
    assert "grupo_existente" in rbac_data_after["users"]["usuario_com_grupo"]["grupos"]
    assert "usuario_com_grupo" in rbac_data_after["groups"]["grupo_existente"]["members"]


def test_create_user_username_already_exists(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a tentativa de criar um usuário com um username que já existe.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    existing_user_data = { # Assume 'user_comum' exists from master data
        "username": "user_comum",
        "password": "newpassword",
        "papel": "user",
        "grupos": []
    }
    response = client.post("/tools/usuarios", headers=headers, json=existing_user_data)
    assert response.status_code == 409 # Conflict
    assert response.json()["detail"] == "Username já existe."

def test_create_user_invalid_role(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a tentativa de criar um usuário com um papel inválido.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    new_user_data = {
        "username": "usuario_papel_invalido",
        "password": "password123",
        "papel": "super_mega_admin", # Papel inválido
        "grupos": []
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 400 # Bad Request or 422 Unprocessable Entity
    # The exact error message might depend on Pydantic validation or custom logic
    assert "papel" in response.json()["detail"].lower() or "role" in response.json()["detail"].lower()


def test_create_user_non_global_admin_forbidden(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a tentativa de criar um usuário por um usuário que não é admin global (ex: user comum).
    """
    token = auth_token_for_user("user_comum", client) # user_comum is not a global admin
    headers = {"Authorization": f"Bearer {token}"}
    new_user_data = {
        "username": "outro_usuario_teste",
        "password": "password123",
        "papel": "user",
        "grupos": []
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 403 # Forbidden

def test_create_user_admin_grupo_forbidden(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a tentativa de criar um usuário por um admin de grupo (que não é admin global).
    """
    token = auth_token_for_user("admin_grupo_A", client) # admin_grupo_A is not a global admin
    headers = {"Authorization": f"Bearer {token}"}
    new_user_data = {
        "username": "mais_um_usuario_teste",
        "password": "password123",
        "papel": "user",
        "grupos": []
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 403 # Forbidden

def test_create_user_missing_username(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a tentativa de criar um usuário sem o campo username.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    new_user_data = {
        # "username": "usuario_sem_nome",
        "password": "password123",
        "papel": "user",
        "grupos": []
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 422 # Unprocessable Entity (FastAPI default for Pydantic validation)

def test_create_user_missing_password(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a tentativa de criar um usuário sem o campo password.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    new_user_data = {
        "username": "usuario_sem_senha",
        # "password": "password123",
        "papel": "user",
        "grupos": []
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 422 # Unprocessable Entity

def test_create_user_missing_role(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a tentativa de criar um usuário sem o campo papel.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    new_user_data = {
        "username": "usuario_sem_papel",
        "password": "password123",
        # "papel": "user",
        "grupos": []
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 422 # Unprocessable Entity

def test_create_user_non_existent_group(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a criação de um usuário com um grupo inicial que não existe.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    new_user_data = {
        "username": "usuario_com_grupo_inexistente",
        "password": "password123",
        "papel": "user",
        "grupos": ["grupo_que_nao_existe_12345"]
    }
    response = client.post("/tools/usuarios", headers=headers, json=new_user_data)
    assert response.status_code == 400 # Bad Request
    assert "grupo_que_nao_existe_12345" in response.json()["detail"]
    assert "não encontrado" in response.json()["detail"]

# --- Testes para GET /tools/usuarios (Listar Usuários) ---

def test_list_users_success_global_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a listagem bem-sucedida de usuários por um admin global.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/tools/usuarios", headers=headers)
    assert response.status_code == 200
    users_list = response.json()
    assert isinstance(users_list, list)
    # Verifica se pelo menos os usuários do master data estão presentes
    # (admin_global, user_comum, admin_grupo_A, user_sem_grupo)
    # O número exato pode variar dependendo de outros testes que adicionam usuários
    assert len(users_list) >= 4 
    usernames_in_response = [user["username"] for user in users_list]
    assert "admin_global" in usernames_in_response
    assert "user_comum" in usernames_in_response
    for user in users_list:
        assert "username" in user
        assert "papel" in user
        assert "grupos" in user
        assert "admin_de_grupos" in user
        assert "hashed_password" not in user # Senha não deve ser retornada
        assert "password" not in user # Senha não deve ser retornada

def test_list_users_forbidden_group_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa que um admin de grupo (não global) não pode listar todos os usuários.
    """
    token = auth_token_for_user("admin_grupo_A", client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/tools/usuarios", headers=headers)
    assert response.status_code == 403 # Forbidden

def test_list_users_forbidden_regular_user(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa que um usuário comum não pode listar todos os usuários.
    """
    token = auth_token_for_user("user_comum", client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/tools/usuarios", headers=headers)
    assert response.status_code == 403 # Forbidden

def test_list_users_unauthenticated(client: TestClient, manage_test_data_files):
    """
    Testa que um usuário não autenticado não pode listar usuários.
    """
    response = client.get("/tools/usuarios")
    assert response.status_code == 401 # Unauthorized

# --- Testes para GET /tools/usuarios/{username} (Detalhar Usuário) ---

def test_get_user_details_success_global_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a obtenção bem-sucedida dos detalhes de um usuário por um admin global.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum" # Usuário existente do master data
    response = client.get(f"/tools/usuarios/{target_username}", headers=headers)
    assert response.status_code == 200
    user_details = response.json()
    assert user_details["username"] == target_username
    assert user_details["papel"] == "user"
    assert "hashed_password" not in user_details
    assert "password" not in user_details
    # Verifica se os grupos e admin_de_grupos estão corretos conforme test_rbac_master.json
    rbac_master_data = manage_test_data_files # Carrega os dados mestre
    expected_groups = rbac_master_data["users"][target_username].get("grupos", [])
    expected_admin_groups = rbac_master_data["users"][target_username].get("admin_de_grupos", [])
    assert sorted(user_details["grupos"]) == sorted(expected_groups)
    assert sorted(user_details["admin_de_grupos"]) == sorted(expected_admin_groups)

def test_get_user_details_self_success(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa se um usuário pode obter seus próprios detalhes.
    """
    target_username = "user_comum"
    token = auth_token_for_user(target_username, client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/tools/usuarios/{target_username}", headers=headers)
    assert response.status_code == 200
    user_details = response.json()
    assert user_details["username"] == target_username

def test_get_user_details_forbidden_other_user(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa que um usuário comum não pode obter detalhes de outro usuário.
    """
    token = auth_token_for_user("user_comum", client) # user_comum tentando ver admin_grupo_A
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "admin_grupo_A"
    response = client.get(f"/tools/usuarios/{target_username}", headers=headers)
    assert response.status_code == 403 # Forbidden

def test_get_user_details_forbidden_group_admin_for_unrelated_user(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa que um admin de grupo não pode obter detalhes de um usuário não relacionado ao seu grupo.
    """
    token = auth_token_for_user("admin_grupo_A", client) # admin_grupo_A
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_sem_grupo" # user_sem_grupo não está no grupo_A
    response = client.get(f"/tools/usuarios/{target_username}", headers=headers)
    assert response.status_code == 403 # Forbidden

def test_get_user_details_not_found(client: TestClient, auth_token_for_user, manage_test_data_files):
    """
    Testa a tentativa de obter detalhes de um usuário inexistente.
    """
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "usuario_que_nao_existe_999"
    response = client.get(f"/tools/usuarios/{target_username}", headers=headers)
    assert response.status_code == 404 # Not Found
    assert response.json()["detail"] == "Usuário não encontrado."

def test_get_user_details_unauthenticated(client: TestClient, manage_test_data_files):
    """
    Testa que um usuário não autenticado não pode obter detalhes de um usuário.
    """
    target_username = "user_comum"
    response = client.get(f"/tools/usuarios/{target_username}")
    assert response.status_code == 401 # Unauthorized

# --- Testes para PUT /tools/usuarios/{username} (Atualizar Usuário) ---

def test_update_user_role_success_global_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA atualiza o papel de um usuário (user -> admin de grupo_A)."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum" # Existe no master data com papel "user"

    update_data = {"papel": "admin"} # Tenta mudar para admin sem especificar admin_de_grupos explicitamente
                                    # A lógica do endpoint deve lidar com isso, 
                                    # mas admin_de_grupos é mais gerenciado via /grupos endpoints.
                                    # Para este endpoint, mudar papel para 'admin' sem grupos em admin_de_grupos é válido.

    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["username"] == target_username
    assert updated_user["papel"] == "admin"

    rbac_data = load_rbac_data()
    assert rbac_data["users"][target_username]["papel"] == "admin"
    # Se o papel muda para admin, admin_de_grupos não deve ser automaticamente populado por este endpoint
    # a menos que a lógica do endpoint especificamente faça isso. O UserUpdate não tem admin_de_grupos.
    assert rbac_data["users"][target_username].get("admin_de_grupos", []) == []

def test_update_user_groups_success_global_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA atualiza os grupos de um usuário."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_sem_grupo" # Existe no master data sem grupos

    # Garante que grupo_A e grupo_B existem
    rbac_data_initial = load_rbac_data()
    if "grupo_A" not in rbac_data_initial["groups"]:
        rbac_data_initial["groups"]["grupo_A"] = {"description": "Test Group A", "admins": [], "members": [], "tools": []}
    if "grupo_B" not in rbac_data_initial["groups"]:
        rbac_data_initial["groups"]["grupo_B"] = {"description": "Test Group B", "admins": [], "members": [], "tools": []}
    save_rbac_data(rbac_data_initial)

    update_data = {"grupos": ["grupo_A", "grupo_B"]}
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["username"] == target_username
    assert sorted(updated_user["grupos"]) == sorted(["grupo_A", "grupo_B"])

    rbac_data = load_rbac_data()
    assert sorted(rbac_data["users"][target_username]["grupos"]) == sorted(["grupo_A", "grupo_B"])
    assert target_username in rbac_data["groups"]["grupo_A"]["members"]
    assert target_username in rbac_data["groups"]["grupo_B"]["members"]

    # Testa a remoção de um grupo e adição de outro
    update_data_2 = {"grupos": ["grupo_B", "grupo_C"]}
    if "grupo_C" not in rbac_data["groups"]:
        rbac_data["groups"]["grupo_C"] = {"description": "Test Group C", "admins": [], "members": [], "tools": []}
        save_rbac_data(rbac_data)
    
    response_2 = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data_2)
    assert response_2.status_code == 200
    updated_user_2 = response_2.json()
    assert sorted(updated_user_2["grupos"]) == sorted(["grupo_B", "grupo_C"])

    rbac_data_2 = load_rbac_data()
    assert sorted(rbac_data_2["users"][target_username]["grupos"]) == sorted(["grupo_B", "grupo_C"])
    assert target_username not in rbac_data_2["groups"]["grupo_A"]["members"]
    assert target_username in rbac_data_2["groups"]["grupo_B"]["members"]
    assert target_username in rbac_data_2["groups"]["grupo_C"]["members"]

def test_update_user_role_and_groups_success_global_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA atualiza o papel e os grupos de um usuário."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum" # Papel "user", grupos ["grupo_A"] no master

    rbac_data_initial = load_rbac_data()
    if "grupo_B" not in rbac_data_initial["groups"]:
        rbac_data_initial["groups"]["grupo_B"] = {"description": "Test Group B", "admins": [], "members": [], "tools": []}
        save_rbac_data(rbac_data_initial)

    update_data = {"papel": "admin", "grupos": ["grupo_B"]}
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["papel"] == "admin"
    assert updated_user["grupos"] == ["grupo_B"]

    rbac_data = load_rbac_data()
    assert rbac_data["users"][target_username]["papel"] == "admin"
    assert rbac_data["users"][target_username]["grupos"] == ["grupo_B"]
    assert target_username not in rbac_data["groups"]["grupo_A"]["members"] # Assumindo que user_comum estava em grupo_A
    assert target_username in rbac_data["groups"]["grupo_B"]["members"]

def test_update_user_to_global_admin_success(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA promove um usuário para global_admin."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum"

    update_data = {"papel": "global_admin"}
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["papel"] == "global_admin"

    rbac_data = load_rbac_data()
    assert rbac_data["users"][target_username]["papel"] == "global_admin"

def test_update_user_clear_admin_privileges_on_role_change(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA muda o papel de um admin de grupo para 'user', limpando admin_de_grupos."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "admin_grupo_A" # Master: papel "admin", admin_de_grupos ["grupo_A"]

    update_data = {"papel": "user"}
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["papel"] == "user"
    assert updated_user["admin_de_grupos"] == []

    rbac_data = load_rbac_data()
    assert rbac_data["users"][target_username]["papel"] == "user"
    assert rbac_data["users"][target_username].get("admin_de_grupos", []) == []
    assert target_username not in rbac_data["groups"]["grupo_A"]["admins"]

def test_update_user_remove_all_groups_success(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA remove todos os grupos de um usuário que pertence a grupos."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum" # Pertence a ["grupo_A"] no master data

    update_data = {"grupos": []}
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["grupos"] == []

    rbac_data = load_rbac_data()
    assert rbac_data["users"][target_username]["grupos"] == []
    assert target_username not in rbac_data["groups"]["grupo_A"]["members"]

def test_update_user_not_found(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA tenta atualizar um usuário inexistente."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {"papel": "user"}
    response = client.put("/tools/usuarios/usuario_fantasma123", headers=headers, json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado."

def test_update_user_invalid_role_value(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA tenta definir um valor de papel inválido."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum"
    update_data = {"papel": "role_que_nao_existe"}
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 422 # Erro de validação Pydantic

def test_update_user_non_existent_group(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA tenta adicionar um usuário a um grupo inexistente."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum"
    update_data = {"grupos": ["grupo_A", "grupo_fantasma123"]}
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 400 # Bad Request (validação customizada no endpoint)
    assert "grupo_fantasma123" in response.json()["detail"]
    assert "não encontrado" in response.json()["detail"]

def test_update_user_empty_payload_no_change(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA envia um payload de atualização vazio; nenhum dado deve mudar."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum"

    # Carrega estado inicial para comparação
    rbac_before = load_rbac_data()
    user_before = rbac_before["users"][target_username].copy()

    update_data = {} # Payload vazio
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 200 # Deve ser OK, mas sem modificações
    
    updated_user_response = response.json()
    rbac_after = load_rbac_data()
    user_after = rbac_after["users"][target_username]

    assert user_after["papel"] == user_before["papel"]
    assert sorted(user_after.get("grupos", [])) == sorted(user_before.get("grupos", []))
    assert updated_user_response["papel"] == user_before["papel"]
    assert sorted(updated_user_response.get("grupos", [])) == sorted(user_before.get("grupos", []))


def test_update_user_forbidden_regular_user(client: TestClient, auth_token_for_user, manage_test_data_files):
    """Usuário regular não pode atualizar outros usuários."""
    token = auth_token_for_user("user_comum", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "admin_grupo_A"
    update_data = {"papel": "user"}
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 403

def test_update_user_forbidden_self_regular_user(client: TestClient, auth_token_for_user, manage_test_data_files):
    """Usuário regular não pode atualizar seu próprio papel ou grupos por este endpoint."""
    target_username = "user_comum"
    token = auth_token_for_user(target_username, client)
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {"papel": "admin"} # Tentando se auto-promover
    response = client.put(f"/tools/usuarios/{target_username}", headers=headers, json=update_data)
    assert response.status_code == 403 # Global admin only endpoint

def test_update_user_unauthenticated(client: TestClient, manage_test_data_files):
    """Tentativa não autenticada de atualizar usuário."""
    target_username = "user_comum"
    update_data = {"papel": "user"}
    response = client.put(f"/tools/usuarios/{target_username}", json=update_data)
    assert response.status_code == 401

# --- Testes para DELETE /tools/usuarios/{username} (Remover Usuário) ---

def test_delete_user_success_global_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA remove um usuário com sucesso."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Cria um usuário para deletar para não afetar os usuários base dos testes
    rbac_data = load_rbac_data()
    user_to_delete = "usuario_para_deletar"
    if user_to_delete not in rbac_data["users"]:
        rbac_data["users"][user_to_delete] = {
            "hashed_password": "some_hash", 
            "papel": "user", 
            "grupos": ["grupo_A"],
            "admin_de_grupos": []
        }
        # Adiciona ao grupo_A também
        if "grupo_A" in rbac_data["groups"] and user_to_delete not in rbac_data["groups"]["grupo_A"]["members"]:
             rbac_data["groups"]["grupo_A"]["members"].append(user_to_delete)
        save_rbac_data(rbac_data)

    response = client.delete(f"/tools/usuarios/{user_to_delete}", headers=headers)
    assert response.status_code == 200
    assert response.json()["detail"] == "Usuário removido com sucesso."

    rbac_data_after = load_rbac_data()
    assert user_to_delete not in rbac_data_after["users"]
    # Verifica se foi removido dos membros do grupo
    if "grupo_A" in rbac_data_after["groups"]:
        assert user_to_delete not in rbac_data_after["groups"]["grupo_A"]["members"]

def test_delete_admin_user_removes_from_group_admin_list(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA remove um usuário que é admin de um grupo, verificando se é removido da lista de admins do grupo."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}

    # Cria um usuário admin de grupo para deletar
    rbac_data = load_rbac_data()
    admin_user_to_delete = "admin_temp_para_deletar"
    group_he_admins = "grupo_X_temp"

    if group_he_admins not in rbac_data["groups"]:
        rbac_data["groups"][group_he_admins] = {"description": "Temp group", "admins": [], "members": [], "tools": []}
    
    rbac_data["users"][admin_user_to_delete] = {
        "hashed_password": "some_hash", 
        "papel": "admin", 
        "grupos": [],
        "admin_de_grupos": [group_he_admins]
    }
    rbac_data["groups"][group_he_admins]["admins"].append(admin_user_to_delete)
    save_rbac_data(rbac_data)

    response = client.delete(f"/tools/usuarios/{admin_user_to_delete}", headers=headers)
    assert response.status_code == 200

    rbac_data_after = load_rbac_data()
    assert admin_user_to_delete not in rbac_data_after["users"]
    assert admin_user_to_delete not in rbac_data_after["groups"][group_he_admins]["admins"]

def test_delete_user_not_found(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA tenta remover um usuário inexistente."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.delete("/tools/usuarios/usuario_fantasma_para_deletar", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado."

def test_delete_self_global_admin_forbidden(client: TestClient, auth_token_for_user, manage_test_data_files):
    """GA tenta se auto-remover (deve ser proibido)."""
    token = auth_token_for_user("admin_global", client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.delete("/tools/usuarios/admin_global", headers=headers)
    assert response.status_code == 400 # Ou 403, dependendo da implementação específica
    assert "não pode remover a si mesmo" in response.json()["detail"].lower() or "cannot remove yourself" in response.json()["detail"].lower()

def test_delete_user_forbidden_regular_user(client: TestClient, auth_token_for_user, manage_test_data_files):
    """Usuário regular tenta remover outro usuário."""
    token = auth_token_for_user("user_comum", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_sem_grupo" # Outro usuário existente
    response = client.delete(f"/tools/usuarios/{target_username}", headers=headers)
    assert response.status_code == 403

def test_delete_user_forbidden_group_admin(client: TestClient, auth_token_for_user, manage_test_data_files):
    """Admin de grupo tenta remover outro usuário."""
    token = auth_token_for_user("admin_grupo_A", client)
    headers = {"Authorization": f"Bearer {token}"}
    target_username = "user_comum"
    response = client.delete(f"/tools/usuarios/{target_username}", headers=headers)
    assert response.status_code == 403

def test_delete_user_unauthenticated(client: TestClient, manage_test_data_files):
    """Tentativa não autenticada de remover usuário."""
    target_username = "user_comum"
    response = client.delete(f"/tools/usuarios/{target_username}")
    assert response.status_code == 401

# --- Fim dos Testes para DELETE /tools/usuarios/{username} ---
