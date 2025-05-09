from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from app.auth import authenticate_user, create_jwt_for_user, get_current_user, validate_and_hash_password, verify_password
from app.utils.dependencies import get_rbac_data
from app.utils.password import hash_password, migrate_rbac_passwords
import logging
from typing import Optional, List, Dict, Any
from datetime import timedelta
from pydantic import BaseModel

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
@router.get('/grupos', response_model=List[GroupDetailSchema], tags=["Admin"], summary="Listar grupos detalhadamente", description="Lista todos os grupos com detalhes. Apenas para admin global.")
async def listar_grupos(user=Depends(get_current_user)):
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    rbac = get_rbac_data()
    grupos_detalhados = []
    all_tools_definitions = rbac.get("ferramentas", {})

    for nome_grupo, detalhes_grupo_data in rbac.get("grupos", {}).items():
        ferramentas_do_grupo_obj = []
        nomes_ferramentas_no_grupo = detalhes_grupo_data.get("ferramentas", [])
        if not isinstance(nomes_ferramentas_no_grupo, list):
            nomes_ferramentas_no_grupo = []

        for nome_ferramenta in nomes_ferramentas_no_grupo:
            tool_def = all_tools_definitions.get(nome_ferramenta)
            if tool_def and isinstance(tool_def, dict):
                ferramentas_do_grupo_obj.append(ToolResponseSchema(
                    id=nome_ferramenta,
                    nome=nome_ferramenta,
                    url_base=tool_def.get("url_base", ""),
                    descricao=tool_def.get("descricao")
                ))
            else:
                ferramentas_do_grupo_obj.append(ToolResponseSchema(
                    id=nome_ferramenta,
                    nome=nome_ferramenta,
                    url_base="", 
                    descricao="Definição da ferramenta não encontrada ou inválida"
                ))
        
        grupo_detalhado = GroupDetailSchema(
            id=nome_grupo,
            nome=nome_grupo,
            descricao=detalhes_grupo_data.get("descricao"),
            administradores=detalhes_grupo_data.get("admins", []),
            usuarios=detalhes_grupo_data.get("users", []),
            ferramentas_disponiveis=ferramentas_do_grupo_obj
        )
        grupos_detalhados.append(grupo_detalhado)
    return grupos_detalhados

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
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
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

    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
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
    rbac["grupos"].pop(grupo)
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
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
    if novo_admin not in rbac["grupos"][grupo]["admins"]:
        rbac["grupos"][grupo]["admins"].append(novo_admin)
    if grupo not in rbac["usuarios"][novo_admin]["grupos"]:
        rbac["usuarios"][novo_admin]["grupos"].append(grupo)
    rbac["usuarios"][novo_admin]["papel"] = "admin"
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{novo_admin}' promovido a admin do grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{novo_admin}' agora é admin do grupo '{grupo}'"}

# RF03: Adicionar usuário ao grupo (admin do grupo ou global)
@router.post('/grupos/{grupo}/usuarios', tags=["Admin"], summary="Adicionar usuário ao grupo", description="Admin do grupo ou global pode adicionar usuário ao grupo.")
async def adicionar_usuario_grupo(grupo: str, data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user["grupos"] or user["username"] not in rbac["grupos"][grupo]["admins"]):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    novo_user = data.get("username")
    if not novo_user or novo_user not in rbac["usuarios"]:
        raise HTTPException(status_code=400, detail="Usuário inválido.")
    if novo_user not in rbac["grupos"][grupo]["users"]:
        rbac["grupos"][grupo]["users"].append(novo_user)
    if grupo not in rbac["usuarios"][novo_user]["grupos"]:
        rbac["usuarios"][novo_user]["grupos"].append(grupo)
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{novo_user}' adicionado ao grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{novo_user}' adicionado ao grupo '{grupo}'"}

