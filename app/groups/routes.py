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

    try:
        user = authenticate_user(username, password)
        if not user:
            logger.warning(f"Tentativa de login inválida para usuário '{username}'")
            raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
        
        token = create_jwt_for_user(username)
        logger.info(f"Usuário '{username}' autenticado com sucesso")
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException as http_exc:
        # Re-levantar HTTPExceptions para que o FastAPI as trate como de costume
        raise http_exc
    except Exception as e:
        # Capturar quaisquer outras exceções, logá-las com traceback, e retornar um erro 500 genérico
        logger.error(f"Erro inesperado durante o login para o usuário '{username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno no servidor durante o login. Verifique os logs do servidor para mais detalhes.")

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

# RF02: Criar grupo (admin global)
@router.post('/grupos', tags=["Admin"], summary="Criar grupo", description="Admin global pode criar um novo grupo.")
async def criar_grupo(data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    nome = data.get("nome")
    if not nome:
        raise HTTPException(status_code=400, detail="Nome do grupo é obrigatório.")
    if nome in rbac["grupos"]:
        raise HTTPException(status_code=409, detail="Grupo já existe.")
    rbac["grupos"][nome] = {"admins": [], "users": [], "ferramentas": []}
    # Persistência
    from pathlib import Path
    import json
    rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
    with open(rbac_path, 'w', encoding='utf-8') as f:
        json.dump(rbac, f, indent=2, ensure_ascii=False)
    logger.info(f"Grupo '{nome}' criado por {user['username']}")
    return {"message": f"Grupo '{nome}' criado com sucesso."}

# RF02: Editar grupo (admin global)
@router.put('/grupos/{grupo}', tags=["Admin"], summary="Editar grupo", description="Admin global pode editar grupo.")
async def editar_grupo(grupo: str, data: dict, user=Depends(get_current_user)):
    rbac = get_rbac_data()
    if user["papel"] != "global_admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin global.")
    if grupo not in rbac["grupos"]:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    novo_nome = data.get("nome")
    if novo_nome and novo_nome != grupo:
        if novo_nome in rbac["grupos"]:
            raise HTTPException(status_code=409, detail="Novo nome já existe.")
        rbac["grupos"][novo_nome] = rbac["grupos"].pop(grupo)
        grupo = novo_nome
    # Persistência
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
    # Persistência
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
    # Persistência
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
    # Persistência
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
    # Se não está em nenhum grupo, papel volta a user
    if not rbac["usuarios"][username]["grupos"]:
        rbac["usuarios"][username]["papel"] = "user"
    # Persistência
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
    # Persistência
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
    # Persistência simples (para produção, usar banco)
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
    # join_requests: { grupo: [usernames] }
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
    # Adiciona usuário ao grupo
    if username not in rbac["grupos"][grupo]["users"]:
        rbac["grupos"][grupo]["users"].append(username)
    if grupo not in rbac["usuarios"][username]["grupos"]:
        rbac["usuarios"][username]["grupos"].append(grupo)
    # Remove solicitação
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
