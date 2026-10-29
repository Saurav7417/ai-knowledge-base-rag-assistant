from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
