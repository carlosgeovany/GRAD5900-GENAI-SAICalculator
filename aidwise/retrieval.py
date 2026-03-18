from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from aidwise.models import RetrievedPassage

TOKEN_PATTERN = re.compile(r"[a-z0-9']+")


@dataclass(slots=True)
class DocumentChunk:
    source: str
    text: str


class SimpleRetriever:
    """A lightweight keyword retriever that keeps the first version grounded."""

    def __init__(self, document_dir: str | Path = "data/policy", chunk_size: int = 900):
        self.document_dir = Path(document_dir)
        self.chunk_size = chunk_size
        self._chunks: list[DocumentChunk] = []

    def load(self) -> None:
        self._chunks = []
        if not self.document_dir.exists():
            return

        for path in sorted(self.document_dir.iterdir()):
            if path.suffix.lower() in {".txt", ".md"}:
                self._chunks.extend(self._chunk_text(path.name, path.read_text(encoding="utf-8")))
            elif path.suffix.lower() == ".pdf":
                pdf_text = self._extract_pdf_text(path)
                if pdf_text:
                    self._chunks.extend(self._chunk_text(path.name, pdf_text))

    def search(self, query: str, limit: int = 3) -> list[RetrievedPassage]:
        if not self._chunks:
            self.load()
        if not self._chunks:
            return []

        query_tokens = set(self._tokenize(query))
        scored: list[RetrievedPassage] = []
        for chunk in self._chunks:
            chunk_tokens = self._tokenize(chunk.text)
            if not chunk_tokens:
                continue
            overlap = query_tokens.intersection(chunk_tokens)
            score = len(overlap) / len(set(chunk_tokens))
            if score > 0:
                scored.append(
                    RetrievedPassage(
                        source=chunk.source,
                        text=chunk.text.strip(),
                        score=round(score, 4),
                    )
                )
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def available_sources(self) -> list[str]:
        if not self._chunks:
            self.load()
        return sorted({chunk.source for chunk in self._chunks})

    def _chunk_text(self, source: str, text: str) -> list[DocumentChunk]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []

        chunks: list[DocumentChunk] = []
        start = 0
        while start < len(normalized):
            end = min(start + self.chunk_size, len(normalized))
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(DocumentChunk(source=source, text=chunk))
            start = end
        return chunks

    @staticmethod
    def _extract_pdf_text(path: Path) -> str:
        try:
            import fitz
        except ImportError:
            return ""

        text_parts: list[str] = []
        with fitz.open(path) as pdf:
            for page in pdf:
                text_parts.append(page.get_text())
        return "\n".join(text_parts)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return TOKEN_PATTERN.findall(text.lower())