# RF03: Remover usuário do grupo (admin do grupo ou global)
@router.delete('/grupos/{grupo}/usuarios/{username}', tags=["Admin"], summary="Remover usuário do grupo", description="Admin do grupo ou global pode remover usuário do grupo.")
async def remover_usuario_grupo(grupo: str, username: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user["grupos"] or user["username"] not in rbac["grupos"][grupo]["admins"]):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    if username not in rbac["grupos"][grupo]["users"]:
        raise HTTPException(status_code=404, detail="Usuário não está no grupo.")
    rbac["grupos"][grupo]["users"].remove(username)
    if grupo in rbac["usuarios"][username]["grupos"]:
        rbac["usuarios"][username]["grupos"].remove(grupo)
    if not rbac["usuarios"][username]["grupos"]:
        rbac["usuarios"][username]["papel"] = "user"
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{username}' removido do grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{username}' removido do grupo '{grupo}'"}

# RF03: Promover usuário a admin do grupo (admin do grupo ou global)
@router.post('/grupos/{grupo}/promover-admin', tags=["Admin"], summary="Promover usuário a admin do grupo", description="Admin do grupo ou global pode promover usuário a admin do grupo.")
async def promover_admin_grupo(grupo: str, data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user["grupos"] or user["username"] not in rbac["grupos"][grupo]["admins"]):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    novo_admin = data.get("username")
    if not novo_admin or novo_admin not in rbac["usuarios"]:
        raise HTTPException(status_code=400, detail="Usuário inválido.")
    if novo_admin not in rbac["grupos"][grupo]["admins"]:
        rbac["grupos"][grupo]["admins"].append(novo_admin)
    if grupo not in rbac["usuarios"][novo_admin]["grupos"]:
        rbac["usuarios"][novo_admin]["grupos"].append(grupo)
    rbac["usuarios"][novo_admin]["papel"] = "admin"
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{novo_admin}' promovido a admin do grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{novo_admin}' agora é admin do grupo '{grupo}'"}

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

# Rota para criar ferramenta (apenas admin do grupo ou global)
@router.post('/grupos/{grupo}/ferramentas', tags=["Admin"], summary="Criar ferramenta", description="Admin do grupo ou global pode criar uma nova ferramenta para o grupo.")
async def criar_ferramenta(grupo: str, data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user["grupos"] or user["username"] not in rbac["grupos"][grupo]["admins"]):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    nome = data.get("nome")
    if not nome:
        raise HTTPException(status_code=400, detail="Nome da ferramenta é obrigatório.")
    if nome in rbac["grupos"][grupo]["ferramentas"]:
        raise HTTPException(status_code=409, detail="Ferramenta já existe no grupo.")
    rbac["grupos"][grupo]["ferramentas"].append(nome)
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Ferramenta '{nome}' criada no grupo '{grupo}' por {user['username']}")
    return {"message": f"Ferramenta '{nome}' criada com sucesso no grupo '{grupo}'"}

