import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kb_id = Column(String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, txt, md
    file_size_bytes = Column(Integer, nullable=False)
    file_path = Column(String(512), nullable=False)
    
    processing_status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    total_pages = Column(Integer, default=1, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
