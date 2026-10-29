from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.citation import Citation
from app.schemas.conversation import ConversationResponse, MessageResponse, CreateConversationRequest
from app.schemas.rag import CitationItem
from app.api.deps import get_current_user, get_user_conversation, get_user_kb

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new research conversation session."""
    conv = Conversation(
        user_id=current_user.id,
        kb_id=conv_in.kb_id,
        title=conv_in.title or "New Research Session"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    return ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        kb_id=conv.kb_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[]
    )


@router.get("/", response_model=List[ConversationResponse])
def list_conversations(
    kb_id: str = Query(..., description="Knowledge base ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all conversation sessions within a knowledge base."""
    convs = db.execute(
        select(Conversation)
        .where(
            Conversation.kb_id == kb_id,
            Conversation.user_id == current_user.id
        )
        .order_by(Conversation.updated_at.desc())
    ).scalars().all()

    return [
        ConversationResponse(
            id=c.id,
            user_id=c.user_id,
            kb_id=c.kb_id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            messages=[]
        )
        for c in convs
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conv: Conversation = Depends(get_user_conversation),
    db: Session = Depends(get_db)
):
    """Retrieve full conversation message history, verified citations, and retrieval debug logs."""
    messages = db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    ).scalars().all()

    message_responses = []
    for m in messages:
        citations = db.execute(
            select(Citation).where(Citation.message_id == m.id)
        ).scalars().all()

        citation_items = [
            CitationItem(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                document_name=c.document_name,
                page_number=c.page_number,
                excerpt=c.excerpt,
                similarity_score=c.similarity_score
            )
            for c in citations
        ]

        message_responses.append(
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                is_abstained=m.is_abstained,
                citations=citation_items,
                retrieval_debug_info=m.retrieval_debug_info or {},
                created_at=m.created_at
            )
        )

    return ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        kb_id=conv.kb_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=message_responses
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conv: Conversation = Depends(get_user_conversation),
    db: Session = Depends(get_db)
):
    """Delete a conversation session and all associated messages and citations."""
    db.delete(conv)
    db.commit()
    return None
