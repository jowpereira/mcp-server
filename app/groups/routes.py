from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from app.auth import authenticate_user, create_jwt_for_user, get_current_user
from app.utils.dependencies import get_rbac_data
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

# Middleware de logging detalhado
from fastapi import FastAPI

def setup_middlewares(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Requisição: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Resposta: {response.status_code} para {request.method} {request.url}")
        return response

# Rotas de autenticação e ferramentas
@router.post('/login', tags=["Auth"], summary="Login de usuário", description="Autentica usuário e retorna JWT.")
async def login(data: dict):
    username: Optional[str] = data.get("username")
    password: Optional[str] = data.get("password")
    if not username or not password:
        logger.warning("Tentativa de login sem usuário ou senha.")
        raise HTTPException(status_code=400, detail="Usuário e senha obrigatórios.")
    user = authenticate_user(username, password)
    if not user:
        logger.warning(f"Tentativa de login inválida para usuário '{username}'")
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    token = create_jwt_for_user(username)
    logger.info(f"Usuário '{username}' autenticado com sucesso")
    return {"access_token": token, "token_type": "bearer"}

# Exemplo de rota pública (healthcheck)
@router.get('/health', tags=["Infra"], summary="Healthcheck", description="Verifica se o serviço está online.")
async def health():
    return {"status": "ok"}

# Exemplo de rota para listar grupos (apenas admin global)
@router.get('/grupos', tags=["Admin"], summary="Listar grupos", description="Lista todos os grupos. Apenas para admin global.")
async def listar_grupos(user=Depends(get_current_user)):
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    rbac = get_rbac_data()
    return {"grupos": list(rbac["grupos"].keys())}

# Exemplo de rota para listar usuários de um grupo (admin do grupo ou global)
@router.get('/grupos/{grupo}/usuarios', tags=["Admin"], summary="Listar usuários do grupo", description="Lista usuários de um grupo. Admin do grupo ou global.")
async def listar_usuarios_grupo(grupo: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and grupo not in user["grupos"]:
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    return {
        "admins": rbac["grupos"][grupo]["admins"],
        "users": rbac["grupos"][grupo]["users"]
    }

# Rotas de ferramentas (com OPTIONS)
def has_permission(user: dict, ferramenta: str) -> bool:
    rbac = get_rbac_data()
    if user["papel"] == "global_admin":
        return True
    return any(
        g in rbac["grupos"] and ferramenta in rbac["grupos"][g]["ferramentas"]
        for g in user["grupos"]
    )

@router.options('/ferramenta_x', tags=["Ferramentas"])
async def options_ferramenta_x(response: Response):
    response.headers["Allow"] = "GET,OPTIONS"
    return Response(status_code=204)

@router.get('/ferramenta_x', tags=["Ferramentas"], summary="Ferramenta X", description="Executa a ferramenta X se o usuário tiver permissão.")
async def ferramenta_x(user=Depends(get_current_user)):
    if not has_permission(user, "ferramenta_x"):
        logger.warning(f"Acesso negado a ferramenta_x para {user['username']}")
        raise HTTPException(status_code=403, detail="Acesso negado")
    logger.info(f"Usuário {user['username']} executou ferramenta_x")
    return {"result": f"Execução da ferramenta X por {user['username']}"}

@router.options('/ferramenta_y', tags=["Ferramentas"])
async def options_ferramenta_y(response: Response):
    response.headers["Allow"] = "GET,OPTIONS"
    return Response(status_code=204)

@router.get('/ferramenta_y', tags=["Ferramentas"], summary="Ferramenta Y", description="Executa a ferramenta Y se o usuário tiver permissão.")
async def ferramenta_y(user=Depends(get_current_user)):
    if not has_permission(user, "ferramenta_y"):
        logger.warning(f"Acesso negado a ferramenta_y para {user['username']}")
        raise HTTPException(status_code=403, detail="Acesso negado")
    logger.info(f"Usuário {user['username']} executou ferramenta_y")
    return {"result": f"Execução da ferramenta Y por {user['username']}"}

@router.options('/ferramenta_z', tags=["Ferramentas"])
async def options_ferramenta_z(response: Response):
    response.headers["Allow"] = "GET,OPTIONS"
    return Response(status_code=204)

@router.get('/ferramenta_z', tags=["Ferramentas"], summary="Ferramenta Z", description="Executa a ferramenta Z se o usuário tiver permissão.")
async def ferramenta_z(user=Depends(get_current_user)):
    if not has_permission(user, "ferramenta_z"):
        logger.warning(f"Acesso negado a ferramenta_z para {user['username']}")
        raise HTTPException(status_code=403, detail="Acesso negado")
    logger.info(f"Usuário {user['username']} executou ferramenta_z")
    return {"result": f"Execução da ferramenta Z por {user['username']}"}
