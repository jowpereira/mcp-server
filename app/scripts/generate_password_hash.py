#!/usr/bin/env python3
import bcrypt
import sys

def generate_password_hash(password):
    """
    Gera um hash bcrypt para a senha fornecida.
    
    Args:
        password (str): A senha em texto plano
    
    Returns:
        str: O hash bcrypt da senha
    """
    # Gerar um salt e fazer hash da senha
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password(plain_password, hashed_password):
    """
    Verifica se a senha em texto plano corresponde ao hash bcrypt.
    
    Args:
        plain_password (str): A senha em texto plano
        hashed_password (str): O hash bcrypt da senha
    
    Returns:
        bool: True se a senha corresponde ao hash, False caso contrário
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_password_hash.py <senha>")
        sys.exit(1)
    
    password = sys.argv[1]
    hash_value = generate_password_hash(password)
    print(f"Hash para a senha '{password}':")
    print(hash_value)
    
    # Verificar se o hash funciona
    verification = check_password(password, hash_value)
    print(f"Verificação do hash: {'Sucesso' if verification else 'Falha'}")
    
    # Se um segundo argumento é fornecido, é um hash a ser verificado
    if len(sys.argv) >= 3:
        check_hash = sys.argv[2]
        verification = check_password(password, check_hash)
        print(f"Verificação do hash fornecido: {'Sucesso' if verification else 'Falha'}")
