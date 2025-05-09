from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class GroupAccessRequest(BaseModel):
    """Modelo para solicitação de acesso a um grupo"""
    request_id: str
    username: str
    grupo: str
    status: RequestStatus = RequestStatus.PENDING
    justificativa: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_comment: Optional[str] = None

class GroupAccessRequestCreate(BaseModel):
    """Modelo para criação de solicitação de acesso"""
    grupo: str
    justificativa: str = Field(..., min_length=5, max_length=500)

class GroupAccessRequestReview(BaseModel):
    """Modelo para revisão de solicitação de acesso"""
    status: RequestStatus
    comment: Optional[str] = Field(None, max_length=500)

class GroupAccessRequestResponse(BaseModel):
    """Modelo para resposta da API de solicitações de acesso"""
    request_id: str
    username: str
    grupo: str
    status: RequestStatus
    justificativa: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_comment: Optional[str] = None
