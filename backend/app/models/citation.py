import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), nullable=False, index=True)
    document_id = Column(String(36), nullable=False, index=True)
    
    document_name = Column(String(255), nullable=False)
    page_number = Column(Integer, default=1, nullable=False)
    excerpt = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=False)

    message = relationship("Message", back_populates="citations")
