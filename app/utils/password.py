import bcrypt
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """
    Cria um hash da senha usando bcrypt.
    
    Args:
        password: A senha em texto claro para ser hasheada
        
    Returns:
        str: O hash da senha como string codificada em UTF-8
    """
    # Gera um hash usando bcrypt (salt é gerado automaticamente e embutido no hash resultante)
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')  # Retorna como string em vez de bytes

def migrate_rbac_passwords(rbac_file: str, backup: bool = True):
    """
    Migra todas as senhas em texto plano no arquivo RBAC para hashes bcrypt.
    
    Args:
        rbac_file: Caminho para o arquivo RBAC JSON
        backup: Se deve criar uma cópia de backup do arquivo original
        
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    try:
        # Carregar dados RBAC
        rbac_path = Path(rbac_file)
        
        if not rbac_path.exists():
            logger.error(f"Arquivo RBAC não encontrado: {rbac_file}")
            return False
            
        if backup:
            # Cria backup
            import shutil
            backup_path = rbac_path.with_suffix(f"{rbac_path.suffix}.bak")
            shutil.copy2(rbac_path, backup_path)
            logger.info(f"Backup criado em: {backup_path}")
        
        # Carrega o arquivo JSON
        with open(rbac_path, 'r', encoding='utf-8') as f:
            rbac_data = json.load(f)
        
        # Atualiza as senhas
        usuarios_modificados = 0
        for username, user_data in rbac_data.get("usuarios", {}).items():
            if "senha" in user_data and not user_data["senha"].startswith("$2"):
                # Senha em texto plano, criar hash
                clear_password = user_data["senha"]
                hashed_password = hash_password(clear_password)
                user_data["senha"] = hashed_password
                usuarios_modificados += 1
        
        # Salva o arquivo atualizado
        with open(rbac_path, 'w', encoding='utf-8') as f:
            json.dump(rbac_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Migração concluída: {usuarios_modificados} senhas convertidas para hash bcrypt")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao migrar senhas: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Configuração de logging
    logging.basicConfig(level=logging.INFO)
    
    # Path relativo ao arquivo de script
    default_rbac_path = str(Path(__file__).parent.parent.parent / 'data' / 'rbac.json')
    
    # Executar a migração
    migrate_rbac_passwords(default_rbac_path)
