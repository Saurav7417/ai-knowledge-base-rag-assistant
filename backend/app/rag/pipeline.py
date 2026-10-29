import time
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.models.document import Document, DocumentStatus
from app.models.chunk import DocumentChunk
from app.rag.parsers import DocumentParser
from app.rag.chunker import RecursiveChunker
from app.rag.embeddings import get_embedding_provider, BaseEmbeddingProvider
from app.rag.vector_store import get_vector_store, BaseVectorStore, ScoredChunk
from app.rag.reranker import ReciprocalRankReranker
from app.rag.prompt_builder import SYSTEM_PROMPT, build_rag_prompt
from app.rag.llm import get_llm_provider, BaseLLMProvider
from app.rag.citation_validator import CitationValidator
from app.schemas.rag import RAGQueryResponse, CitationItem, RetrievedChunkDebug

logger = get_logger(__name__)


class RAGPipeline:
    def __init__(
        self,
        db: Session,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        self.db = db
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.llm_provider = llm_provider or get_llm_provider()
        self.vector_store: BaseVectorStore = get_vector_store(db)
        self.reranker = ReciprocalRankReranker()

    def ingest_document(
        self,
        document_id: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Document:
        """
        End-to-end ingestion pipeline:
        File Parsing -> Normalization -> Recursive Chunking -> Embeddings -> Vector Store Indexing.
        """
        doc = self.db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        try:
            doc.processing_status = DocumentStatus.PROCESSING
            self.db.commit()

            # 1. Parse document
            parsed_doc = DocumentParser.parse_file(doc.file_path, doc.filename)
            doc.total_pages = parsed_doc.total_pages

            # 2. Chunk document
            c_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
            c_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP
            chunker = RecursiveChunker(chunk_size=c_size, chunk_overlap=c_overlap)
            raw_chunks = chunker.chunk_document(parsed_doc)

            if not raw_chunks:
                raise ValueError(f"Document '{doc.filename}' produced 0 chunks after text extraction.")

            # 3. Generate embeddings
            chunk_texts = [c.content for c in raw_chunks]
            embeddings = self.embedding_provider.embed_documents(chunk_texts)

            # 4. Save chunks to database
            for i, c in enumerate(raw_chunks):
                chunk_record = DocumentChunk(
                    document_id=doc.id,
                    kb_id=doc.kb_id,
                    user_id=doc.user_id,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    page_number=c.page_number,
                    char_start=c.char_start,
                    char_end=c.char_end,
                    metadata_json=c.metadata,
                    embedding=embeddings[i]
                )
                self.db.add(chunk_record)

            doc.chunk_count = len(raw_chunks)
            doc.processing_status = DocumentStatus.COMPLETED
            doc.error_message = None
            self.db.commit()
            self.db.refresh(doc)
            logger.info(f"Successfully indexed document '{doc.filename}': {len(raw_chunks)} chunks, {doc.total_pages} pages.")
            return doc

        except Exception as e:
            self.db.rollback()
            logger.error(f"Ingestion failed for document '{doc.filename}': {str(e)}")
            doc.processing_status = DocumentStatus.FAILED
            doc.error_message = str(e)
            self.db.commit()
            raise

    def query(
        self,
        query_text: str,
        user_id: str,
        kb_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        rerank: bool = True
    ) -> RAGQueryResponse:
        """
        Execute grounded RAG query:
        Vector Retrieval -> Score Thresholding -> Reranking -> Grounded Synthesis -> Citation Verification.
        """
        start_total = time.time()
        k = top_k or settings.DEFAULT_TOP_K
        threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD

        # 1. Retrieval
        start_retrieval = time.time()
        query_vector = self.embedding_provider.embed_query(query_text)
        
        # Retrieve candidate chunks (retrieve slightly more if reranking is enabled)
        fetch_k = k * 2 if rerank else k
        raw_candidates = self.vector_store.similarity_search(
            query_vector=query_vector,
            user_id=user_id,
            kb_id=kb_id,
            document_ids=document_ids,
            top_k=fetch_k,
            min_score=0.0  # Retrieve all to record debug scores
        )
        retrieval_ms = round((time.time() - start_retrieval) * 1000, 2)

        # 2. Score threshold check & debug telemetry
        passed_threshold_candidates = [c for c in raw_candidates if c.similarity_score >= threshold]
        
        debug_chunks: List[RetrievedChunkDebug] = []
        for c in raw_candidates[:k]:
            debug_chunks.append(
                RetrievedChunkDebug(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    document_name=c.document_name,
                    page_number=c.page_number,
                    content=c.content,
                    similarity_score=c.similarity_score,
                    rerank_score=c.metadata.get("rerank_score"),
                    passed_threshold=(c.similarity_score >= threshold)
                )
            )

        # Abstention check: no relevant evidence found above threshold
        if not passed_threshold_candidates:
            total_ms = round((time.time() - start_total) * 1000, 2)
            return RAGQueryResponse(
                answer="The uploaded documents do not contain sufficient evidence to answer this question.",
                is_abstained=True,
                abstention_reason=f"No retrieved passages exceeded the minimum similarity threshold ({threshold}).",
                citations=[],
                retrieved_chunks=debug_chunks,
                metrics={
                    "retrieval_time_ms": retrieval_ms,
                    "generation_time_ms": 0.0,
                    "total_time_ms": total_ms,
                    "retrieved_count": len(raw_candidates),
                    "passed_threshold_count": 0,
                    "valid_citations_count": 0
                }
            )

        # 3. Optional Reranking
        if rerank and len(passed_threshold_candidates) > 1:
            reranked_chunks = self.reranker.rerank(query_text, passed_threshold_candidates, top_k=k)
            final_chunks = reranked_chunks
        else:
            final_chunks = passed_threshold_candidates[:k]

        # 4. Grounded LLM Generation
        start_generation = time.time()
        user_prompt = build_rag_prompt(query_text, final_chunks)
        raw_answer = self.llm_provider.generate(SYSTEM_PROMPT, user_prompt)
        generation_ms = round((time.time() - start_generation) * 1000, 2)

        # 5. Model-level abstention check
        if "INSUFFICIENT_EVIDENCE:" in raw_answer:
            total_ms = round((time.time() - start_total) * 1000, 2)
            abstain_msg = raw_answer.replace("INSUFFICIENT_EVIDENCE:", "").strip()
            return RAGQueryResponse(
                answer=abstain_msg,
                is_abstained=True,
                abstention_reason="LLM determined retrieved passages lacked necessary facts to support a grounded answer.",
                citations=[],
                retrieved_chunks=debug_chunks,
                metrics={
                    "retrieval_time_ms": retrieval_ms,
                    "generation_time_ms": generation_ms,
                    "total_time_ms": total_ms,
                    "retrieved_count": len(raw_candidates),
                    "passed_threshold_count": len(passed_threshold_candidates),
                    "valid_citations_count": 0
                }
            )

        # 6. Citation Validation and Formatting
        clean_answer, verified_citations, hallucinated_count = CitationValidator.validate_and_format(
            raw_answer, final_chunks
        )

        total_ms = round((time.time() - start_total) * 1000, 2)

        return RAGQueryResponse(
            answer=clean_answer,
            is_abstained=False,
            citations=verified_citations,
            retrieved_chunks=debug_chunks,
            metrics={
                "retrieval_time_ms": retrieval_ms,
                "generation_time_ms": generation_ms,
                "total_time_ms": total_ms,
                "retrieved_count": len(raw_candidates),
                "passed_threshold_count": len(passed_threshold_candidates),
                "valid_citations_count": len(verified_citations),
                "hallucinated_citations_stripped": hallucinated_count
            }
        )
