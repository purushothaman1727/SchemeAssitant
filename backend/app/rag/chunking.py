import re
import unicodedata
from dataclasses import dataclass

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_PAGE_MARK = re.compile(r"\bPage\s+\d+\s+of\s+\d+\b", re.IGNORECASE)
_TOC = re.compile(
    r"(sl\.?\s*no\.?.{0,60}(topics|contents?|page no)|table of contents|^\s*contents?\b)",
    re.IGNORECASE | re.DOTALL,
)
_SENTENCE_END = re.compile(r"(?<=[.!?;:।])\s+")


def clean_text(text: str) -> str:
    """Normalise extracted text: unicode NFC, drop control chars, unwrap hard line breaks."""
    text = unicodedata.normalize("NFC", text)
    text = _CTRL.sub(" ", text)
    text = text.replace("\r", "\n")
    text = _PAGE_MARK.sub(" ", text)  # running page headers add noise to every chunk
    text = re.sub(r"-\n(?=[a-z])", "", text)  # hyphenated line wraps
    text = re.sub(r"\n{2,}", "\n\n", text)
    paras = [re.sub(r"\s+", " ", p).strip() for p in text.split("\n\n")]
    return "\n\n".join(p for p in paras if p)


def is_boilerplate(text: str) -> bool:
    """Tables of contents / index listings: lots of headings and page numbers, no content."""
    if _TOC.search(text[:300]):
        return True
    digits = sum(c.isdigit() for c in text)
    return len(text) > 200 and digits / len(text) > 0.3 and "page no" in text.lower()


@dataclass
class Chunk:
    text: str
    page: int | None
    index: int


def _hard_split(s: str, size: int) -> list[str]:
    return [s[i : i + size] for i in range(0, len(s), size)]


def split_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Sentence-aware greedy chunking with character overlap."""
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("require chunk_size > 0 and 0 <= overlap < chunk_size")
    units: list[str] = []
    for para in text.split("\n\n"):
        for sent in _SENTENCE_END.split(para):
            sent = sent.strip()
            if not sent:
                continue
            units.extend(_hard_split(sent, chunk_size) if len(sent) > chunk_size else [sent])

    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for u in units:
        if current and length + len(u) + 1 > chunk_size:
            chunks.append(" ".join(current))
            # carry trailing units as overlap
            carried: list[str] = []
            size = 0
            for prev in reversed(current):
                if size + len(prev) > overlap:
                    break
                carried.insert(0, prev)
                size += len(prev) + 1
            current, length = carried, size
        current.append(u)
        length += len(u) + 1
    if current:
        tail = " ".join(current)
        if not chunks or tail != chunks[-1]:
            chunks.append(tail)
    return chunks


def chunk_pages(pages: list[tuple[int | None, str]], chunk_size: int, overlap: int) -> list[Chunk]:
    """Chunks never span pages, so every chunk keeps an exact page number."""
    out: list[Chunk] = []
    for page, raw in pages:
        cleaned = clean_text(raw)
        if len(cleaned) < 20:
            continue
        for piece in split_text(cleaned, chunk_size, overlap):
            out.append(Chunk(text=piece, page=page, index=len(out)))
    return out
