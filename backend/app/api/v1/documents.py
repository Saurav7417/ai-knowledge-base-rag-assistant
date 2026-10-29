import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document, DocumentStatus
from app.models.chunk import DocumentChunk
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentChunkResponse
from app.api.deps import get_current_user, get_user_document
from app.rag.pipeline import RAGPipeline

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, TXT, Markdown), validate type & size,
    extract text, generate chunks, compute embeddings, and index into vector store.
    """
    # 1. Verify KB ownership
    kb = db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        )
    ).scalar_one_or_none()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or unauthorized."
        )

    # 2. Validate file extension
    orig_filename = os.path.basename(file.filename or "uploaded_file")
    ext = os.path.splitext(orig_filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 3. Read content and validate file size
    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES / (1024 * 1024):.1f}MB"
        )
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # 4. Save file to disk
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, current_user.id)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex[:8]}_{orig_filename}"
    file_path = os.path.join(user_upload_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 5. Create Document record in DB
    doc = Document(
        kb_id=kb.id,
        user_id=current_user.id,
        filename=orig_filename,
        file_type=ext.replace(".", ""),
        file_size_bytes=file_size,
        file_path=file_path,
        processing_status=DocumentStatus.PENDING
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Execute RAG Ingestion Pipeline
    try:
        pipeline = RAGPipeline(db=db)
        doc = pipeline.ingest_document(doc.id)
    except Exception as e:
        logger.error(f"Failed to ingest document '{orig_filename}': {e}")
        # Return document record with FAILED status and error message
        db.refresh(doc)

    return doc


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    kb_id: str = Query(..., description="Filter documents by knowledge base ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents in a knowledge base with their status and chunk counts."""
    # Verify KB ownership
    kb = db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        )
    ).scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")

    docs = db.execute(
        select(Document)
        .where(Document.kb_id == kb_id, Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    ).scalars().all()

    return docs


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    doc: Document = Depends(get_user_document),
    db: Session = Depends(get_db)
):
    """Get document details along with its indexed chunks."""
    chunks = db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc.id)
        .order_by(DocumentChunk.chunk_index.asc())
    ).scalars().all()

    chunk_responses = [
        DocumentChunkResponse(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            content=c.content,
            page_number=c.page_number,
            char_start=c.char_start,
            char_end=c.char_end,
            metadata_json=c.metadata_json or {}
        )
        for c in chunks
    ]

    return DocumentDetailResponse(
        id=doc.id,
        kb_id=doc.kb_id,
        user_id=doc.user_id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size_bytes=doc.file_size_bytes,
        processing_status=doc.processing_status,
        error_message=doc.error_message,
        total_pages=doc.total_pages,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks=chunk_responses
    )


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(
    doc: Document = Depends(get_user_document),
    db: Session = Depends(get_db)
):
    """Inspect all chunks extracted from a specific document for debugging."""
    chunks = db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc.id)
        .order_by(DocumentChunk.chunk_index.asc())
    ).scalars().all()

    return [
        DocumentChunkResponse(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            content=c.content,
            page_number=c.page_number,
            char_start=c.char_start,
            char_end=c.char_end,
            metadata_json=c.metadata_json or {}
        )
        for c in chunks
    ]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc: Document = Depends(get_user_document),
    db: Session = Depends(get_db)
):
    """
    Delete a document, cascade delete its chunks from the database/vector store,
    and remove the stored file on disk.
    """
    # 1. Delete physical file if present
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file on disk {doc.file_path}: {e}")

    # 2. Delete document record (DocumentChunk rows cascade deleted via foreign key)
    db.delete(doc)
    db.commit()
    return None
