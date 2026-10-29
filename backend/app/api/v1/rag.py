from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.models.conversation import Conversation, Message
from app.models.citation import Citation
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, CitationItem
from app.api.deps import get_current_user
from app.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/rag", tags=["RAG & Research"])


@router.post("/query", response_model=RAGQueryResponse)
def rag_query(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a single grounded research query against a knowledge base or filtered documents.
    Returns verified citations, debug scores for each retrieved candidate, and latency metrics.
    """
    # 1. Verify KB ownership
    kb = db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == request.kb_id,
            KnowledgeBase.user_id == current_user.id
        )
    ).scalar_one_or_none()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or unauthorized."
        )

    # 2. Verify document ownership if specific document_ids provided
    if request.document_ids:
        docs = db.execute(
            select(Document.id).where(
                Document.id.in_(request.document_ids),
                Document.kb_id == request.kb_id,
                Document.user_id == current_user.id
            )
        ).scalars().all()
        if len(docs) != len(request.document_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more selected documents do not belong to this knowledge base."
            )

    # 3. Execute pipeline
    pipeline = RAGPipeline(db=db)
    response = pipeline.query(
        query_text=request.query,
        user_id=current_user.id,
        kb_id=request.kb_id,
        document_ids=request.document_ids,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        rerank=request.rerank if request.rerank is not None else True
    )

    return response


@router.post("/chat", response_model=RAGQueryResponse)
def rag_chat(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a multi-turn grounded research chat interaction.
    Persists user message and assistant response with verified citations in conversation history.
    """
    # 1. Verify KB ownership
    kb = db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == request.kb_id,
            KnowledgeBase.user_id == current_user.id
        )
    ).scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")

    # 2. Resolve or create conversation
    conv = None
    if request.conversation_id:
        conv = db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id
            )
        ).scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    else:
        # Create a new conversation session
        title = request.query[:50] + ("..." if len(request.query) > 50 else "")
        conv = Conversation(
            user_id=current_user.id,
            kb_id=request.kb_id,
            title=title
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 3. Record User Message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=request.query,
        is_abstained=False,
        retrieval_debug_info={}
    )
    db.add(user_msg)
    db.commit()

    # 4. Execute RAG Query
    pipeline = RAGPipeline(db=db)
    response = pipeline.query(
        query_text=request.query,
        user_id=current_user.id,
        kb_id=request.kb_id,
        document_ids=request.document_ids,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        rerank=request.rerank if request.rerank is not None else True
    )

    # 5. Record Assistant Message
    debug_payload = {
        "retrieved_chunks": [c.model_dump() for c in response.retrieved_chunks],
        "metrics": response.metrics,
        "abstention_reason": response.abstention_reason
    }

    asst_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=response.answer,
        is_abstained=response.is_abstained,
        retrieval_debug_info=debug_payload
    )
    db.add(asst_msg)
    db.commit()
    db.refresh(asst_msg)

    # 6. Save verified citations
    for cit in response.citations:
        cit_record = Citation(
            message_id=asst_msg.id,
            chunk_id=cit.chunk_id,
            document_id=cit.document_id,
            document_name=cit.document_name,
            page_number=cit.page_number,
            excerpt=cit.excerpt,
            similarity_score=cit.similarity_score
        )
        db.add(cit_record)
    db.commit()

    response.conversation_id = conv.id
    response.message_id = asst_msg.id
    return response
