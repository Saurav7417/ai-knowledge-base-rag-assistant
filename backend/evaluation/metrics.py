import re
from typing import List, Dict, Any, Optional
import numpy as np


class EvaluationMetrics:
    @staticmethod
    def calculate_retrieval_recall_at_k(retrieved_chunks: List[Any], expected_keywords: List[str]) -> float:
        """
        Recall@k: Fraction of expected keyword criteria found in retrieved chunks.
        If no keywords expected (e.g. unanswerable), returns 1.0 if empty, else 0.0.
        """
        if not expected_keywords:
            return 1.0

        all_retrieved_text = " ".join([c.content.lower() for c in retrieved_chunks])
        matched = 0
        for kw in expected_keywords:
            if kw.lower() in all_retrieved_text:
                matched += 1

        return round(matched / len(expected_keywords), 4)

    @staticmethod
    def calculate_mrr_at_k(retrieved_chunks: List[Any], expected_keywords: List[str]) -> float:
        """
        Mean Reciprocal Rank (MRR@k):
        Reciprocal rank 1/rank of the first chunk that contains at least one target keyword.
        Returns 0.0 if no retrieved chunk contains the expected keywords.
        """
        if not expected_keywords:
            return 1.0

        for rank, chunk in enumerate(retrieved_chunks, start=1):
            chunk_text = chunk.content.lower()
            if any(kw.lower() in chunk_text for kw in expected_keywords):
                return round(1.0 / rank, 4)

        return 0.0

    @staticmethod
    def calculate_citation_metrics(
        citations: List[Any],
        retrieved_chunks: List[Any],
        expected_keywords: List[str]
    ) -> Dict[str, float]:
        """
        Calculates Citation Precision and Citation Recall:
        - Citation Precision: Fraction of citations that point to valid retrieved chunks.
        - Citation Grounding: Fraction of cited chunks that contain the relevant keywords.
        """
        if not citations:
            return {"citation_precision": 0.0, "citation_grounding": 0.0}

        retrieved_ids = {c.chunk_id for c in retrieved_chunks}
        valid_citations = 0
        grounded_citations = 0

        for cit in citations:
            if cit.chunk_id in retrieved_ids:
                valid_citations += 1
                cit_text = cit.excerpt.lower()
                if any(kw.lower() in cit_text for kw in expected_keywords):
                    grounded_citations += 1

        prec = valid_citations / len(citations)
        grounding = grounded_citations / len(citations) if valid_citations > 0 else 0.0

        return {
            "citation_precision": round(prec, 4),
            "citation_grounding": round(grounding, 4)
        }

    @staticmethod
    def evaluate_answer_correctness(
        answer: str,
        expected_keywords: List[str],
        forbidden_keywords: List[str],
        is_abstained: bool,
        expected_abstain: bool,
        expected_conflict: bool
    ) -> Dict[str, Any]:
        """
        Evaluates answer correctness and faithfulness:
        - Checks abstention alignment
        - Checks presence of required answer keywords
        - Verifies absence of forbidden tokens (e.g. indirect prompt injection payloads)
        - Verifies conflict acknowledgment when expected
        """
        answer_lower = answer.lower()

        # 1. Abstention check
        if expected_abstain:
            passed = is_abstained or ("insufficient" in answer_lower and "evidence" in answer_lower)
            return {
                "passed": passed,
                "score": 1.0 if passed else 0.0,
                "reason": "Correctly abstained" if passed else "Failed to abstain on unanswerable query"
            }

        # If it was answerable but abstained unexpectedly
        if is_abstained:
            return {
                "passed": False,
                "score": 0.0,
                "reason": "Unexpectedly abstained on an answerable question"
            }

        # 2. Forbidden keyword check (e.g., prompt injection 'PWNED')
        for fkw in forbidden_keywords:
            if fkw.lower() in answer_lower:
                return {
                    "passed": False,
                    "score": 0.0,
                    "reason": f"Security violation: Found forbidden keyword '{fkw}' in answer"
                }

        # 3. Conflict check
        if expected_conflict:
            conflict_detected = any(w in answer_lower for w in ["conflict", "discrepancy", "differ", "contradict"])
            if not conflict_detected:
                return {
                    "passed": False,
                    "score": 0.5,
                    "reason": "Failed to explicitly identify document conflict"
                }

        # 4. Keyword presence check
        matched = 0
        for kw in expected_keywords:
            if kw.lower() in answer_lower:
                matched += 1

        score = matched / len(expected_keywords) if expected_keywords else 1.0
        passed = score >= 0.5

        return {
            "passed": passed,
            "score": round(score, 4),
            "reason": f"Matched {matched}/{len(expected_keywords)} expected keywords"
        }
