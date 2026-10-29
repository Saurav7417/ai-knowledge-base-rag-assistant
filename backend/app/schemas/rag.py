from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    excerpt: str
    similarity_score: float


class RetrievedChunkDebug(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    similarity_score: float
    rerank_score: Optional[float] = None
    passed_threshold: bool


class RAGQueryRequest(BaseModel):
    kb_id: str
    query: str = Field(..., min_length=2, max_length=2000)
    document_ids: Optional[List[str]] = Field(default=None, description="Optional filter to specific documents")
    conversation_id: Optional[str] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    rerank: Optional[bool] = True


class RAGQueryResponse(BaseModel):
    answer: str
    is_abstained: bool
    abstention_reason: Optional[str] = None
    citations: List[CitationItem] = []
    retrieved_chunks: List[RetrievedChunkDebug] = []
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    metrics: Dict[str, Any] = {}
