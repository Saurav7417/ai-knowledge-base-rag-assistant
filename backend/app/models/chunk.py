import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base, is_sqlite
from app.core.config import settings

# If running postgresql, import Vector from pgvector; otherwise use JSON
try:
    if not is_sqlite:
        from pgvector.sqlalchemy import Vector
        EmbeddingType = Vector(settings.EMBEDDING_DIMENSION)
    else:
        EmbeddingType = JSON
except Exception:
    EmbeddingType = JSON


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    char_start = Column(Integer, default=0, nullable=False)
    char_end = Column(Integer, default=0, nullable=False)
    
    metadata_json = Column(JSON, default=dict, nullable=False)
    embedding = Column(EmbeddingType, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="chunks")
