import unicodedata
import re


def normalize_text(text: str) -> str:
    """
    Normalize text content:
    - Normalize Unicode into NFKC form
    - Standardize CRLF/CR to LF
    - Replace non-standard whitespace characters with regular spaces
    - Remove NULL bytes and non-printable control characters (except newline, tab)
    - Collapse excessive consecutive newlines (3+ into 2)
    """
    if not text:
        return ""
    
    # Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)
    
    # Convert carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Strip null characters and control characters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    
    # Normalize tabs to 4 spaces
    text = text.replace("\t", "    ")
    
    # Collapse multiple trailing spaces on lines
    text = re.sub(r"[ ]+\n", "\n", text)
    
    # Collapse 3+ newlines to 2 newlines (preserve paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


def extract_excerpt(text: str, max_length: int = 220) -> str:
    """Extract a clean, concise excerpt without cutting off mid-word."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_length:
        return cleaned
    
    truncated = cleaned[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."
