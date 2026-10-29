from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.conversation import Conversation

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if not user_id:
        raise credentials_exception

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user


def get_user_kb(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> KnowledgeBase:
    """Ensure knowledge base exists and belongs to the authenticated user."""
    kb = db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        )
    ).scalar_one_or_none()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or access denied."
        )
    return kb


def get_user_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Document:
    """Ensure document exists and belongs to the authenticated user."""
    doc = db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )
    return doc


def get_user_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Conversation:
    """Ensure conversation exists and belongs to the authenticated user."""
    conv = db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    ).scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )
    return conv