# RF06: Usuário solicita acesso a grupo (workflow de aprovação)
@router.post('/grupos/{grupo}/solicitar-entrada', tags=["User"], summary="Solicitar entrada em grupo", description="Usuário solicita acesso a um grupo. Admin do grupo aprova/rejeita.")
async def solicitar_entrada_grupo(grupo: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    username = user["username"]
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    if username in rbac["grupos"][grupo]["users"] or username in rbac["grupos"][grupo]["admins"]:
        raise HTTPException(status_code=409, detail="Usuário já faz parte do grupo.")
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    if "join_requests" not in rbac:
        rbac["join_requests"] = {}
    if grupo not in rbac["join_requests"]:
        rbac["join_requests"][grupo] = []
    if username in rbac["join_requests"][grupo]:
        raise HTTPException(status_code=409, detail="Solicitação já enviada.")
    rbac["join_requests"][grupo].append(username)
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Usuário '{username}' solicitou entrada no grupo '{grupo}'")
    return {"message": f"Solicitação enviada para o grupo '{grupo}'"}

# RF06: Admin lista solicitações de entrada no grupo
@router.get('/grupos/{grupo}/solicitacoes', tags=["Admin"], summary="Listar solicitações de entrada", description="Admin do grupo ou global lista solicitações de entrada no grupo.")
async def listar_solicitacoes_entrada(grupo: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user["grupos"] or user["username"] not in rbac["grupos"][grupo]["admins"]):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    join_requests = rbac.get("join_requests", {}).get(grupo, [])
    return {"solicitacoes": join_requests}

# RF06: Admin aprova solicitação de entrada
@router.post('/grupos/{grupo}/solicitacoes/{username}/aprovar', tags=["Admin"], summary="Aprovar solicitação de entrada", description="Admin do grupo ou global aprova solicitação de entrada.")
async def aprovar_solicitacao_entrada(grupo: str, username: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user["grupos"] or user["username"] not in rbac["grupos"][grupo]["admins"]):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac.get("join_requests", {}) or username not in rbac["join_requests"][grupo]:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    if username not in rbac["grupos"][grupo]["users"]:
        rbac["grupos"][grupo]["users"].append(username)
    if grupo not in rbac["usuarios"][username]["grupos"]:
        rbac["usuarios"][username]["grupos"].append(grupo)
    rbac["join_requests"][grupo].remove(username)
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Solicitação de '{username}' aprovada para grupo '{grupo}' por {user['username']}")
    return {"message": f"Usuário '{username}' adicionado ao grupo '{grupo}'"}

# RF06: Admin rejeita solicitação de entrada
@router.post('/grupos/{grupo}/solicitacoes/{username}/rejeitar', tags=["Admin"], summary="Rejeitar solicitação de entrada", description="Admin do grupo ou global rejeita solicitação de entrada.")
async def rejeitar_solicitacao_entrada(grupo: str, username: str, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin" and (grupo not in user["grupos"] or user["username"] not in rbac["grupos"][grupo]["admins"]):
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin do grupo ou global.")
    if grupo not in rbac.get("join_requests", {}) or username not in rbac["join_requests"][grupo]:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    rbac["join_requests"][grupo].remove(username)
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Solicitação de '{username}' rejeitada para grupo '{grupo}' por {user['username']}")
    return {"message": f"Solicitação de '{username}' rejeitada para grupo '{grupo}'"}

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
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username e password são obrigatórios.")
    
    if username in rbac["usuarios"]:
        raise HTTPException(status_code=409, detail="Usuário já existe.")
    
    if papel not in ["user", "admin", "global_admin"]:
        raise HTTPException(status_code=400, detail="Papel inválido. Deve ser 'user', 'admin' ou 'global_admin'.")
    
    for grupo in grupos:
        if grupo not in rbac["grupos"]:
            raise HTTPException(status_code=400, detail=f"Grupo '{grupo}' não existe.")
    
    senha_valida, resultado = validate_and_hash_password(password)
    if not senha_valida:
        if isinstance(resultado, list):
            raise HTTPException(status_code=400, detail={
                "message": "A senha não atende aos requisitos de segurança",
                "errors": resultado
            })
        else:
            raise HTTPException(status_code=400, detail=resultado)
    
    hashed_password = resultado
    
    rbac["usuarios"][username] = {
        "senha": hashed_password,
        "grupos": grupos,
        "papel": papel
    }
    
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Usuário '{username}' criado por {user['username']}")
    return {"message": f"Usuário '{username}' criado com sucesso."}

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
    
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Senha alterada com sucesso para o usuário '{username}'")
    return {"message": "Senha alterada com sucesso"}

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
async def list_user_tools(current_user=Depends(get_current_user)):
    user_tools: Dict[str, ToolResponseSchema] = {}

    if not current_user or not hasattr(current_user, 'username') or not current_user.username:
        raise HTTPException(status_code=403, detail="Usuário não identificado.")

    rbac = get_rbac_data()

    for group_name, group_details in rbac.get("grupos", {}).items():
        if current_user["username"] in group_details.get("users", []):
            for tool_name, tool_details in group_details.get("ferramentas", {}).items():
                if tool_name not in user_tools:
                    user_tools[tool_name] = ToolResponseSchema(
                        id=tool_name,
                        nome=tool_name,
                        url_base=tool_details.get("url_base", ""),
                        descricao=tool_details.get("descricao")
                    )

    return list(user_tools.values())
