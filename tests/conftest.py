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
MASTER_RBAC_FILE = os.path.join(BASE_DIR, "data", "test_rbac_fixed.json") # Our fixed master file with all test users
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

    # Primeiro verificamos se o arquivo master de RBAC está disponível
    if not os.path.exists(MASTER_RBAC_FILE):
        print(f"AVISO: Arquivo master RBAC {MASTER_RBAC_FILE} não encontrado!")
        # Ao invés de apenas criar um vazio, vamos usar o que temos no test_rbac_master.json
        master_data_path = os.path.join(BASE_DIR, "data", "test_rbac_master.json")
        if os.path.exists(master_data_path):
            print(f"Usando dados de teste de {master_data_path}")
            shutil.copyfile(master_data_path, WORKING_RBAC_FILE)
        else:
            print("Criando dados RBAC padrão para testes")
            # Criar dados padrão que incluem o usuário globaladmin
            default_rbac = {
                "grupos": {
                    "group1": {
                        "descricao": "Test Group 1",
                        "admins": ["admin_group1"],
                        "users": ["testuser1", "admin_group1"],
                        "ferramentas": ["tool_x"]
                    }
                },
                "usuarios": {
                    "testuser1": {
                        "senha": "$2b$12$vNigeVwdz9D/8x9YQm2RzeK42z9k5aGIDtutY1766N5eZx/ub3azO",
                        "grupos": ["group1"],
                        "papel": "user"
                    },
                    "admin_group1": {
                        "senha": "$2b$12$Ezb.NwWPT3mBrp9wUwU1FuCgDCDQ.qQ/aXCGu49S2dqn4VihIIiJy",
                        "grupos": ["group1"],
                        "papel": "admin"
                    },
                    "globaladmin": {
                        "senha": "$2b$12$qL7NEHc85jf/.JK0CJpcI.5FO11s3GEQnmCz1xV/FrKNzezBZXmam",
                        "grupos": [],
                        "papel": "global_admin"
                    }
                }
            }
            with open(WORKING_RBAC_FILE, 'w') as f:
                json.dump(default_rbac, f, indent=2)

    # Handling for MASTER_REQUESTS_FILE remains the same for now
    if not os.path.exists(MASTER_REQUESTS_FILE):
        initial_requests_data = {"requests": []}
        with open(MASTER_REQUESTS_FILE, 'w') as f:
            json.dump(initial_requests_data, f, indent=2)


