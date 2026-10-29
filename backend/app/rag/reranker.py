import re
from typing import List
from app.rag.vector_store import ScoredChunk


class BaseReranker:
    def rerank(self, query: str, chunks: List[ScoredChunk], top_k: int) -> List[ScoredChunk]:
        raise NotImplementedError


class ReciprocalRankReranker(BaseReranker):
    """
    Hybrid semantic-lexical reranker. Combines vector cosine similarity
    with BM25-style keyword density and exact query phrase matches to optimize
    precision for technical and domain-specific terminology.
    """
    def __init__(self, semantic_weight: float = 0.65):
        self.semantic_weight = semantic_weight
        self.lexical_weight = 1.0 - semantic_weight

    def _compute_lexical_score(self, query: str, content: str) -> float:
        query_words = set(re.findall(r"\w+", query.lower()))
        if not query_words:
            return 0.0

        content_lower = content.lower()
        content_words = re.findall(r"\w+", content_lower)
        if not content_words:
            return 0.0

        # Term frequency overlap
        matched_words = 0
        for w in query_words:
            if w in content_lower:
                matched_words += 1

        term_overlap = matched_words / len(query_words)

        # Bonus for exact phrase match
        phrase_bonus = 0.3 if query.lower().strip() in content_lower else 0.0

        score = (term_overlap * 0.7) + phrase_bonus
        return min(score, 1.0)

    def rerank(self, query: str, chunks: List[ScoredChunk], top_k: int) -> List[ScoredChunk]:
        if not chunks:
            return []

        scored_list = []
        for chunk in chunks:
            lexical_score = self._compute_lexical_score(query, chunk.content)
            # Combine semantic similarity and lexical score
            hybrid_score = (self.semantic_weight * chunk.similarity_score) + (self.lexical_weight * lexical_score)
            
            # Store rerank score on the chunk
            chunk.metadata["rerank_score"] = round(hybrid_score, 4)
            scored_list.append((hybrid_score, chunk))

        # Sort descending by hybrid score
        scored_list.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_list[:top_k]]
