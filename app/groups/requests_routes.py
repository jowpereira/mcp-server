from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.auth import get_current_user
from app.utils.dependencies import get_rbac_data
from app.utils.request_manager import (
    create_access_request, 
    get_request_by_id, 
    get_requests_by_user,
    get_pending_requests_by_admin,
    review_access_request,
    apply_approved_request
)
from app.models.requests import (
    GroupAccessRequestCreate, 
    GroupAccessRequestResponse, 
    GroupAccessRequestReview,
    RequestStatus
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/requests",
    tags=["Solicitações"],
    responses={404: {"description": "Item não encontrado"}}
)

@router.post("/", response_model=GroupAccessRequestResponse, summary="Criar solicitação de acesso", description="Cria uma nova solicitação de acesso a um grupo")
async def create_request(request: GroupAccessRequestCreate, user=Depends(get_current_user)):
    """
    Cria uma nova solicitação de acesso a um grupo.
    Os usuários não podem solicitar acesso a grupos que já participam.
    """
    rbac = get_rbac_data()
    username = user["username"]
    grupo = request.grupo
    
    # Verificar se grupo existe
    if grupo not in rbac["grupos"]:
        logger.warning(f"Solicitação para grupo inexistente: {grupo} por {username}")
        raise HTTPException(status_code=404, detail=f"Grupo '{grupo}' não encontrado")
    
    # Verificar se usuário já pertence ao grupo
    if grupo in rbac["usuarios"][username]["grupos"]:
        logger.warning(f"Usuário {username} já pertence ao grupo {grupo}")
        raise HTTPException(status_code=400, detail=f"Você já pertence ao grupo '{grupo}'")
    
    # Criar solicitação
    access_request = create_access_request(username, grupo, request.justificativa)
    
    # Converter para modelo de resposta
    return GroupAccessRequestResponse(
        request_id=access_request.request_id,
        username=access_request.username,
        grupo=access_request.grupo,
        status=access_request.status,
        justificativa=access_request.justificativa,
        created_at=access_request.created_at,
        updated_at=access_request.updated_at,
        reviewed_by=access_request.reviewed_by,
        review_comment=access_request.review_comment
    )

@router.get("/me", response_model=List[GroupAccessRequestResponse], summary="Minhas solicitações", description="Lista todas as solicitações do usuário atual")
async def get_my_requests(user=Depends(get_current_user)):
    """
    Lista todas as solicitações de acesso feitas pelo usuário atual.
    """
    username = user["username"]
    user_requests = get_requests_by_user(username)
    
    # Converter para modelo de resposta
    return [
        GroupAccessRequestResponse(
            request_id=req.request_id,
            username=req.username,
            grupo=req.grupo,
            status=req.status,
            justificativa=req.justificativa,
            created_at=req.created_at,
            updated_at=req.updated_at,
            reviewed_by=req.reviewed_by,
            review_comment=req.review_comment
        ) for req in user_requests
    ]

