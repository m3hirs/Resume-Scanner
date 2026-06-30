import re
import unicodedata


def clean_text(text: str) -> str:
    """Remove noise from extracted text while preserving meaningful content."""
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\x20-\x7E\n\t]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text


def normalize_for_matching(text: str) -> str:
    """Lowercase and simplify text for skill matching purposes."""
    return clean_text(text).lower()
