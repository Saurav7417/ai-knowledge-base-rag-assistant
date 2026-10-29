import re
from typing import List, Dict, Tuple, Set
from app.rag.vector_store import ScoredChunk
from app.schemas.rag import CitationItem
from app.utils.text import extract_excerpt


class CitationValidator:
    """
    Validates, sanitizes, and maps LLM-generated citations against
    the set of retrieved ground-truth candidate chunks.
    Ensures no fabricated or non-existent chunk references reach the user.
    """
    CITATION_REGEX = re.compile(r"\[\[cite:([a-zA-Z0-9_\-]+)\]\]")

    @classmethod
    def validate_and_format(
        cls,
        raw_answer: str,
        retrieved_chunks: List[ScoredChunk]
    ) -> Tuple[str, List[CitationItem], int]:
        """
        Validates citations in raw_answer:
        - Finds all [[cite:chunk_id]] tags.
        - Verifies each chunk_id against retrieved_chunks.
        - Strips fabricated citations that do not exist in retrieved evidence.
        - Transforms valid tags into readable markdown citation badges: [DocName, p.X].
        - Returns: (cleaned_answer, verified_citations, hallucinated_count)
        """
        chunk_map: Dict[str, ScoredChunk] = {c.chunk_id: c for c in retrieved_chunks}
        found_ids = cls.CITATION_REGEX.findall(raw_answer)

        verified_citations_dict: Dict[str, CitationItem] = {}
        hallucinated_count = 0

        # Validate each citation ID
        for cid in found_ids:
            if cid in chunk_map:
                c = chunk_map[cid]
                if cid not in verified_citations_dict:
                    verified_citations_dict[cid] = CitationItem(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        document_name=c.document_name,
                        page_number=c.page_number,
                        excerpt=extract_excerpt(c.content, max_length=220),
                        similarity_score=c.similarity_score
                    )
            else:
                hallucinated_count += 1

        def replace_tag(match: re.Match) -> str:
            cid = match.group(1)
            if cid in chunk_map:
                c = chunk_map[cid]
                return f" **[{c.document_name}, p.{c.page_number}]**"
            else:
                # Strip out hallucinated chunk reference
                return ""

        formatted_answer = cls.CITATION_REGEX.sub(replace_tag, raw_answer).strip()
        # Clean up any duplicate spacing caused by stripped tags
        formatted_answer = re.sub(r" +", " ", formatted_answer)

        return formatted_answer, list(verified_citations_dict.values()), hallucinated_count
