from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi import Request
from fastapi.exception_handlers import request_validation_exception_handler
from app.auth import authenticate_user, create_jwt_for_user, get_current_user, validate_and_hash_password, verify_password
from app.utils.dependencies import get_rbac_data
from app.utils.password import hash_password, migrate_rbac_passwords
from app.utils.rbac_utils import is_group_admin_or_global
import logging
from typing import Optional, List, Dict, Any
from datetime import timedelta
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_ROLES = {"user", "admin", "global_admin"}

# Middleware de logging detalhado
from fastapi import FastAPI

def setup_middlewares(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Requisição: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Resposta: {response.status_code} para {request.method} {request.url}")
        return response

# RF05 - Tool Listing Schema
class ToolResponseSchema(BaseModel):
    id: str  # tool name
    nome: str
    url_base: str
    descricao: Optional[str] = None

class GroupDetailSchema(BaseModel):
    id: str  # group name
    nome: str
    descricao: Optional[str] = None
    administradores: List[str]
    usuarios: List[str]
    ferramentas_disponiveis: List[ToolResponseSchema]

class UserDetailResponse(BaseModel):
    username: str
    papel: str
    grupos: List[str]

class UserUpdateRequest(BaseModel):
    papel: Optional[str] = None
    grupos: Optional[List[str]] = None
    ferramentas_disponiveis: List[ToolResponseSchema]

# Rotas de autenticação e ferramentas
@router.post('/login', tags=["Auth"], summary="Login de usuário", description="Autentica usuário e retorna JWT.")
async def login(data: dict):
    username: Optional[str] = data.get("username")
    password: Optional[str] = data.get("password")

    if not username or not password:
        logger.warning("Tentativa de login sem usuário ou senha.")
        raise HTTPException(status_code=400, detail="Usuário e senha obrigatórios.")

    try:
        user = authenticate_user(username, password)
        if not user:
            logger.warning(f"Tentativa de login inválida para usuário '{username}'")
            raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
        
        token = create_jwt_for_user(username)
        logger.info(f"Usuário '{username}' autenticado com sucesso")
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Erro inesperado durante o login para o usuário '{username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno no servidor durante o login. Verifique os logs do servidor para mais detalhes.")

# Endpoint para renovar token JWT (token refresh)
@router.post('/refresh-token', tags=["Auth"], summary="Renovar token", description="Renova o token JWT do usuário atual.")
async def refresh_token(user=Depends(get_current_user)):
    try:
        token = create_jwt_for_user(user["username"], expires_delta=timedelta(hours=24))
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Erro ao renovar token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao renovar token."
        )

# Exemplo de rota pública (healthcheck)
@router.get('/health', tags=["Infra"], summary="Healthcheck", description="Verifica se o serviço está online.")
async def health():
    return {"status": "ok"}

