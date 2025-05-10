# mcp-server/tests/integration/test_admin_groups_api.py
from fastapi.testclient import TestClient
import pytest
import json
import os

# Helper to load current rbac data for assertions
def load_rbac_data(rbac_file_path):
    with open(rbac_file_path, 'r') as f:
        return json.load(f)

BASE_TEST_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ./tests
WORKING_RBAC_FILE = os.path.join(BASE_TEST_DIR, "data", "test_rbac.json")


# Tests for Group Management by Global Admin
# Requires globaladmin token (password: "password_global")

def test_create_group_success(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    assert token, "Failed to get token for globaladmin"
    headers = {"Authorization": f"Bearer {token}"}
    
    group_data = {"nome": "new_group_1", "descricao": "A brand new group"}
    response = client.post("/tools/grupos", headers=headers, json=group_data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Grupo 'new_group_1' criado com sucesso."}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert "new_group_1" in rbac_data["grupos"]
    assert rbac_data["grupos"]["new_group_1"]["descricao"] == "A brand new group"
    assert rbac_data["grupos"]["new_group_1"]["admins"] == [] # Initially no admins
    assert rbac_data["grupos"]["new_group_1"]["users"] == []
    assert rbac_data["grupos"]["new_group_1"]["ferramentas"] == []

def test_create_group_already_exists(client: TestClient, auth_token_for_user):
    # Obtém token para o globaladmin
    token = auth_token_for_user("globaladmin", "password_global")
    # Garante que o token foi obtido com sucesso
    assert token, "Falha ao obter token para o usuário globaladmin. Verifique se o usuário existe e a senha está correta."
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Tenta criar um grupo com o nome 'group1' que já deve existir no arquivo test_rbac_fixed.json
    group_data = {"nome": "group1", "descricao": "Attempt to recreate"}
    
    # Imprime o conteúdo atual do RBAC para debug
    print("Verificando conteúdo do RBAC antes do teste:")
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    print(f"Grupos existentes: {list(rbac_data.get('grupos', {}).keys())}")
    
    response = client.post("/tools/grupos", headers=headers, json=group_data)
    
    assert response.status_code == 409
    assert response.json() == {"detail": "Grupo já existe."}

def test_create_group_no_name(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    
    group_data = {"descricao": "Group without a name"} # Missing "nome"
    response = client.post("/tools/grupos", headers=headers, json=group_data)
    
    assert response.status_code == 422 # Validation error

def test_create_group_not_global_admin(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("testuser1", "password123") # testuser1 is not global_admin
    assert token, "Failed to get token for testuser1"
    headers = {"Authorization": f"Bearer {token}"}
    
    group_data = {"nome": "group_by_user", "descricao": "Should fail"}
    response = client.post("/tools/grupos", headers=headers, json=group_data)
    
    assert response.status_code == 403
    assert response.json() == {"detail": "Acesso restrito ao admin global."}

def test_list_groups_success_global_admin(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/tools/grupos", headers=headers)
    assert response.status_code == 200
    groups = response.json()
    assert isinstance(groups, list)
    
    # Check for expected groups from master data
    group_names = [g["nome"] for g in groups]
    assert "group1" in group_names
    assert "group_for_request" in group_names
    
    for group in groups:
        if group["nome"] == "group1":
            assert group["descricao"] == "Test Group 1"
            assert "admin_group1" in group["administradores"]
            assert "testuser1" in group["usuarios"]
            assert "admin_group1" in group["usuarios"]
            # Check if tool_x is correctly represented in ferramentas_disponiveis
            tool_x_found = any(t["id"] == "tool_x" and t["nome"] == "Ferramenta X" for t in group["ferramentas_disponiveis"])
            assert tool_x_found, "Tool X not found in group1's available tools"

def test_list_groups_not_global_admin(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("testuser1", "password123")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/tools/grupos", headers=headers)
    assert response.status_code == 403
    assert response.json() == {"detail": "Acesso restrito ao admin global."}

def test_edit_group_success(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    
    edit_data = {"nome": "group1_renamed", "descricao": "Updated description for group1"}
    response = client.put("/tools/grupos/group1", headers=headers, json=edit_data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Grupo 'group1_renamed' editado com sucesso."}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert "group1" not in rbac_data["grupos"] # Old name should be gone
    assert "group1_renamed" in rbac_data["grupos"]
    assert rbac_data["grupos"]["group1_renamed"]["descricao"] == "Updated description for group1"
    # Ensure other properties like admins, users, ferramentas are preserved
    assert rbac_data["grupos"]["group1_renamed"]["admins"] == ["admin_group1"] 
    assert "tool_x" in rbac_data["grupos"]["group1_renamed"]["ferramentas"]

    # Also check if users who were in "group1" are now in "group1_renamed"
    assert "group1_renamed" in rbac_data["usuarios"]["testuser1"]["grupos"]
    assert "group1" not in rbac_data["usuarios"]["testuser1"]["grupos"]
    assert "group1_renamed" in rbac_data["usuarios"]["admin_group1"]["grupos"]
    assert "group1" not in rbac_data["usuarios"]["admin_group1"]["grupos"]


def test_edit_group_only_description(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    
    edit_data = {"descricao": "Only description updated for group_for_request"}
    response = client.put("/tools/grupos/group_for_request", headers=headers, json=edit_data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Grupo 'group_for_request' editado com sucesso."}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert rbac_data["grupos"]["group_for_request"]["descricao"] == "Only description updated for group_for_request"
    assert rbac_data["grupos"]["group_for_request"]["admins"] == ["admin_group_for_request"] # Check if other data is intact

def test_edit_group_rename_to_existing_name(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a temporary group to avoid conflict with master data for other tests
    client.post("/tools/grupos", headers=headers, json={"nome": "temp_group_for_edit_test", "descricao": "temp"})

    edit_data = {"nome": "group1"} # Try to rename "temp_group_for_edit_test" to "group1" which exists
    response = client.put("/tools/grupos/temp_group_for_edit_test", headers=headers, json=edit_data)
    
    assert response.status_code == 409
    assert response.json() == {"detail": "Já existe um grupo com o nome 'group1'."}

    # Cleanup: delete the temporary group
    client.delete("/tools/grupos/temp_group_for_edit_test", headers=headers)


def test_edit_group_not_found(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    
    edit_data = {"nome": "non_existent_group_new_name"}
    response = client.put("/tools/grupos/non_existent_group", headers=headers, json=edit_data)
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Grupo não encontrado."}

def test_edit_group_not_global_admin(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("admin_group1", "password_admin_g1") # admin_group1 is not global_admin
    headers = {"Authorization": f"Bearer {token}"}
    
    edit_data = {"descricao": "Attempt by group admin"}
    response = client.put("/tools/grupos/group1", headers=headers, json=edit_data)
    
    assert response.status_code == 403
    assert response.json() == {"detail": "Acesso restrito ao admin global."}

def test_delete_group_success(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}

    # First, create a group to delete to avoid altering master data needed for other tests
    group_to_delete_name = "group_to_be_deleted_test"
    client.post("/tools/grupos", headers=headers, json={"nome": group_to_delete_name, "descricao": "temp group"})
    
    # Add a user to this group to test if user's group list is updated
    rbac_data_before_delete = load_rbac_data(WORKING_RBAC_FILE)
    rbac_data_before_delete["usuarios"]["testuser1"]["grupos"].append(group_to_delete_name)
    rbac_data_before_delete["grupos"][group_to_delete_name]["users"].append("testuser1")
    with open(WORKING_RBAC_FILE, 'w') as f:
        json.dump(rbac_data_before_delete, f)

    response = client.delete(f"/tools/grupos/{group_to_delete_name}", headers=headers)
    
    assert response.status_code == 200
    assert response.json() == {"message": f"Grupo '{group_to_delete_name}' removido com sucesso."}
    
    rbac_data_after_delete = load_rbac_data(WORKING_RBAC_FILE)
    assert group_to_delete_name not in rbac_data_after_delete["grupos"]
    # Check if user "testuser1" no longer has this group
    assert group_to_delete_name not in rbac_data_after_delete["usuarios"]["testuser1"]["grupos"]


def test_delete_group_not_found(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.delete("/tools/grupos/non_existent_group_for_delete", headers=headers)
    
    assert response.status_code == 404
    assert response.json() == {"detail": "Grupo não encontrado."}

def test_delete_group_not_global_admin(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("admin_group1", "password_admin_g1")
    headers = {"Authorization": f"Bearer {token}"}
    
    # admin_group1 should not be able to delete group1 even if they are admin of it
    response = client.delete("/tools/grupos/group1", headers=headers)
    
    assert response.status_code == 403
    assert response.json() == {"detail": "Acesso restrito ao admin global."}

# TODO: Add more tests for other group management endpoints:
# - POST /grupos/{grupo}/admins
# - DELETE /grupos/{grupo}/admins/{username_param}
# - POST /grupos/{grupo}/usuarios
# - DELETE /grupos/{grupo}/usuarios/{username}
# - POST /grupos/{grupo}/promover-admin
# - GET /grupos/{grupo}/usuarios
# - POST /grupos/{grupo}/ferramentas
# - DELETE /grupos/{grupo}/ferramentas/{tool_id}
# - GET /grupos/disponivel (though this is more user-centric)

# --- Tests for Managing Users and Admins within Groups ---

@pytest.fixture
def setup_group_for_user_management(client: TestClient, auth_token_for_user):
    """Creates a fresh group and a new user for user management tests."""
    ga_token = auth_token_for_user("globaladmin", "password_global")
    headers_ga = {"Authorization": f"Bearer {ga_token}"}
    group_name = "user_manage_group"
    user_to_add_name = "user_for_group_manage"

    # Clean up if exists from previous failed run
    client.delete(f"/tools/grupos/{group_name}", headers=headers_ga)
    client.delete(f"/tools/usuarios/{user_to_add_name}", headers=headers_ga) # Assuming this endpoint exists

    # Create group
    client.post("/tools/grupos", headers=headers_ga, json={"nome": group_name, "descricao": "Test group for user management"})
    # Create user (assuming /tools/usuarios for user creation by global admin exists and works)
    # If not, this user needs to be in test_rbac_master.json or created manually in rbac file for tests
    # For now, let's assume it needs to be pre-existing or created via a different mechanism if /tools/usuarios POST is not ready.
    # We will use 'requesteruser' which is already in master data and not in any group initially.
    user_to_add_name = "requesteruser" 

    return group_name, user_to_add_name, headers_ga

def test_add_user_to_group_global_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_add, headers_ga = setup_group_for_user_management
    
    response = client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_add})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": f"Usuário '{user_to_add}' adicionado ao grupo '{group_name}'"}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert user_to_add in rbac_data["grupos"][group_name]["users"]
    assert group_name in rbac_data["usuarios"][user_to_add]["grupos"]

def test_add_user_to_group_group_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_add, headers_ga = setup_group_for_user_management
    
    # Adiciona 'admin_group1' como membro antes de promover a admin
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": "admin_group1"})
    client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": "admin_group1"})
    group_admin_token = auth_token_for_user("admin_group1", "password_admin_g1")
    headers_group_admin = {"Authorization": f"Bearer {group_admin_token}"}
    response = client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_group_admin, json={"username": user_to_add})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": f"Usuário '{user_to_add}' adicionado ao grupo '{group_name}'"}

def test_add_user_to_group_user_already_in_group(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_add, headers_ga = setup_group_for_user_management
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_add}) # Add first time
    
    response = client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_add}) # Try adding again
    assert response.status_code == 200, response.text
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    user_count_in_group = rbac_data["grupos"][group_name]["users"].count(user_to_add)
    assert user_count_in_group == 1, "User should not be duplicated in group's user list"
    group_count_in_user = rbac_data["usuarios"][user_to_add]["grupos"].count(group_name)
    assert group_count_in_user == 1, "Group should not be duplicated in user's group list"

def test_add_user_to_group_user_not_exist(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, _, headers_ga = setup_group_for_user_management
    response = client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": "non_existent_user_for_add"})
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Usuário inválido."}

def test_add_user_to_group_group_not_exist(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/tools/grupos/non_existent_group_for_user_add/usuarios", headers=headers, json={"username": "testuser1"})
    assert response.status_code == 404, response.text
    assert response.json() == {"detail": "Grupo não encontrado."}

def test_add_user_to_group_no_permission(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_add, _ = setup_group_for_user_management
    regular_user_token = auth_token_for_user("testuser1", "password123") # testuser1 is not admin of group_name or global
    headers_user = {"Authorization": f"Bearer {regular_user_token}"}
    response = client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_user, json={"username": user_to_add})
    assert response.status_code == 403, response.text
    assert response.json() == {"detail": "Acesso restrito ao admin do grupo ou global."}


def test_remove_user_from_group_global_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_manage, headers_ga = setup_group_for_user_management
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_manage}) # Add user first

    response = client.delete(f"/tools/grupos/{group_name}/usuarios/{user_to_manage}", headers=headers_ga)
    assert response.status_code == 200, response.text
    assert response.json() == {"message": f"Usuário '{user_to_manage}' removido do grupo '{group_name}'"}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert user_to_manage not in rbac_data["grupos"][group_name]["users"]
    assert group_name not in rbac_data["usuarios"][user_to_manage]["grupos"]
    # If user was also admin, ensure they are removed from admins list too
    assert user_to_manage not in rbac_data["grupos"][group_name]["admins"]

def test_remove_user_from_group_group_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_manage, headers_ga = setup_group_for_user_management
    
    # Adiciona 'admin_group1' como membro antes de promover a admin
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": "admin_group1"})
    client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": "admin_group1"})
    group_admin_token = auth_token_for_user("admin_group1", "password_admin_g1")
    headers_group_admin = {"Authorization": f"Bearer {group_admin_token}"}
    response = client.delete(f"/tools/grupos/{group_name}/usuarios/{user_to_manage}", headers=headers_group_admin)
    assert response.status_code == 200, response.text

def test_remove_user_from_group_user_not_in_group(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, _, headers_ga = setup_group_for_user_management
    # user 'testuser1' is not in 'group_name' initially by this fixture
    response = client.delete(f"/tools/grupos/{group_name}/usuarios/testuser1", headers=headers_ga)
    assert response.status_code == 404, response.text 
    assert response.json() == {"detail": "Usuário não está no grupo."}

def test_remove_user_from_group_no_permission(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_manage, headers_ga = setup_group_for_user_management
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_manage}) # Add user

    non_admin_token = auth_token_for_user("plainuser", "plainpassword") # plainuser is not admin
    headers_non_admin = {"Authorization": f"Bearer {non_admin_token}"}
    response = client.delete(f"/tools/grupos/{group_name}/usuarios/{user_to_manage}", headers=headers_non_admin)
    assert response.status_code == 403, response.text
    assert response.json() == {"detail": "Acesso restrito ao admin do grupo ou global."}


def test_designate_group_admin_global_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_promote, headers_ga = setup_group_for_user_management
    # Add user to group first, as per API logic (must be member to be admin)
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_promote})

    response = client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": user_to_promote})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": f"Usuário '{user_to_promote}' agora é admin do grupo '{group_name}'"}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert user_to_promote in rbac_data["grupos"][group_name]["admins"]

def test_designate_group_admin_user_not_in_group(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_not_in_group, headers_ga = setup_group_for_user_management
    # user_not_in_group (requesteruser) is NOT added to group_name yet
    response = client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": user_not_in_group})
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": f"Usuário '{user_not_in_group}' não é membro do grupo '{group_name}'. Adicione como membro primeiro."}

def test_remove_group_admin_global_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_make_admin, headers_ga = setup_group_for_user_management
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_make_admin})
    client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": user_to_make_admin})

    response = client.delete(f"/tools/grupos/{group_name}/admins/{user_to_make_admin}", headers=headers_ga)
    assert response.status_code == 200, response.text
    assert response.json() == {"message": f"Usuário '{user_to_make_admin}' não é mais admin do grupo '{group_name}'."}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert user_to_make_admin not in rbac_data["grupos"][group_name]["admins"]

def test_remove_group_admin_by_group_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_demote, headers_ga = setup_group_for_user_management
    acting_admin_username = "admin_group1"

    # Add user_to_demote to the group and make them an admin
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_demote})
    client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": user_to_demote})
    # Make acting_admin_username an admin of this group too
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": acting_admin_username})
    client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": acting_admin_username})

    acting_admin_token = auth_token_for_user(acting_admin_username, "password_admin_g1")
    headers_acting_admin = {"Authorization": f"Bearer {acting_admin_token}"}

    response = client.delete(f"/tools/grupos/{group_name}/admins/{user_to_demote}", headers=headers_acting_admin)
    assert response.status_code == 200, response.text
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert user_to_demote not in rbac_data["grupos"][group_name]["admins"]

def test_remove_last_group_admin_by_group_admin_fail(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, _, headers_ga = setup_group_for_user_management
    last_admin_username = "admin_group1"
    # Add last_admin_username as the only admin
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": last_admin_username})
    client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": last_admin_username})

    last_admin_token = auth_token_for_user(last_admin_username, "password_admin_g1")
    headers_last_admin = {"Authorization": f"Bearer {last_admin_token}"}

    # Try to remove self as last admin
    response = client.delete(f"/tools/grupos/{group_name}/admins/{last_admin_username}", headers=headers_last_admin)
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Não é possível remover o último administrador do grupo."}

def test_remove_last_group_admin_by_global_admin_success(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, _, headers_ga = setup_group_for_user_management
    last_admin_username = "admin_group1"
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": last_admin_username})
    client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": last_admin_username})

    # Global admin can remove the last admin
    response = client.delete(f"/tools/grupos/{group_name}/admins/{last_admin_username}", headers=headers_ga)
    assert response.status_code == 200, response.text
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert last_admin_username not in rbac_data["grupos"][group_name]["admins"]


def test_promote_user_to_group_admin_global_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_promote, headers_ga = setup_group_for_user_management
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_promote}) # Ensure user is in group

    response = client.post(f"/tools/grupos/{group_name}/promover-admin", headers=headers_ga, json={"username": user_to_promote})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": f"Usuário '{user_to_promote}' agora é admin do grupo '{group_name}'"}
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert user_to_promote in rbac_data["grupos"][group_name]["admins"]

def test_promote_user_to_group_admin_group_admin(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_to_promote, headers_ga = setup_group_for_user_management
    acting_admin = "admin_group1"
    # Add user_to_promote to group
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": user_to_promote})
    # Make acting_admin an admin of this group
    client.post(f"/tools/grupos/{group_name}/usuarios", headers=headers_ga, json={"username": acting_admin})
    client.post(f"/tools/grupos/{group_name}/admins", headers=headers_ga, json={"username": acting_admin})

    group_admin_token = auth_token_for_user(acting_admin, "password_admin_g1")
    headers_group_admin = {"Authorization": f"Bearer {group_admin_token}"}

    response = client.post(f"/tools/grupos/{group_name}/promover-admin", headers=headers_group_admin, json={"username": user_to_promote})
    assert response.status_code == 200, response.text
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert user_to_promote in rbac_data["grupos"][group_name]["admins"]

def test_promote_user_to_group_admin_user_not_in_group(client: TestClient, auth_token_for_user, setup_group_for_user_management):
    group_name, user_not_member, headers_ga = setup_group_for_user_management
    # user_not_member (requesteruser) is not in group_name
    response = client.post(f"/tools/grupos/{group_name}/promover-admin", headers=headers_ga, json={"username": user_not_member})
    assert response.status_code == 400, response.text
    assert response.json() == {"detail": f"Usuário '{user_not_member}' não é membro do grupo '{group_name}'. Não pode ser promovido."}


def test_list_users_in_group_global_admin(client: TestClient, auth_token_for_user):
    token = auth_token_for_user("globaladmin", "password_global")
    headers = {"Authorization": f"Bearer {token}"}
    # group1 has admin_group1 (admin, user) and testuser1 (user)
    # Determine current name of group1 due to potential rename in test_edit_group_success_rename_and_description
    rbac_before = load_rbac_data(WORKING_RBAC_FILE)
    original_group1_current_name = "group1_renamed" if "group1_renamed" in rbac_before["grupos"] else "group1"

    response = client.get(f"/tools/grupos/{original_group1_current_name}/usuarios", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "admin_group1" in data["admins"]
    assert "admin_group1" in data["users"]
    assert "testuser1" in data["users"]

def test_list_users_in_group_group_admin(client: TestClient, auth_token_for_user):
    # admin_group1 is admin of group1 (or its renamed version)
    token = auth_token_for_user("admin_group1", "password_admin_g1")
    headers = {"Authorization": f"Bearer {token}"}
    
    rbac_before = load_rbac_data(WORKING_RBAC_FILE)
    original_group1_current_name = "group1_renamed" if "group1_renamed" in rbac_before["grupos"] else "group1"

    response = client.get(f"/tools/grupos/{original_group1_current_name}/usuarios", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "admin_group1" in data["admins"]
    assert "testuser1" in data["users"]

def test_list_users_in_group_group_member(client: TestClient, auth_token_for_user):
    # testuser1 is a member of group1 (or its renamed version), but not an admin of it.
    token = auth_token_for_user("testuser1", "password123")
    headers = {"Authorization": f"Bearer {token}"}

    rbac_before = load_rbac_data(WORKING_RBAC_FILE)
    original_group1_current_name = "group1_renamed" if "group1_renamed" in rbac_before["grupos"] else "group1"

    response = client.get(f"/tools/grupos/{original_group1_current_name}/usuarios", headers=headers)
    assert response.status_code == 200, response.text # Members can view user list of their group
    data = response.json()
    assert "admin_group1" in data["admins"]
    assert "testuser1" in data["users"]

def test_list_users_in_group_no_permission(client: TestClient, auth_token_for_user):
    # plainuser is not a member or admin of group1 (or its renamed version)
    token = auth_token_for_user("plainuser", "plainpassword")
    headers = {"Authorization": f"Bearer {token}"}

    rbac_before = load_rbac_data(WORKING_RBAC_FILE)
    original_group1_current_name = "group1_renamed" if "group1_renamed" in rbac_before["grupos"] else "group1"

    response = client.get(f"/tools/grupos/{original_group1_current_name}/usuarios", headers=headers)
    assert response.status_code == 403, response.text
    assert response.json() == {"detail": "Acesso restrito. Você deve ser membro ou administrador do grupo, ou administrador global."}


# --- Tests for Managing Tools within Groups (Basic Add/Remove by Global Admin) ---
# Tool management by group admin will require similar tests.

@pytest.fixture
def setup_group_for_tool_management(client: TestClient, auth_token_for_user):
    ga_token = auth_token_for_user("globaladmin", "password_global")
    headers_ga = {"Authorization": f"Bearer {ga_token}"}
    group_name = "tool_manage_group"
    # Ensure tool_y exists in master data (it does)
    tool_id_to_manage = "tool_y"

    client.delete(f"/tools/grupos/{group_name}", headers=headers_ga) # Cleanup
    client.post("/tools/grupos", headers=headers_ga, json={"nome": group_name, "descricao": "Test group for tool management"})
    return group_name, tool_id_to_manage, headers_ga

def test_add_tool_to_group_global_admin(client: TestClient, auth_token_for_user, setup_group_for_tool_management):
    group_name, tool_id, headers_ga = setup_group_for_tool_management

    response = client.post(f"/tools/grupos/{group_name}/ferramentas", headers=headers_ga, json={"tool_id": tool_id})
    assert response.status_code == 200, response.text
    assert response.json() == {"message": f"Ferramenta '{tool_id}' adicionada com sucesso ao grupo '{group_name}'"}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert tool_id in rbac_data["grupos"][group_name]["ferramentas"]

def test_add_tool_to_group_tool_already_in_group(client: TestClient, auth_token_for_user, setup_group_for_tool_management):
    group_name, tool_id, headers_ga = setup_group_for_tool_management
    client.post(f"/tools/grupos/{group_name}/ferramentas", headers=headers_ga, json={"tool_id": tool_id}) # Add first time

    response = client.post(f"/tools/grupos/{group_name}/ferramentas", headers=headers_ga, json={"tool_id": tool_id}) # Try again
    assert response.status_code == 409, response.text
    assert response.json() == {"detail": f"Ferramenta '{tool_id}' já existe no grupo '{group_name}'."}

def test_add_tool_to_group_tool_not_exist_globally(client: TestClient, auth_token_for_user, setup_group_for_tool_management):
    group_name, _, headers_ga = setup_group_for_tool_management
    non_existent_tool_id = "tool_non_existent"
    response = client.post(f"/tools/grupos/{group_name}/ferramentas", headers=headers_ga, json={"tool_id": non_existent_tool_id})
    assert response.status_code == 404, response.text
    assert response.json() == {"detail": f"Ferramenta com ID '{non_existent_tool_id}' não encontrada nas definições globais."}

def test_remove_tool_from_group_global_admin(client: TestClient, auth_token_for_user, setup_group_for_tool_management):
    group_name, tool_id, headers_ga = setup_group_for_tool_management
    client.post(f"/tools/grupos/{group_name}/ferramentas", headers=headers_ga, json={"tool_id": tool_id}) # Add tool first

    response = client.delete(f"/tools/grupos/{group_name}/ferramentas/{tool_id}", headers=headers_ga)
    assert response.status_code == 200, response.text
    assert response.json() == {"message": f"Ferramenta '{tool_id}' removida com sucesso do grupo '{group_name}'"}
    
    rbac_data = load_rbac_data(WORKING_RBAC_FILE)
    assert tool_id not in rbac_data["grupos"][group_name]["ferramentas"]

def test_remove_tool_from_group_tool_not_in_group(client: TestClient, auth_token_for_user, setup_group_for_tool_management):
    group_name, tool_id_not_added, headers_ga = setup_group_for_tool_management
    # tool_id_not_added (tool_y) is not added to group_name by the fixture setup for this specific test path
    response = client.delete(f"/tools/grupos/{group_name}/ferramentas/{tool_id_not_added}", headers=headers_ga)
    assert response.status_code == 404, response.text
    assert response.json() == {"detail": f"Ferramenta '{tool_id_not_added}' não encontrada no grupo '{group_name}'."}

# TODO: Add tests for tool management by group admins.
# TODO: Add tests for GET /grupos/disponivel
