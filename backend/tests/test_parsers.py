import os
import tempfile
import pytest
from app.rag.parsers import DocumentParser


def test_parse_text_file():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Line 1 with text.\r\nLine 2 with \t tabs and extra spaces.   \n\n\nLine 3.")
        temp_path = f.name

    try:
        parsed = DocumentParser.parse_file(temp_path, "sample.txt")
        assert parsed.total_pages == 1
        assert len(parsed.pages) == 1
        # Check text normalization
        assert "\r" not in parsed.pages[0].text
        assert "\n\n\n" not in parsed.pages[0].text
        assert "Line 1 with text." in parsed.pages[0].text
    finally:
        os.remove(temp_path)


def test_parse_empty_file_raises():
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("    \n\n  ")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="empty or contains only whitespace"):
            DocumentParser.parse_file(temp_path, "empty.md")
    finally:
        os.remove(temp_path)


def test_unsupported_file_format():
    with pytest.raises(ValueError, match="Unsupported file format"):
        DocumentParser.parse_file("malicious.exe", "malicious.exe")