# Exemplo de rota para listar grupos (apenas admin global)
@router.get('/grupos', tags=["Admin"], summary="Listar grupos", description="Lista todos os grupos com detalhes.")
async def listar_grupos(user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    grupos = []
    ferramentas_globais = rbac.get("ferramentas", {})
    for nome, g in rbac["grupos"].items():
        ferramentas_disponiveis = []
        for tool_id in g.get("ferramentas", []):
            tool = ferramentas_globais.get(tool_id)
            if tool:
                ferramentas_disponiveis.append({"id": tool_id, **tool})
            else:
                ferramentas_disponiveis.append({"id": tool_id, "nome": tool_id})
        grupos.append({
            "nome": nome,
            "descricao": g.get("descricao", ""),
            "administradores": g.get("admins", []),
            "usuarios": g.get("users", []),
            "ferramentas_disponiveis": ferramentas_disponiveis
        })
    return grupos

# RF02: Criar grupo (admin global)
class CreateGroupRequest(BaseModel):
    nome: str
    descricao: Optional[str] = None

@router.post('/grupos', tags=["Admin"], summary="Criar grupo", description="Admin global pode criar um novo grupo.")
async def criar_grupo(data: CreateGroupRequest, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    
    nome = data.nome
    descricao = data.descricao

    if not nome:
        raise HTTPException(status_code=400, detail="Nome do grupo é obrigatório.")
    if nome in rbac["grupos"]:
        raise HTTPException(status_code=409, detail="Grupo já existe.")
    
    rbac["grupos"][nome] = {
        "descricao": descricao if descricao is not None else "",
        "admins": [], 
        "users": [], 
        "ferramentas": []
    }
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Grupo '{nome}' criado por {user['username']}")
    return {"message": f"Grupo '{nome}' criado com sucesso."}

# RF02: Editar grupo (admin global)
class EditGroupRequest(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None

@router.put('/grupos/{grupo}', tags=["Admin"], summary="Editar grupo", description="Admin global pode editar nome e/ou descrição do grupo.")
async def editar_grupo(grupo: str, data: EditGroupRequest, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")

    group_data_to_update = rbac["grupos"][grupo]
    
    novo_nome = data.nome
    nova_descricao = data.descricao
    updated = False

    if nova_descricao is not None:
        group_data_to_update["descricao"] = nova_descricao
        updated = True

    if novo_nome and novo_nome != grupo:
        if novo_nome in rbac["grupos"]:
            raise HTTPException(status_code=409, detail=f"Já existe um grupo com o nome '{novo_nome}'.")
        
        for username, user_details in rbac.get("usuarios", {}).items():
            if "grupos" in user_details and grupo in user_details["grupos"]:
                user_details["grupos"].remove(grupo)
                user_details["grupos"].append(novo_nome)
        
        if "join_requests" in rbac and grupo in rbac["join_requests"]:
            rbac["join_requests"][novo_nome] = rbac["join_requests"].pop(grupo)

        rbac["grupos"][novo_nome] = rbac["grupos"].pop(grupo)
        group_data_to_update = rbac["grupos"][novo_nome]
        grupo = novo_nome
        updated = True
    
    if not updated and novo_nome is None and nova_descricao is None:
         return JSONResponse(content={"message": "Nenhuma alteração fornecida."}, status_code=200)

    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Grupo '{grupo}' editado por {user['username']}")
    return {"message": f"Grupo '{grupo}' editado com sucesso."}

# RF02: Remover grupo (admin global)
@router.delete('/grupos/{grupo}', tags=["Admin"], summary="Remover grupo", description="Admin global pode remover grupo.")
async def remover_grupo(grupo: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    # Remover grupo da lista de grupos e admin_de_grupos dos usuários
    for username, user_data in rbac["usuarios"].items():
        if "grupos" in user_data and grupo in user_data["grupos"]:
            user_data["grupos"].remove(grupo)
        if "admin_de_grupos" in user_data and grupo in user_data["admin_de_grupos"]:
            user_data["admin_de_grupos"].remove(grupo)
    # Remove group from rbac
    rbac["grupos"].pop(grupo)
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Grupo '{grupo}' removido por {user['username']}")
    return {"message": f"Grupo '{grupo}' removido com sucesso."}

# RF02: Designar admin de grupo (admin global)
@router.post('/grupos/{grupo}/admins', tags=["Admin"], summary="Designar admin de grupo", description="Admin global pode designar admin de grupo.")
async def designar_admin_grupo(grupo: str, data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    novo_admin = data.get("username")
    if not novo_admin or novo_admin not in rbac["usuarios"]:
        raise HTTPException(status_code=400, detail="Usuário inválido.")
    # Mensagem de erro exata para usuário não-membro
    if novo_admin not in rbac["grupos"][grupo]["users"]:
        raise HTTPException(status_code=400, detail=f"Usuário '{novo_admin}' não é membro do grupo '{grupo}'. Adicione como membro primeiro.")
    if novo_admin not in rbac["grupos"][grupo]["admins"]:
        rbac["grupos"][grupo]["admins"].append(novo_admin)
    if grupo not in rbac["usuarios"][novo_admin]["grupos"]:
        rbac["usuarios"][novo_admin]["grupos"].append(grupo)
    rbac["usuarios"][novo_admin]["papel"] = "admin"
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{novo_admin}' designado admin do grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{novo_admin}' agora é admin do grupo '{grupo}'"}

@router.delete('/grupos/{grupo}/admins/{username_param}', tags=["Admin"], summary="Remover admin de grupo", description="Admin global ou outro admin do grupo pode remover um admin (não a si mesmo, a menos que seja o último e admin global).")
async def remover_admin_de_grupo(grupo: str, username_param: str, current_user_identity=Depends(get_current_user)):
    rbac = get_rbac_data()
    
    if grupo not in rbac.get("grupos", {}):
        raise HTTPException(status_code=404, detail=f"Grupo '{grupo}' não encontrado.")
    
    group_admins = rbac["grupos"][grupo].get("admins", [])
    
    is_global_admin = current_user_identity["papel"] == "global_admin"
    is_group_admin = current_user_identity["username"] in group_admins

    if not (is_global_admin or is_group_admin):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global ou admin do grupo.")

    if username_param not in rbac.get("usuarios", {}):
        raise HTTPException(status_code=404, detail=f"Usuário admin '{username_param}' não encontrado.")

    if username_param not in group_admins:
        raise HTTPException(status_code=404, detail=f"Usuário '{username_param}' não é admin do grupo '{grupo}'.")

    if len(group_admins) == 1 and username_param == group_admins[0]:
        if not is_global_admin:
            raise HTTPException(status_code=400, detail="Não é possível remover o último administrador do grupo.")

    rbac["grupos"][grupo]["admins"].remove(username_param)

    is_admin_elsewhere = False
    if rbac["usuarios"][username_param].get("papel") == "global_admin":
        is_admin_elsewhere = True
    else:
        for g_name, g_details in rbac.get("grupos", {}).items():
            if username_param in g_details.get("admins", []):
                is_admin_elsewhere = True
                break
    
    if not is_admin_elsewhere:
        rbac["usuarios"][username_param]["papel"] = "user"

    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Usuário '{username_param}' removido como admin do grupo '{grupo}' por {current_user_identity['username']}.")
    return {"message": f"Usuário '{username_param}' não é mais admin do grupo '{grupo}'."}

# RF03: Adicionar usuário ao grupo (admin do grupo ou global)
@router.post('/grupos/{grupo}/usuarios', tags=["Admin"], summary="Adicionar usuário ao grupo", description="Admin do grupo ou global pode adicionar usuário ao grupo.")
async def adicionar_usuario_grupo(grupo: str, data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if not is_group_admin_or_global(user, grupo, rbac):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    username = data.get("username")
    if not username or username not in rbac["usuarios"]:
        raise HTTPException(status_code=400, detail="Usuário inválido.")
    if username in rbac["grupos"][grupo]["users"]:
        return {"message": f"Usuário '{username}' já está no grupo '{grupo}'"}
    rbac["grupos"][grupo]["users"].append(username)
    if grupo not in rbac["usuarios"][username]["grupos"]:
        rbac["usuarios"][username]["grupos"].append(grupo)
    if "members" in rbac["grupos"][grupo]:
        if username not in rbac["grupos"][grupo]["members"]:
            rbac["grupos"][grupo]["members"].append(username)
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{username}' adicionado ao grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{username}' adicionado ao grupo '{grupo}'"}

# RF03: Remover usuário do grupo (admin do grupo ou global)
@router.delete('/grupos/{grupo}/usuarios/{username}', tags=["Admin"], summary="Remover usuário do grupo", description="Admin do grupo ou global pode remover usuário do grupo.")
async def remover_usuario_grupo(grupo: str, username: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if not is_group_admin_or_global(user, grupo, rbac):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    if username not in rbac["grupos"][grupo]["users"]:
        raise HTTPException(status_code=404, detail="Usuário não está no grupo.")
    # Remove usuário do grupo
    rbac["grupos"][grupo]["users"].remove(username)
    if grupo in rbac["usuarios"][username]["grupos"]:
        rbac["usuarios"][username]["grupos"].remove(grupo)
    # Se for admin do grupo, remove também
    if username in rbac["grupos"][grupo]["admins"]:
        rbac["grupos"][grupo]["admins"].remove(username)
    # Se não restarem grupos, papel volta a 'user'
    if not rbac["usuarios"][username]["grupos"]:
        rbac["usuarios"][username]["papel"] = "user"
        rbac["usuarios"][username]["admin_de_grupos"] = []
    else:
        # Remove grupo de admin_de_grupos se necessário
        if "admin_de_grupos" in rbac["usuarios"][username] and grupo in rbac["usuarios"][username]["admin_de_grupos"]:
            rbac["usuarios"][username]["admin_de_grupos"].remove(grupo)
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{username}' removido do grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{username}' removido do grupo '{grupo}'"}

# RF03: Promover usuário a admin do grupo (admin do grupo ou global)
@router.post('/grupos/{grupo}/promover-admin', tags=["Admin"], summary="Promover usuário a admin do grupo", description="Admin do grupo ou global pode promover usuário a admin do grupo.")
async def promover_admin_grupo(grupo: str, data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user.get("grupos", []) or user["username"] not in rbac["grupos"][grupo]["admins"]):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    novo_admin = data.get("username")
    if not novo_admin or novo_admin not in rbac["usuarios"]:
        raise HTTPException(status_code=400, detail="Usuário inválido.")
    if novo_admin not in rbac["grupos"][grupo]["users"]:
        raise HTTPException(status_code=400, detail=f"Usuário '{novo_admin}' não é membro do grupo '{grupo}'. Não pode ser promovido.")
    if novo_admin not in rbac["grupos"][grupo]["admins"]:
        rbac["grupos"][grupo]["admins"].append(novo_admin)
    if grupo not in rbac["usuarios"][novo_admin]["grupos"]:
        rbac["usuarios"][novo_admin]["grupos"].append(grupo)
    rbac["usuarios"][novo_admin]["papel"] = "admin"
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{novo_admin}' promovido a admin do grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{novo_admin}' agora é admin do grupo '{grupo}'"}

# Exemplo de rota para listar usuários de um grupo (admin do grupo ou global)
@router.get('/grupos/{grupo}/usuarios', tags=["Admin"], summary="Listar usuários do grupo", description="Lista administradores e usuários de um grupo.")
async def listar_usuarios_grupo(grupo: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    if user["papel"] == "global_admin" or (grupo in user.get("grupos", []) and (user["username"] in rbac["grupos"][grupo]["admins"] or user["username"] in rbac["grupos"][grupo]["users"])):
        return {
            "admins": rbac["grupos"][grupo]["admins"],
            "users": rbac["grupos"][grupo]["users"]
        }
    raise HTTPException(status_code=403, detail="Acesso restrito. Você deve ser membro ou administrador do grupo, ou administrador global.")

# Rota para criar ferramenta (apenas admin do grupo ou global)
@router.post('/grupos/{grupo}/ferramentas', tags=["Admin"], summary="Adicionar ferramenta ao grupo", description="Admin do grupo ou global pode adicionar uma ferramenta existente ao grupo.")
async def adicionar_ferramenta_ao_grupo(grupo: str, data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user.get("grupos", []) or user["username"] not in rbac["grupos"].get(grupo, {}).get("admins", [])):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    
    nome_ferramenta = data.get("tool_id")
    if not nome_ferramenta:
        raise HTTPException(status_code=400, detail="ID da ferramenta (tool_id) é obrigatório.")

    if nome_ferramenta not in rbac.get("ferramentas", {}):
        raise HTTPException(status_code=404, detail=f"Ferramenta com ID '{nome_ferramenta}' não encontrada nas definições globais.")

    if nome_ferramenta in rbac["grupos"][grupo].get("ferramentas", []):
        raise HTTPException(status_code=409, detail=f"Ferramenta '{nome_ferramenta}' já existe no grupo '{grupo}'.")
    
    rbac["grupos"][grupo].setdefault("ferramentas", []).append(nome_ferramenta)
    
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Ferramenta '{nome_ferramenta}' adicionada ao grupo '{grupo}' por {user['username']}")
    return {"message": f"Ferramenta '{nome_ferramenta}' adicionada com sucesso ao grupo '{grupo}'"}

@router.delete('/grupos/{grupo}/ferramentas/{tool_id}', tags=["Admin"], summary="Remover ferramenta do grupo", description="Admin do grupo ou global pode remover uma ferramenta do grupo.")
async def remover_ferramenta_do_grupo(grupo: str, tool_id: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user.get("grupos", []) or user["username"] not in rbac["grupos"].get(grupo, {}).get("admins", [])):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail=f"Grupo '{grupo}' não encontrado.")
    
    group_tools = rbac["grupos"][grupo].get("ferramentas", [])
    if tool_id not in group_tools:
        raise HTTPException(status_code=404, detail=f"Ferramenta '{tool_id}' não encontrada no grupo '{grupo}'.")

    rbac["grupos"][grupo]["ferramentas"].remove(tool_id)
    
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Ferramenta '{tool_id}' removida do grupo '{grupo}' por {user['username']}")
    return {"message": f"Ferramenta '{tool_id}' removida com sucesso do grupo '{grupo}'"}

# Endpoint para listar todas as ferramentas globais definidas
@router.get("/ferramentas", response_model=List[ToolResponseSchema], tags=["Ferramentas"], summary="Listar todas as ferramentas globais", description="Lista todas as ferramentas definidas globalmente no sistema.")
async def listar_ferramentas_globais(user=Depends(get_current_user)):
    rbac = get_rbac_data()
    all_tools_definitions = rbac.get("ferramentas", {})
    ferramentas_list = []
    for tool_id, tool_def in all_tools_definitions.items():
        if isinstance(tool_def, dict):
            ferramentas_list.append(ToolResponseSchema(
                id=tool_id,
                nome=tool_def.get("nome", tool_id),
                url_base=tool_def.get("url_base", ""),
                descricao=tool_def.get("descricao")
            ))
        else:
            ferramentas_list.append(ToolResponseSchema(
                id=tool_id,
                nome=tool_id, 
                url_base="",
                descricao="Definição da ferramenta inválida"
            ))
    return ferramentas_list

# RF07: Criar usuário (admin global)
@router.post('/usuarios', tags=["Admin"], summary="Criar usuário", description="Admin global pode criar um novo usuário.")
async def criar_usuario(data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    username = data.get("username")
    password = data.get("password")
    papel = data.get("papel", "user")
    grupos = data.get("grupos", [])
    # Validação de campos obrigatórios
    if not username or not password:
        return JSONResponse(status_code=422, content={"detail": "username e password são obrigatórios."})
    # Validação de papel
    ALLOWED_ROLES = ["user", "admin", "global_admin"]
    if papel not in ALLOWED_ROLES:
        return JSONResponse(status_code=400, content={"detail": "Papel inválido."})
    # Usuário já existe
    if username in rbac["usuarios"]:
        return JSONResponse(status_code=409, content={"detail": "Usuário já existe."})
    # Validação de grupos
    for grupo in grupos:
        if grupo not in rbac["grupos"]:
            return JSONResponse(status_code=400, content={"detail": f"Grupo '{grupo}' não encontrado."})
    # Criação do usuário
    from app.utils.password import hash_password
    senha_hash = hash_password(password)
    rbac["usuarios"][username] = {
        "senha": senha_hash,
        "grupos": grupos,
        "papel": papel
    }
    for grupo in grupos:
        if "users" not in rbac["grupos"][grupo]:
            rbac["grupos"][grupo]["users"] = []
        if username not in rbac["grupos"][grupo]["users"]:
            rbac["grupos"][grupo]["users"].append(username)
        if "members" in rbac["grupos"][grupo]:
            if username not in rbac["grupos"][grupo]["members"]:
                rbac["grupos"][grupo]["members"].append(username)
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{username}' criado por {user['username']}")
    return JSONResponse(status_code=201, content={
        "username": username,
        "papel": papel,
        "grupos": grupos
    })

# Endpoint para alterar senha do usuário
@router.post('/usuarios/alterar-senha', tags=["User"], summary="Alterar senha", description="Permite ao usuário alterar sua própria senha.")
async def alterar_senha(data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    username = user["username"]
    
    senha_atual = data.get("senha_atual")
    nova_senha = data.get("nova_senha")
    
    if not senha_atual or not nova_senha:
        raise HTTPException(
            status_code=400, 
            detail="Senha atual e nova senha são obrigatórias"
        )
    
    stored_password = rbac["usuarios"][username]["senha"]
    if not verify_password(senha_atual, stored_password):
        logger.warning(f"Tentativa de alteração de senha com senha atual incorreta para '{username}'")
        raise HTTPException(
            status_code=401, 
            detail="Senha atual incorreta"
        )
    
    if verify_password(nova_senha, stored_password):
        raise HTTPException(
            status_code=400, 
            detail="A nova senha não pode ser igual à senha atual"
        )
    
    senha_valida, resultado = validate_and_hash_password(nova_senha)
    if not senha_valida:
        if isinstance(resultado, list):
            raise HTTPException(status_code=400, detail={
                "message": "A senha não atende aos requisitos de segurança",
                "errors": resultado
            })
        else:
            raise HTTPException(status_code=400, detail=resultado)
    
    hashed_password = resultado
    
    rbac["usuarios"][username]["senha"] = hashed_password
    
    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Senha alterada com sucesso para o usuário '{username}'")
    return {"message": "Senha alterada com sucesso"}

# Endpoint para listar todos os usuários (apenas admin global)
@router.get("/usuarios", tags=["Admin"], summary="Listar todos os usuários", description="Admin global pode listar todos os usuários.")
async def listar_usuarios(user=Depends(get_current_user)):
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    rbac = get_rbac_data()
    user_list = []
    for username, details in rbac.get("usuarios", {}).items():
        user_list.append({
            "username": username,
            "papel": details.get("papel", "user"),
            "grupos": details.get("grupos", []),
            "admin_de_grupos": details.get("admin_de_grupos", []),
        })
    return user_list

# Endpoint para obter detalhes de um usuário específico (apenas admin global)
@router.get("/usuarios/{username_param}", response_model=UserDetailResponse, tags=["Admin"], summary="Obter detalhes de um usuário", description="Admin global pode obter detalhes de um usuário específico.")
async def obter_usuario(username_param: str, user=Depends(get_current_user)):
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    
    rbac = get_rbac_data()
    user_data = rbac.get("usuarios", {}).get(username_param)
    
    if not user_data:
        raise HTTPException(status_code=404, detail=f"Usuário '{username_param}' não encontrado.")
    
    return UserDetailResponse(
        username=username_param,
        papel=user_data.get("papel", "user"),
        grupos=user_data.get("grupos", [])
    )

# Endpoint para atualizar um usuário (apenas admin global)
@router.put("/usuarios/{username_param}", response_model=UserDetailResponse, tags=["Admin"], summary="Atualizar usuário", description="Admin global pode atualizar o papel e os grupos de um usuário.")
async def atualizar_usuario(username_param: str, data: UserUpdateRequest, current_user_identity=Depends(get_current_user)):
    if current_user_identity["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")

    rbac = get_rbac_data()
    if username_param not in rbac.get("usuarios", {}):
        raise HTTPException(status_code=404, detail=f"Usuário '{username_param}' não encontrado.")

    user_to_update = rbac["usuarios"][username_param]
    updated = False

    if data.papel is not None:
        if data.papel not in ["user", "admin", "global_admin"]:
            raise HTTPException(status_code=400, detail="Papel inválido. Deve ser 'user', 'admin' ou 'global_admin'.")
        if username_param == current_user_identity["username"] and data.papel != current_user_identity["papel"]:
            if current_user_identity["papel"] == "global_admin" and data.papel != "global_admin":
                global_admins = [u for u, d in rbac.get("usuarios", {}).items() if d.get("papel") == "global_admin"]
                if len(global_admins) <= 1:
                    raise HTTPException(status_code=400, detail="Não é possível remover o último administrador global.")
        user_to_update["papel"] = data.papel
        updated = True

    if data.grupos is not None:
        for grupo_nome in data.grupos:
            if grupo_nome not in rbac.get("grupos", {}):
                raise HTTPException(status_code=400, detail=f"Grupo '{grupo_nome}' não encontrado.")
        
        old_grupos = set(user_to_update.get("grupos", []))
        new_grupos_set = set(data.grupos)

        for grupo_nome in old_grupos - new_grupos_set:
            if grupo_nome in rbac["grupos"]:
                if username_param in rbac["grupos"][grupo_nome].get("usuarios", []):
                    rbac["grupos"][grupo_nome]["usuarios"].remove(username_param)
                if username_param in rbac["grupos"][grupo_nome].get("admins", []):
                    rbac["grupos"][grupo_nome]["admins"].remove(username_param)
        
        for grupo_nome in new_grupos_set - old_grupos:
            if grupo_nome in rbac["grupos"]:
                if username_param not in rbac["grupos"][grupo_nome].get("usuarios", []):
                    rbac["grupos"][grupo_nome].setdefault("usuarios", []).append(username_param)

        user_to_update["grupos"] = data.grupos
        updated = True

    if updated:
        from app.config import settings
        import json
        rbac_path = settings.RBAC_FILE
        with open(rbac_path, 'w', encoding='utf-8') as f:
            json.dump(rbac, f, indent=2, ensure_ascii=False)
        logger.info(f"Usuário '{username_param}' atualizado por {current_user_identity['username']}.")
    
    return UserDetailResponse(
        username=username_param,
        papel=user_to_update.get("papel"),
        grupos=user_to_update.get("grupos", [])
    )

# Endpoint para deletar um usuário (apenas admin global)
@router.delete("/usuarios/{username_param}", status_code=200, tags=["Admin"], summary="Deletar usuário", description="Admin global pode deletar um usuário.")
async def deletar_usuario(username_param: str, current_user_identity=Depends(get_current_user)):
    if current_user_identity["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")

    if username_param == current_user_identity["username"]:
        raise HTTPException(status_code=400, detail="Não é possível deletar a si mesmo.")

    rbac = get_rbac_data()
    if username_param not in rbac.get("usuarios", {}):
        raise HTTPException(status_code=404, detail=f"Usuário '{username_param}' não encontrado.")

    for grupo_nome, grupo_details in rbac.get("grupos", {}).items():
        if username_param in grupo_details.get("usuarios", []):
            grupo_details["usuarios"].remove(username_param)
        if username_param in grupo_details.get("admins", []):
            grupo_details["admins"].remove(username_param)

    del rbac["usuarios"][username_param]

    from app.config import settings
    import json
    rbac_path = settings.RBAC_FILE
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Usuário '{username_param}' deletado por {current_user_identity['username']}.")
    return {"message": f"Usuário '{username_param}' deletado com sucesso."}

# Endpoint para obter os requisitos de senha
@router.get('/usuarios/requisitos-senha', tags=["User"], summary="Requisitos de senha", description="Retorna os requisitos de segurança para senhas.")
async def requisitos_senha():
    from app.utils.password_validator import default_validator
    
    requisitos = default_validator.get_requirements_text()
    
    return {
        "requisitos": requisitos,
        "min_length": default_validator.min_length,
        "require_uppercase": default_validator.require_uppercase,
        "require_lowercase": default_validator.require_lowercase,
        "require_digits": default_validator.require_digits,
        "require_special": default_validator.require_special,
        "min_unique_chars": default_validator.min_unique_chars
    }

# Endpoint para migrar senhas em texto puro para hashes bcrypt (apenas admin global)
@router.post('/admin/migrate-passwords', tags=["Admin"], summary="Migrar senhas", description="Admin global pode migrar senhas em texto puro para hashes bcrypt.")
async def migrar_senhas(user=Depends(get_current_user)):
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    
    from pathlib import Path
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    
    if migrate_rbac_passwords(str(rbac_path)):
        return {"message": "Migração de senhas concluída com sucesso."}
    else:
        raise HTTPException(status_code=500, detail="Erro ao migrar senhas. Verifique os logs do servidor.")

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

# Endpoint para listar grupos disponíveis para solicitação (que o usuário não participa)
@router.get('/grupos/disponivel', tags=["Grupos"], summary="Listar grupos disponíveis", description="Lista grupos que o usuário não faz parte e pode solicitar acesso.")
async def listar_grupos_disponiveis(user=Depends(get_current_user)):
    rbac = get_rbac_data()
    username = user["username"]
    
    user_grupos = rbac["usuarios"][username]["grupos"]
    
    grupos_disponiveis = [
        grupo for grupo in rbac["grupos"].keys()
        if grupo not in user_grupos
    ]
    
    return {"grupos": grupos_disponiveis}

@router.get("/user_tools", response_model=List[ToolResponseSchema], summary="Listar ferramentas disponíveis para o usuário logado")
async def list_user_tools(current_user_data: dict = Depends(get_current_user)):
    user_tools: Dict[str, ToolResponseSchema] = {}
    rbac = get_rbac_data()
    all_tools_definitions = rbac.get("ferramentas", {})

    if not isinstance(current_user_data, dict) or "username" not in current_user_data:
        raise HTTPException(status_code=403, detail="Usuário não identificado.")

    user_groups = current_user_data.get("grupos", [])
    if not isinstance(user_groups, list):
        user_groups = []

    for group_name in user_groups:
        group_details = rbac.get("grupos", {}).get(group_name)
        if group_details and isinstance(group_details, dict):
            tool_names_in_group = group_details.get("ferramentas", []) 
            if not isinstance(tool_names_in_group, list):
                tool_names_in_group = []

            for tool_name in tool_names_in_group:
                if tool_name not in user_tools:
                    tool_definition = all_tools_definitions.get(tool_name)
                    if tool_definition and isinstance(tool_definition, dict):
                        user_tools[tool_name] = ToolResponseSchema(
                            id=tool_name,
                            nome=tool_name,
                            url_base=tool_definition.get("url_base", ""),
                            descricao=tool_definition.get("descricao")
                        )

    return list(user_tools.values())
