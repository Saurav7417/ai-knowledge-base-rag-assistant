import logging
import re
import sys
from typing import Any

# Patterns to mask in logs
SENSITIVE_PATTERNS = [
    (re.compile(r'("?(?:password|token|secret|access_token|authorization|api_key)"?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1***MASKED***\3'),
    (re.compile(r'(sk-[a-zA-Z0-9]{20,})', re.IGNORECASE), r'sk-***MASKED***'),
    (re.compile(r'(Bearer\s+)[a-zA-Z0-9_\-\.]+', re.IGNORECASE), r'\1***MASKED***'),
]


class SafeFormatter(logging.Formatter):
    """Custom formatter that automatically scrubs sensitive credentials from log outputs."""
    def format(self, record: logging.LogRecord) -> str:
        orig = super().format(record)
        sanitized = orig
        for pattern, replacement in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            SafeFormatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(handler)
        logger.propagate = False
    return logger
