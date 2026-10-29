from app.rag.citation_validator import CitationValidator
from app.rag.vector_store import ScoredChunk


def test_citation_validator_valid_and_hallucinated():
    c1 = ScoredChunk(
        chunk_id="valid_chunk_1",
        document_id="doc_1",
        document_name="architecture.pdf",
        chunk_index=0,
        page_number=2,
        content="RTO is 15 minutes for cloud services.",
        char_start=0,
        char_end=37,
        similarity_score=0.88
    )
    retrieved = [c1]

    raw_answer = (
        "The downtime objective is 15 minutes [[cite:valid_chunk_1]]. "
        "Also the company was founded in 2010 [[cite:fake_chunk_999]]."
    )

    clean_ans, verified_citations, hallucinated_count = CitationValidator.validate_and_format(
        raw_answer, retrieved
    )

    assert hallucinated_count == 1
    assert len(verified_citations) == 1
    assert verified_citations[0].chunk_id == "valid_chunk_1"
    assert verified_citations[0].document_name == "architecture.pdf"
    assert verified_citations[0].page_number == 2

    # Verify badge formatting
    assert "**[architecture.pdf, p.2]**" in clean_ans
    assert "fake_chunk_999" not in clean_ans
