import os
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from app.utils.text import normalize_text


class ParsedPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text


class ParsedDocument:
    def __init__(self, filename: str, pages: List[ParsedPage], total_pages: int, total_chars: int):
        self.filename = filename
        self.pages = pages
        self.total_pages = total_pages
        self.total_chars = total_chars


class DocumentParser:
    @staticmethod
    def parse_pdf(file_path: str, filename: str) -> ParsedDocument:
        pages: List[ParsedPage] = []
        total_chars = 0
        
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            if total_pages == 0:
                raise ValueError(f"PDF file '{filename}' has no pages.")
            
            for idx, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                cleaned_text = normalize_text(raw_text)
                if cleaned_text:
                    pages.append(ParsedPage(page_number=idx + 1, text=cleaned_text))
                    total_chars += len(cleaned_text)
                    
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to read or parse PDF '{filename}': {str(e)}")
            
        if total_chars == 0:
            raise ValueError(f"PDF file '{filename}' contains no extractable text. Scanned or image-only PDFs require OCR.")
            
        return ParsedDocument(filename=filename, pages=pages, total_pages=total_pages, total_chars=total_chars)

    @staticmethod
    def parse_text(file_path: str, filename: str) -> ParsedDocument:
        content = ""
        # Try UTF-8 first, fallback to latin-1
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
                
        cleaned = normalize_text(content)
        if not cleaned:
            raise ValueError(f"Text file '{filename}' is empty or contains only whitespace.")
            
        page = ParsedPage(page_number=1, text=cleaned)
        return ParsedDocument(filename=filename, pages=[page], total_pages=1, total_chars=len(cleaned))

    @classmethod
    def parse_file(cls, file_path: str, filename: str) -> ParsedDocument:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return cls.parse_pdf(file_path, filename)
        elif ext in [".txt", ".md", ".markdown"]:
            return cls.parse_text(file_path, filename)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Supported formats: .pdf, .txt, .md")