@pytest.fixture(scope="function", autouse=True)
def manage_test_data_files():
    """
    Fixture para gerenciar os arquivos de dados de teste.
    Roda antes de cada teste para garantir um ambiente limpo com dados consistentes.
    """
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Definir os dados mínimos necessários para os testes funcionarem
    needed_users = [
        "globaladmin", "testuser1", "plainuser", "admin_group1",
        "requesteruser", "admin_group_for_request"
    ]
    
    # Sempre recria o arquivo de teste a partir do master para cada teste
    print(f"Reiniciando dados de teste para um novo teste...")
    # Garante que o RBAC esteja em um estado consistente para cada teste
      # Definir uma senha hash para o globaladmin (password_global)
    globaladmin_password_hash = "$2b$12$PClOP0mZrASxU6NGlXL4Z.lAAsmOjRmuS/slyaepN2HAV/dIzA25W"  # password_global
    
    fallback_rbac = {
        "grupos": {
            "group1": {
                "descricao": "Test Group 1",
                "admins": ["admin_group1"],
                "users": ["testuser1", "admin_group1"],
                "ferramentas": ["tool_x"]
            },
            "group_for_request": {
                "descricao": "Group for access requests",
                "admins": ["admin_group_for_request"],
                "users": ["admin_group_for_request"],
                "ferramentas": []
            }
        },
        "usuarios": {
            "testuser1": {
                "senha": "$2b$12$vNigeVwdz9D/8x9YQm2RzeK42z9k5aGIDtutY1766N5eZx/ub3azO",  # password123
                "grupos": ["group1"],
                "papel": "user"
            },
            "admin_group1": {
                "senha": "$2b$12$Ezb.NwWPT3mBrp9wUwU1FuCgDCDQ.qQ/aXCGu49S2dqn4VihIIiJy",  # password123
                "grupos": ["group1"],
                "papel": "admin"
            },
            "globaladmin": {
                "senha": globaladmin_password_hash,
                "grupos": [],
                "papel": "global_admin"
            },
            "plainuser": {
                "senha": "plainpassword",
                "grupos": [],
                "papel": "user"
            },
            "requesteruser": {
                "senha": "$2b$12$wUoxriexlDcxrzwCbeLPv.KdcW5YjszfEGo1wuIP2HbYkzih/Nfrq",  # password123
                "grupos": [],
                "papel": "user"
            },
            "admin_group_for_request": {
                "senha": "$2b$12$Dg3tXO7RIeVmeI1V/0mWHe44Ifz5IqxSVtnP6bjPBrvPDmAVNkmJi",  # password123
                "grupos": ["group_for_request"],
                "papel": "admin"
            }
        },
        "ferramentas": {
            "tool_x": {
                "nome": "Ferramenta X",
                "url_base": "/tools/ferramenta_x",
                "descricao": "Ferramenta de Teste X"
            },
            "tool_y": {
                "nome": "Ferramenta Y",
                "url_base": "/tools/ferramenta_y",
                "descricao": "Ferramenta de Teste Y"
            }
        }
    }
    fallback_requests = {"requests": []}    # Sempre usa o arquivo master do RBAC para cada teste
    if os.path.exists(MASTER_RBAC_FILE):
        print(f"Copiando dados RBAC do arquivo master: {MASTER_RBAC_FILE}")
        # Sempre copia o arquivo master para garantir um estado consistente
        try:
            with open(MASTER_RBAC_FILE, 'r') as f:
                master_rbac = json.load(f)
            
            # Garante que o master_rbac tem todos os usuários necessários
            usuarios = master_rbac.get("usuarios", {})
            missing_users = [u for u in needed_users if u not in usuarios]
            
            if missing_users:
                print(f"Adicionando usuários ausentes no arquivo master...")
                # Adiciona usuários ausentes ao arquivo master
                for user in missing_users:
                    if user in fallback_rbac["usuarios"]:
                        master_rbac["usuarios"][user] = fallback_rbac["usuarios"][user]
            
            # Escreve um novo arquivo de trabalho
            with open(WORKING_RBAC_FILE, 'w') as f:
                json.dump(master_rbac, f, indent=2)
            
        except Exception as e:
            print(f"Erro ao atualizar {WORKING_RBAC_FILE} a partir do master: {e}")
            print("Usando dados de fallback...")
            with open(WORKING_RBAC_FILE, 'w') as f:
                json.dump(fallback_rbac, f, indent=2)
    else:
        print(f"Aviso: MASTER_RBAC_FILE ({MASTER_RBAC_FILE}) não encontrado.")
        print(f"Criando arquivo de teste RBAC com usuários padrão...")
        with open(WORKING_RBAC_FILE, 'w') as f:
            json.dump(fallback_rbac, f, indent=2)

    # Gerencia o arquivo de solicitações
    if os.path.exists(MASTER_REQUESTS_FILE):
        shutil.copyfile(MASTER_REQUESTS_FILE, WORKING_REQUESTS_FILE)
    else:
        print(f"Aviso: MASTER_REQUESTS_FILE ({MASTER_REQUESTS_FILE}) não encontrado.")
        print("Criando arquivo de solicitações vazio...")
        with open(WORKING_REQUESTS_FILE, 'w') as f:
            json.dump(fallback_requests, f, indent=2)
            
    yield


@pytest.fixture(scope="session", autouse=True)
def verify_test_data():
    """Verifica se o arquivo test_rbac.json contém os usuários necessários para os testes."""
    print("Verificando dados de teste para usuários necessários...")
    try:
        with open(WORKING_RBAC_FILE, 'r') as f:
            rbac_data = json.load(f)
        
        usuarios = rbac_data.get("usuarios", {})
        needed_users = ["globaladmin", "testuser1", "plainuser"]
        
        for user in needed_users:
            if user not in usuarios:
                print(f"AVISO: Usuário '{user}' não encontrado em {WORKING_RBAC_FILE}")
            else:
                print(f"Usuário '{user}' encontrado em {WORKING_RBAC_FILE}")
                
        # Verificar senha do globaladmin especificamente
        if "globaladmin" in usuarios:
            print(f"Hash da senha para globaladmin: {usuarios['globaladmin']['senha'][:20]}...")
    except Exception as e:
        print(f"Erro ao verificar dados de teste: {e}")

@pytest.fixture(scope="module")
def client():
    if not FASTAPI_APP_IMPORTED or app is None:
        pytest.fail("FastAPI app could not be imported. Check PYTHONPATH and imports in conftest.py.")
    
    # Verificar variáveis de ambiente críticas para os testes
    print(f"SECRET_KEY nos testes: {os.getenv('SECRET_KEY')}")
    print(f"RBAC_FILE nos testes: {os.getenv('RBAC_FILE')}")
    
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_token_for_user(client: TestClient):
    def _get_token(username, password):
        print(f"Tentando obter token para usuário: {username} com senha: {password}")
        response = client.post("/tools/login", json={"username": username, "password": password})
        print(f"Resposta do login: {response.status_code}")
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"Token obtido com sucesso: {token[:20]}...")
            return token
        else:
            print(f"Falha ao obter token. Resposta: {response.text}")
            return None
    return _get_token
