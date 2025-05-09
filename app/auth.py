import jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.utils.dependencies import get_rbac_data
from app.utils.password_validator import validate_password
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Union

security = HTTPBearer()
logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

# Função auxiliar para verificar senhas com suporte legado
def verify_password(plain_password: str, stored_password: str) -> bool:
    # Verifica se a senha armazenada parece ser um hash bcrypt
    if stored_password.startswith('$2'):
        # Verificando hash bcrypt
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), stored_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Erro ao verificar hash bcrypt: {e}")
            return False
    else:
        # Verificando senha em texto puro (legado)
        # Isso é mantido para compatibilidade até que todas as senhas sejam migradas
        logger.warning("Verificação de senha em texto puro (legado) - por favor, migre para hash bcrypt")
        return plain_password == stored_password

# Função para validar e fazer hash de uma nova senha
def validate_and_hash_password(password: str) -> Tuple[bool, Union[str, List[str]]]:
    """
    Valida uma senha contra os requisitos de segurança e retorna um hash bcrypt se válida.
    
    Args:
        password: A senha em texto plano para validar
        
    Returns:
        Tuple[bool, Union[str, List[str]]]: Tupla com (sucesso, resultado)
            - Se sucesso=True, resultado será o hash bcrypt da senha
            - Se sucesso=False, resultado será uma string ou lista de strings com mensagens de erro
    """
    # Validar senha contra os requisitos de segurança
    is_valid, errors = validate_password(password, return_all_errors=True)
    
    if not is_valid:
        return False, errors
    
    # Fazer hash da senha com bcrypt
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return True, hashed.decode('utf-8')  # Retorna como string em vez de bytes
    except Exception as e:
        logger.error(f"Erro ao criar hash da senha: {e}")
        return False, ["Erro interno ao processar senha. Por favor, tente novamente."]

# Função para autenticação de usuário (login)
def authenticate_user(username: str, password: str):
    rbac = get_rbac_data()
    user = rbac["usuarios"].get(username)
    if not user or not verify_password(password, user["senha"]):
        return None
    return user

# Função para gerar JWT para usuário
def create_jwt_for_user(username: str, expires_delta: Optional[timedelta] = None) -> str:
    rbac = get_rbac_data()
    user = rbac["usuarios"].get(username)
    if not user:
        raise ValueError("Usuário não encontrado")
    
    logger.info(f"Auth: Creating JWT. Key used (first 10 chars): {settings.SECRET_KEY[:10] if settings.SECRET_KEY else 'None'}")

    to_encode = {
        "sub": username,
        "grupos": user["grupos"],
        "papel": user["papel"],
        "exp": datetime.utcnow() + (expires_delta or timedelta(hours=1))
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Auth: Generated JWT (first 20 chars): {encoded_jwt[:20]}...")
    return encoded_jwt

# Função para extrair usuário do JWT
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    logger.info(f"Auth: Validating JWT. Key used (first 10 chars): {settings.SECRET_KEY[:10] if settings.SECRET_KEY else 'None'}")
    logger.info(f"Auth: Received token for validation (first 20 chars): {token[:20]}...")
    try:
        # Verificar versão do PyJWT e ajustar parâmetros conforme necessário
        import jwt
        logger.info(f"Auth: Using PyJWT version {jwt.__version__}")
        
        # Modificado para incluir mais opções para compatibilidade
        # Ajustado para lidar melhor com diferentes formatos de token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_signature": True, "verify_exp": True}
        )
        
        # Log adicional para ver o payload decodificado
        logger.info(f"Auth: Successfully decoded payload: sub={payload.get('sub')}, papel={payload.get('papel')}")
        
        username = payload.get("sub")
        grupos = payload.get("grupos")
        papel = payload.get("papel")
        if not username or grupos is None or not papel:  # Modificado de not grupos para grupos is None (permite lista vazia)
            logger.warning(f"Auth: Invalid token payload - missing fields. username={username}, grupos={grupos}, papel={papel}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido: dados incompletos")
        return {"username": username, "grupos": grupos, "papel": papel}
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.PyJWTError:
        logger.warning("Token inválido")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
