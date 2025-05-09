import requests
import os
import json
from pathlib import Path

# URL base da API
BASE_URL = 'http://localhost:8000'

def load_rbac_data():
    rbac_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'rbac.json')
    with open(rbac_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def login(username, password):
    """Login na API e retorna o token JWT"""
    response = requests.post(
        f'{BASE_URL}/tools/login',
        json={'username': username, 'password': password}
    )
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Erro ao fazer login: {response.status_code}")
        print(response.text)
        return None

def criar_usuario(token, novo_usuario):
    """Cria um novo usuário usando a API"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f'{BASE_URL}/tools/usuarios',
        json=novo_usuario,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(response.text)
    return response

def migrar_senhas(token):
    """Migra todas as senhas para hash bcrypt"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f'{BASE_URL}/tools/admin/migrate-passwords',
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(response.text)
    return response

def main():
    print("Testando autenticação e criação de usuários com senhas hasheadas")
    
    # 1. Login como superadmin
    print("\n1. Fazendo login como superadmin...")
    token = login('superadmin', 'super123')
    if not token:
        print("Falha ao fazer login como superadmin. Abortando.")
        return
    
    print(f"Login bem-sucedido! Token: {token[:20]}...")
    
    # 2. Criar novo usuário com senha hasheada
    print("\n2. Criando novo usuário 'testeuser' com senha hasheada...")
    novo_usuario = {
        "username": "testeuser",
        "password": "teste123",
        "papel": "user",
        "grupos": ["projeto_a"]
    }
    resposta_criacao = criar_usuario(token, novo_usuario)
    
    # 3. Migrar senhas existentes para hash
    print("\n3. Migrando senhas existentes para hash bcrypt...")
    resposta_migracao = migrar_senhas(token)
    
    # 4. Verificar se podemos fazer login com um usuário migrado
    print("\n4. Testando login com usuário migrado 'alice'...")
    token_migrado = login('alice', 'admin123')
    if token_migrado:
        print("Login bem-sucedido com usuário migrado!")
    else:
        print("Falha ao fazer login com usuário migrado.")
    
    # 5. Verificar se podemos fazer login com o novo usuário
    print("\n5. Testando login com novo usuário 'testeuser'...")
    token_novo = login('testeuser', 'teste123')
    if token_novo:
        print("Login bem-sucedido com novo usuário!")
    else:
        print("Falha ao fazer login com novo usuário.")

if __name__ == "__main__":
    main()
