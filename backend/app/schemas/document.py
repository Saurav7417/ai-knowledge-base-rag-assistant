from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: str
    kb_id: str
    user_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    processing_status: DocumentStatus
    error_message: Optional[str] = None
    total_pages: int
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    page_number: int
    char_start: int
    char_end: int
    metadata_json: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []
