from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth import authenticate_user, create_jwt_for_user, get_current_user
from app.utils.dependencies import get_rbac_data
import logging
from typing import Optional

# Example tool endpoints
# Segue boas práticas: logging, tipagem, modularidade

tools_router = APIRouter()
logger = logging.getLogger(__name__)

# Toda a lógica de rota foi movida para routes.py
# Este arquivo pode ser mantido para lógica utilitária de ferramentas, se necessário.

# Utilitário para checagem de permissão

def has_permission(user: dict, ferramenta: str) -> bool:
    rbac = get_rbac_data()
    # Global admin tem acesso a tudo
    if user["papel"] == "global_admin":
        return True
    return any(
        g in rbac["grupos"] and ferramenta in rbac["grupos"][g]["ferramentas"]
        for g in user["grupos"]
    )
