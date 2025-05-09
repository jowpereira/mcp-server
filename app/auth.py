import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.utils.dependencies import get_rbac_data
import logging
from datetime import datetime, timedelta
from typing import Optional

security = HTTPBearer()
logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

# Função para autenticação de usuário (login)
def authenticate_user(username: str, password: str):
    rbac = get_rbac_data()
    user = rbac["usuarios"].get(username)
    if not user or user["senha"] != password:
        return None
    return user

# Função para gerar JWT para usuário
def create_jwt_for_user(username: str, expires_delta: Optional[timedelta] = None) -> str:
    rbac = get_rbac_data()
    user = rbac["usuarios"].get(username)
    if not user:
        raise ValueError("Usuário não encontrado")
    to_encode = {
        "sub": username,
        "grupos": user["grupos"],
        "papel": user["papel"],
        "exp": datetime.utcnow() + (expires_delta or timedelta(hours=1))
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

# Função para extrair usuário do JWT
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        grupos = payload.get("grupos")
        papel = payload.get("papel")
        if not username or not grupos or not papel:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return {"username": username, "grupos": grupos, "papel": papel}
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.PyJWTError:
        logger.warning("Token inválido")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
