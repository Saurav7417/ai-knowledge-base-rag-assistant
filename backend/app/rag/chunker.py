import re
from typing import List, Dict, Any, Optional
from app.rag.parsers import ParsedDocument, ParsedPage


class Chunk:
    def __init__(
        self,
        chunk_index: int,
        content: str,
        page_number: int,
        char_start: int,
        char_end: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.chunk_index = chunk_index
        self.content = content
        self.page_number = page_number
        self.char_start = char_start
        self.char_end = char_end
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "content": self.content,
            "page_number": self.page_number,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "metadata": self.metadata
        }


class RecursiveChunker:
    """
    Hierarchical text chunker that splits on paragraphs, sentences, and words
    while preserving page numbers, character offsets, and semantic integrity.
    """
    def __init__(
        self,
        chunk_size: int = 600,
        chunk_overlap: int = 120,
        separators: Optional[List[str]] = None
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using the given list of separators."""
        final_chunks: List[str] = []
        separator = separators[-1]
        new_separators: List[str] = []
        
        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator != "" else list(text)

        good_splits: List[str] = []
        for s in splits:
            if separator != "" and s != "":
                piece = s + separator
            else:
                piece = s
            if piece:
                good_splits.append(piece)

        # Merge splits up to chunk_size
        accumulated = ""
        for piece in good_splits:
            if len(piece) > self.chunk_size:
                # If accumulated has text, commit it first
                if accumulated:
                    final_chunks.append(accumulated.strip())
                    accumulated = ""
                if new_separators:
                    sub_chunks = self._split_text(piece, new_separators)
                    final_chunks.extend(sub_chunks)
                else:
                    # Hard slice if no more separators
                    for i in range(0, len(piece), self.chunk_size - self.chunk_overlap):
                        final_chunks.append(piece[i:i + self.chunk_size].strip())
            elif len(accumulated) + len(piece) <= self.chunk_size:
                accumulated += piece
            else:
                if accumulated:
                    final_chunks.append(accumulated.strip())
                # Start new chunk with overlap if applicable
                overlap_text = accumulated[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                accumulated = (overlap_text + piece).strip()

        if accumulated.strip():
            final_chunks.append(accumulated.strip())

        return [c for c in final_chunks if c]

    def chunk_document(self, parsed_doc: ParsedDocument) -> List[Chunk]:
        """
        Chunks an entire ParsedDocument while preserving page boundaries and
        calculating continuous character offsets.
        """
        all_chunks: List[Chunk] = []
        global_chunk_idx = 0

        for page in parsed_doc.pages:
            page_text = page.text
            if not page_text:
                continue

            page_splits = self._split_text(page_text, self.separators)
            
            # Map character start and end offsets inside the page
            current_search_pos = 0
            for text_chunk in page_splits:
                if not text_chunk:
                    continue

                # Find chunk within page
                char_start = page_text.find(text_chunk[:30], current_search_pos)
                if char_start == -1:
                    char_start = current_search_pos
                char_end = char_start + len(text_chunk)
                current_search_pos = max(char_start + 1, current_search_pos)

                chunk = Chunk(
                    chunk_index=global_chunk_idx,
                    content=text_chunk,
                    page_number=page.page_number,
                    char_start=char_start,
                    char_end=char_end,
                    metadata={
                        "filename": parsed_doc.filename,
                        "page_number": page.page_number,
                        "length_chars": len(text_chunk)
                    }
                )
                all_chunks.append(chunk)
                global_chunk_idx += 1

        return all_chunks
