import abc
from typing import List, Optional, Dict, Any
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScoredChunk:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        document_name: str,
        chunk_index: int,
        page_number: int,
        content: str,
        char_start: int,
        char_end: int,
        similarity_score: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.document_name = document_name
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.content = content
        self.char_start = char_start
        self.char_end = char_end
        self.similarity_score = round(float(similarity_score), 4)
        self.metadata = metadata or {}


class BaseVectorStore(abc.ABC):
    def __init__(self, db: Session):
        self.db = db

    @abc.abstractmethod
    def similarity_search(
        self,
        query_vector: List[float],
        user_id: str,
        kb_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[ScoredChunk]:
        pass

    def delete_document_chunks(self, document_id: str, user_id: str) -> None:
        """Remove all chunks associated with a deleted document."""
        self.db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.user_id == user_id
            )
        )
        self.db.commit()


class SqliteVectorStore(BaseVectorStore):
    """
    In-process vector search using NumPy cosine calculation.
    Enforces tenant boundaries by filtering chunks strictly on user_id and kb_id.
    """
    def similarity_search(
        self,
        query_vector: List[float],
        user_id: str,
        kb_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[ScoredChunk]:
        query_np = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(query_np)
        if q_norm == 0:
            return []
        query_unit = query_np / q_norm

        # Filter chunks by user and knowledge base
        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                DocumentChunk.user_id == user_id,
                DocumentChunk.kb_id == kb_id
            )
        )

        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

        rows = self.db.execute(stmt).all()
        if not rows:
            return []

        scored_candidates: List[ScoredChunk] = []

        for chunk_row, doc_filename in rows:
            raw_emb = chunk_row.embedding
            if not raw_emb:
                continue

            emb_np = np.array(raw_emb, dtype=np.float32)
            c_norm = np.linalg.norm(emb_np)
            if c_norm == 0:
                continue
            
            # Cosine similarity
            cosine_sim = float(np.dot(query_unit, emb_np / c_norm))

            if cosine_sim >= min_score:
                scored_candidates.append(
                    ScoredChunk(
                        chunk_id=chunk_row.id,
                        document_id=chunk_row.document_id,
                        document_name=doc_filename,
                        chunk_index=chunk_row.chunk_index,
                        page_number=chunk_row.page_number,
                        content=chunk_row.content,
                        char_start=chunk_row.char_start,
                        char_end=chunk_row.char_end,
                        similarity_score=cosine_sim,
                        metadata=chunk_row.metadata_json or {}
                    )
                )

        # Sort descending by cosine similarity
        scored_candidates.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored_candidates[:top_k]


class PGVectorStore(BaseVectorStore):
    """
    PostgreSQL vector store using the pgvector extension and cosine distance (<=>).
    """
    def similarity_search(
        self,
        query_vector: List[float],
        user_id: str,
        kb_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[ScoredChunk]:
        # pgvector cosine distance: 1 - cosine_similarity
        # So cosine_similarity = 1 - distance
        cosine_distance = DocumentChunk.embedding.cosine_distance(query_vector)
        cosine_similarity = 1.0 - cosine_distance

        stmt = (
            select(
                DocumentChunk,
                Document.filename,
                cosine_similarity.label("similarity")
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                DocumentChunk.user_id == user_id,
                DocumentChunk.kb_id == kb_id
            )
        )

        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

        # Order by similarity descending
        stmt = stmt.order_by(cosine_similarity.desc()).limit(top_k)

        rows = self.db.execute(stmt).all()
        scored_candidates: List[ScoredChunk] = []

        for chunk_row, doc_filename, sim in rows:
            sim_val = float(sim) if sim is not None else 0.0
            if sim_val >= min_score:
                scored_candidates.append(
                    ScoredChunk(
                        chunk_id=chunk_row.id,
                        document_id=chunk_row.document_id,
                        document_name=doc_filename,
                        chunk_index=chunk_row.chunk_index,
                        page_number=chunk_row.page_number,
                        content=chunk_row.content,
                        char_start=chunk_row.char_start,
                        char_end=chunk_row.char_end,
                        similarity_score=sim_val,
                        metadata=chunk_row.metadata_json or {}
                    )
                )

        return scored_candidates


def get_vector_store(db: Session) -> BaseVectorStore:
    dialect_name = db.bind.dialect.name if db.bind else ""
    if dialect_name == "postgresql":
        try:
            return PGVectorStore(db)
        except Exception as e:
            logger.warning(f"PGVector initialization warning: {e}. Falling back to SqliteVectorStore logic.")
            return SqliteVectorStore(db)
    return SqliteVectorStore(db)
