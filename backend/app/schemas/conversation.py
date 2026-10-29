from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.rag import CitationItem


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    is_abstained: bool
    citations: List[CitationItem] = []
    retrieval_debug_info: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    kb_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CreateConversationRequest(BaseModel):
    kb_id: str
    title: Optional[str] = "New Research Session"
