import re
from collections import Counter
from pathlib import Path
import pdfplumber
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9']+")


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".pdf":
        with pdfplumber.open(path) as pdf:
            pages = [(page.extract_text() or "") for page in pdf.pages]
        return "\n".join(pages).strip()
    raise ValueError("Only PDF and TXT files are supported")


def normalize_text(text: str) -> str:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    return " ".join(token for token in tokens if token not in ENGLISH_STOP_WORDS and len(token) > 1)


def tokenize(text: str) -> list[str]:
    return normalize_text(text).split()


def word_count(text: str) -> int:
    return len(TOKEN_PATTERN.findall(text))


def vocabulary_richness(text: str) -> float:
    tokens = tokenize(text)
    return round((len(set(tokens)) / len(tokens)) * 100, 2) if tokens else 0.0


def matching_phrases(left: str, right: str, phrase_length: int = 5, limit: int = 5) -> list[str]:
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)
    right_ngrams = {" ".join(right_tokens[i:i + phrase_length]) for i in range(max(0, len(right_tokens) - phrase_length + 1))}
    seen: list[str] = []
    for i in range(max(0, len(left_tokens) - phrase_length + 1)):
        phrase = " ".join(left_tokens[i:i + phrase_length])
        if phrase in right_ngrams and phrase not in seen:
            seen.append(phrase)
    return seen[:limit]
