from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from app.api.deps import get_current_user, get_user_kb

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.post("/", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    kb_in: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new private knowledge base."""
    kb = KnowledgeBase(
        user_id=current_user.id,
        name=kb_in.name.strip(),
        description=kb_in.description.strip() if kb_in.description else None
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return KnowledgeBaseResponse(
        id=kb.id,
        user_id=kb.user_id,
        name=kb.name,
        description=kb.description,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
        document_count=0
    )


@router.get("/", response_model=List[KnowledgeBaseResponse])
def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all knowledge bases owned by the current user."""
    # Subquery for document count per KB
    doc_counts = (
        select(Document.kb_id, func.count(Document.id).label("doc_count"))
        .where(Document.user_id == current_user.id)
        .group_by(Document.kb_id)
        .subquery()
    )

    kbs = db.execute(
        select(KnowledgeBase, func.coalesce(doc_counts.c.doc_count, 0))
        .outerjoin(doc_counts, KnowledgeBase.id == doc_counts.c.kb_id)
        .where(KnowledgeBase.user_id == current_user.id)
        .order_by(KnowledgeBase.created_at.desc())
    ).all()

    results = []
    for kb, count in kbs:
        results.append(
            KnowledgeBaseResponse(
                id=kb.id,
                user_id=kb.user_id,
                name=kb.name,
                description=kb.description,
                created_at=kb.created_at,
                updated_at=kb.updated_at,
                document_count=count
            )
        )
    return results


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    kb: KnowledgeBase = Depends(get_user_kb),
    db: Session = Depends(get_db)
):
    """Get details of a specific knowledge base."""
    doc_count = db.execute(
        select(func.count(Document.id)).where(Document.kb_id == kb.id)
    ).scalar_one()

    return KnowledgeBaseResponse(
        id=kb.id,
        user_id=kb.user_id,
        name=kb.name,
        description=kb.description,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
        document_count=doc_count
    )


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
    kb_in: KnowledgeBaseUpdate,
    kb: KnowledgeBase = Depends(get_user_kb),
    db: Session = Depends(get_db)
):
    """Rename or update description of a knowledge base."""
    if kb_in.name is not None:
        kb.name = kb_in.name.strip()
    if kb_in.description is not None:
        kb.description = kb_in.description.strip()
    db.commit()
    db.refresh(kb)

    doc_count = db.execute(
        select(func.count(Document.id)).where(Document.kb_id == kb.id)
    ).scalar_one()

    return KnowledgeBaseResponse(
        id=kb.id,
        user_id=kb.user_id,
        name=kb.name,
        description=kb.description,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
        document_count=doc_count
    )


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    kb: KnowledgeBase = Depends(get_user_kb),
    db: Session = Depends(get_db)
):
    """Delete a knowledge base and cascade all documents, chunks, and conversations."""
    db.delete(kb)
    db.commit()
    return None