@router.get("/admin", response_model=List[GroupAccessRequestResponse], summary="Solicitações pendentes", description="Lista solicitações pendentes para grupos onde o usuário é admin")
async def get_admin_requests(user=Depends(get_current_user)):
    """
    Lista todas as solicitações pendentes para grupos onde o usuário é administrador.
    Administradores globais podem ver solicitações para todos os grupos.
    """
    username = user["username"]
    rbac = get_rbac_data()
    
    # Verificar se usuário é admin (global ou de grupo)
    if user["papel"] not in ["admin", "global_admin"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    
    # Obter solicitações pendentes para os grupos do admin
    admin_requests = get_pending_requests_by_admin(username, rbac)
    
    # Converter para modelo de resposta
    return [
        GroupAccessRequestResponse(
            request_id=req.request_id,
            username=req.username,
            grupo=req.grupo,
            status=req.status,
            justificativa=req.justificativa,
            created_at=req.created_at,
            updated_at=req.updated_at,
            reviewed_by=req.reviewed_by,
            review_comment=req.review_comment
        ) for req in admin_requests
    ]

@router.get("/{request_id}", response_model=GroupAccessRequestResponse, summary="Detalhes da solicitação", description="Obtém detalhes de uma solicitação específica")
async def get_request(request_id: str, user=Depends(get_current_user)):
    """
    Obtém detalhes de uma solicitação específica.
    Usuários só podem ver suas próprias solicitações.
    Administradores podem ver solicitações dos grupos que administram.
    """
    username = user["username"]
    rbac = get_rbac_data()
    
    # Buscar solicitação
    request = get_request_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    # Verificar permissão: usuário só pode ver suas próprias solicitações
    if request.username != username:
        # A menos que seja admin do grupo ou global_admin
        if user["papel"] == "global_admin":
            pass  # Global admin pode ver qualquer solicitação
        elif user["papel"] == "admin":
            # Admin de grupo só pode ver solicitações do seu grupo
            grupo_admins = rbac["grupos"].get(request.grupo, {}).get("admins", [])
            if username not in grupo_admins:
                raise HTTPException(status_code=403, detail="Sem permissão para acessar esta solicitação")
        else:
            # Usuário comum tentando acessar solicitação de outro
            raise HTTPException(status_code=403, detail="Sem permissão para acessar esta solicitação")
    
    # Converter para modelo de resposta
    return GroupAccessRequestResponse(
        request_id=request.request_id,
        username=request.username,
        grupo=request.grupo,
        status=request.status,
        justificativa=request.justificativa,
        created_at=request.created_at,
        updated_at=request.updated_at,
        reviewed_by=request.reviewed_by,
        review_comment=request.review_comment
    )

@router.post("/{request_id}/review", response_model=GroupAccessRequestResponse, summary="Revisar solicitação", description="Aprova ou rejeita uma solicitação de acesso")
async def review_request(request_id: str, review: GroupAccessRequestReview, user=Depends(get_current_user)):
    """
    Aprova ou rejeita uma solicitação de acesso a grupo.
    Apenas admins do grupo ou admins globais podem revisar solicitações.
    """
    username = user["username"]
    rbac = get_rbac_data()
    
    # Verificar se usuário é admin (global ou de grupo)
    if user["papel"] not in ["admin", "global_admin"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    
    # Buscar solicitação
    request = get_request_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    # Verificar se solicitação já foi aprovada/rejeitada
    if request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Solicitação já foi {request.status}")
    
    # Verificar se admin tem permissão neste grupo
    if user["papel"] == "admin":
        grupo_admins = rbac["grupos"].get(request.grupo, {}).get("admins", [])
        if username not in grupo_admins:
            raise HTTPException(status_code=403, detail="Sem permissão para administrar este grupo")
    
    # Processar revisão
    updated_request = review_access_request(
        request_id=request_id,
        reviewer=username,
        status=review.status,
        comment=review.comment
    )
    
    if not updated_request:
        raise HTTPException(status_code=500, detail="Erro ao processar revisão")
    
    # Se aprovado, adicionar usuário ao grupo
    if review.status == RequestStatus.APPROVED:
        if not apply_approved_request(request_id, rbac):
            # A solicitação foi aprovada, mas houve erro ao adicionar ao grupo
            logger.error(f"Erro ao adicionar usuário {request.username} ao grupo {request.grupo}")
            raise HTTPException(
                status_code=500, 
                detail="Solicitação aprovada, mas houve erro ao adicionar usuário ao grupo"
            )
    
    # Converter para modelo de resposta
    return GroupAccessRequestResponse(
        request_id=updated_request.request_id,
        username=updated_request.username,
        grupo=updated_request.grupo,
        status=updated_request.status,
        justificativa=updated_request.justificativa,
        created_at=updated_request.created_at,
        updated_at=updated_request.updated_at,
        reviewed_by=updated_request.reviewed_by,
        review_comment=updated_request.review_comment
    )
