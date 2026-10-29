import pytest
from app.rag.chunker import RecursiveChunker, Chunk
from app.rag.parsers import ParsedDocument, ParsedPage


def test_chunker_invalid_overlap():
    with pytest.raises(ValueError, match="chunk_overlap .* must be strictly less than chunk_size"):
        RecursiveChunker(chunk_size=100, chunk_overlap=100)


def test_chunker_basic_splitting():
    text = (
        "Paragraph 1 contains some introductory details about the cloud infrastructure.\n\n"
        "Paragraph 2 discusses database clustering and consensus mechanics.\n\n"
        "Paragraph 3 covers cybersecurity audit and compliance guidelines."
    )
    page = ParsedPage(page_number=1, text=text)
    doc = ParsedDocument(filename="test.md", pages=[page], total_pages=1, total_chars=len(text))

    chunker = RecursiveChunker(chunk_size=120, chunk_overlap=20)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 3
    for c in chunks:
        assert len(c.content) <= 150  # respects size budget
        assert c.page_number == 1
        assert c.char_end > c.char_start
        assert c.metadata["filename"] == "test.md"


def test_chunker_preserves_page_numbers():
    p1 = ParsedPage(page_number=1, text="Page 1 content about microservices.")
    p2 = ParsedPage(page_number=2, text="Page 2 content regarding Kubernetes ingress.")
    doc = ParsedDocument(filename="multipage.pdf", pages=[p1, p2], total_pages=2, total_chars=70)

    chunker = RecursiveChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert "microservices" in chunks[0].content
    assert chunks[1].page_number == 2
    assert "Kubernetes" in chunks[1].content
