import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.models.requests import GroupAccessRequest, RequestStatus

logger = logging.getLogger(__name__)

# Define o caminho para o arquivo de dados de solicitações
REQUESTS_FILE = Path(__file__).parent.parent.parent / 'data' / 'requests.json'

def _ensure_requests_file() -> None:
    """Garante que o arquivo de solicitações exista com estrutura válida"""
    if not REQUESTS_FILE.exists():
        with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"requests": []}, f, indent=2, ensure_ascii=False)
        logger.info(f"Arquivo de solicitações criado em {REQUESTS_FILE}")

def _load_requests() -> Dict[str, List[Dict[str, Any]]]:
    """Carrega as solicitações do arquivo JSON"""
    _ensure_requests_file()
    
    try:
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo de solicitações: {e}")
        return {"requests": []}

def _save_requests(data: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Salva as solicitações no arquivo JSON"""
    try:
        with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar solicitações: {e}")
        return False

def create_access_request(username: str, grupo: str, justificativa: str) -> GroupAccessRequest:
    """Cria uma nova solicitação de acesso a grupo"""
    data = _load_requests()
    
    # Verificar se já existe uma solicitação pendente
    for request in data["requests"]:
        if (request["username"] == username and 
            request["grupo"] == grupo and 
            request["status"] == RequestStatus.PENDING):
            logger.info(f"Solicitação já existente do usuário {username} para o grupo {grupo}")
            
            # Converter datetime string para objeto
            created_at = datetime.fromisoformat(request["created_at"])
            updated_at = datetime.fromisoformat(request["updated_at"]) if request.get("updated_at") else None
            
            return GroupAccessRequest(
                request_id=request["request_id"],
                username=request["username"],
                grupo=request["grupo"],
                status=request["status"],
                justificativa=request["justificativa"],
                created_at=created_at,
                updated_at=updated_at,
                reviewed_by=request.get("reviewed_by"),
                review_comment=request.get("review_comment")
            )
    
    # Criar nova solicitação
    request_id = str(uuid.uuid4())
    now = datetime.now()
    
    new_request = {
        "request_id": request_id,
        "username": username,
        "grupo": grupo,
        "status": RequestStatus.PENDING,
        "justificativa": justificativa,
        "created_at": now.isoformat(),
        "updated_at": None,
        "reviewed_by": None,
        "review_comment": None
    }
    
    data["requests"].append(new_request)
    _save_requests(data)
    
    logger.info(f"Solicitação {request_id} criada por {username} para o grupo {grupo}")
    
    return GroupAccessRequest(
        request_id=request_id,
        username=username,
        grupo=grupo,
        status=RequestStatus.PENDING,
        justificativa=justificativa,
        created_at=now,
        updated_at=None,
        reviewed_by=None,
        review_comment=None
    )

def get_request_by_id(request_id: str) -> Optional[GroupAccessRequest]:
    """Obtém uma solicitação pelo ID"""
    data = _load_requests()
    
    for request in data["requests"]:
        if request["request_id"] == request_id:
            # Converter datetime string para objeto
            created_at = datetime.fromisoformat(request["created_at"])
            updated_at = datetime.fromisoformat(request["updated_at"]) if request.get("updated_at") else None
            
            return GroupAccessRequest(
                request_id=request["request_id"],
                username=request["username"],
                grupo=request["grupo"],
                status=request["status"],
                justificativa=request["justificativa"],
                created_at=created_at,
                updated_at=updated_at,
                reviewed_by=request.get("reviewed_by"),
                review_comment=request.get("review_comment")
            )
    
    return None

def get_requests_by_user(username: str) -> List[GroupAccessRequest]:
    """Obtém todas as solicitações de um usuário"""
    data = _load_requests()
    user_requests = []
    
    for request in data["requests"]:
        if request["username"] == username:
            # Converter datetime string para objeto
            created_at = datetime.fromisoformat(request["created_at"])
            updated_at = datetime.fromisoformat(request["updated_at"]) if request.get("updated_at") else None
            
            user_requests.append(GroupAccessRequest(
                request_id=request["request_id"],
                username=request["username"],
                grupo=request["grupo"],
                status=request["status"],
                justificativa=request["justificativa"],
                created_at=created_at,
                updated_at=updated_at,
                reviewed_by=request.get("reviewed_by"),
                review_comment=request.get("review_comment")
            ))
    
    return user_requests

def get_pending_requests_by_admin(admin_username: str, rbac_data: Dict[str, Any]) -> List[GroupAccessRequest]:
    """Obtém solicitações pendentes para grupos onde o usuário é admin"""
    data = _load_requests()
    admin_requests = []
    
    # Determinar os grupos onde o usuário é admin
    admin_groups = []
    if rbac_data["usuarios"][admin_username]["papel"] == "global_admin":
        # Admin global pode ver todas as solicitações
        admin_groups = list(rbac_data["grupos"].keys())
    else:
        # Admin de grupo só pode ver solicitações para seus grupos
        for group_name, group_data in rbac_data["grupos"].items():
            if admin_username in group_data.get("admins", []):
                admin_groups.append(group_name)
    
    # Filtrar solicitações pendentes para grupos do admin
    for request in data["requests"]:
        if request["status"] == RequestStatus.PENDING and request["grupo"] in admin_groups:
            # Converter datetime string para objeto
            created_at = datetime.fromisoformat(request["created_at"])
            updated_at = datetime.fromisoformat(request["updated_at"]) if request.get("updated_at") else None
            
            admin_requests.append(GroupAccessRequest(
                request_id=request["request_id"],
                username=request["username"],
                grupo=request["grupo"],
                status=request["status"],
                justificativa=request["justificativa"],
                created_at=created_at,
                updated_at=updated_at,
                reviewed_by=request.get("reviewed_by"),
                review_comment=request.get("review_comment")
            ))
    
    return admin_requests

def review_access_request(request_id: str, reviewer: str, status: RequestStatus, comment: Optional[str] = None) -> Optional[GroupAccessRequest]:
    """Revisa (aprova/rejeita) uma solicitação de acesso"""
    data = _load_requests()
    
    for i, request in enumerate(data["requests"]):
        if request["request_id"] == request_id:
            # Atualizar solicitação
            now = datetime.now()
            data["requests"][i]["status"] = status
            data["requests"][i]["updated_at"] = now.isoformat()
            data["requests"][i]["reviewed_by"] = reviewer
            data["requests"][i]["review_comment"] = comment
            
            _save_requests(data)
            
            created_at = datetime.fromisoformat(request["created_at"])
            
            logger.info(f"Solicitação {request_id} {status} por {reviewer}")
            
            return GroupAccessRequest(
                request_id=request["request_id"],
                username=request["username"],
                grupo=request["grupo"],
                status=status,
                justificativa=request["justificativa"],
                created_at=created_at,
                updated_at=now,
                reviewed_by=reviewer,
                review_comment=comment
            )
    
    return None

def apply_approved_request(request_id: str, rbac_data: Dict[str, Any]) -> bool:
    """Aplica uma solicitação aprovada, adicionando o usuário ao grupo"""
    request = get_request_by_id(request_id)
    
    if not request or request.status != RequestStatus.APPROVED:
        return False
    
    # Verificar se o grupo existe
    if request.grupo not in rbac_data["grupos"]:
        logger.error(f"Grupo {request.grupo} não existe mais")
        return False
    
    # Verificar se o usuário existe
    if request.username not in rbac_data["usuarios"]:
        logger.error(f"Usuário {request.username} não existe mais")
        return False
    
    # Adicionar usuário ao grupo se ainda não estiver
    if request.username not in rbac_data["grupos"][request.grupo]["users"]:
        rbac_data["grupos"][request.grupo]["users"].append(request.username)
        
        # Atualizar os grupos do usuário
        if request.grupo not in rbac_data["usuarios"][request.username]["grupos"]:
            rbac_data["usuarios"][request.username]["grupos"].append(request.grupo)
        
        # Persistir alterações no RBAC
        try:
            rbac_path = Path(__file__).parent.parent.parent / 'data' / 'rbac.json'
            with open(rbac_path, 'w', encoding='utf-8') as f:
                json.dump(rbac_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Usuário {request.username} adicionado ao grupo {request.grupo}")
            return True
        except Exception as e:
            logger.error(f"Erro ao persistir alterações RBAC: {e}")
            return False
    
    # Usuário já está no grupo
    logger.info(f"Usuário {request.username} já pertence ao grupo {request.grupo}")
    return True
