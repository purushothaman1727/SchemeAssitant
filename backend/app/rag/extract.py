"""Text extraction from untrusted PDF/HTML bytes. Nothing here executes document content."""
import re
from dataclasses import dataclass

MAX_PDF_PAGES = 500

# Phrases that try to instruct a model. Content is data, never instructions; matching
# chunks are flagged and excluded from retrieval.
_INJECTION = re.compile(
    r"(ignore (all |any )?(previous|prior|above) (instructions|prompts)|"
    r"disregard (the )?(system|previous) (prompt|instructions)|"
    r"you are now|system prompt|act as (an? )?(?!student)|"
    r"reveal (your|the) (prompt|instructions)|"
    r"<\s*/?\s*(script|iframe)\b)",
    re.IGNORECASE,
)


class ExtractionError(Exception):
    pass


@dataclass
class ExtractedDocument:
    pages: list[tuple[int | None, str]]
    page_count: int | None


def looks_like_injection(text: str) -> bool:
    return bool(_INJECTION.search(text))


def extract_pdf(data: bytes) -> ExtractedDocument:
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:  # corrupt / not a PDF
        raise ExtractionError(f"cannot open PDF: {exc}") from exc
    if doc.needs_pass:
        raise ExtractionError("PDF is password protected")
    if len(doc) > MAX_PDF_PAGES:
        raise ExtractionError(f"PDF has {len(doc)} pages (limit {MAX_PDF_PAGES})")
    pages = [(i, page.get_text()) for i, page in enumerate(doc, start=1)]
    if not any(t.strip() for _, t in pages):
        raise ExtractionError("PDF has no extractable text (scanned image?)")
    return ExtractedDocument(pages=pages, page_count=len(doc))


def extract_html(data: bytes) -> ExtractedDocument:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(data, "lxml")
    for tag in soup(["script", "style", "noscript", "iframe", "nav", "footer", "form", "svg"]):
        tag.decompose()
    for tag in soup.find_all(attrs={"hidden": True}):
        tag.decompose()
    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none", re.I)):
        tag.decompose()
    text = soup.get_text("\n")
    if len(text.strip()) < 40:
        raise ExtractionError("page has no extractable text (client-side rendered?)")
    return ExtractedDocument(pages=[(None, text)], page_count=None)


def extract_text(data: bytes) -> ExtractedDocument:
    return ExtractedDocument(pages=[(None, data.decode("utf-8", errors="replace"))], page_count=None)


def extract(data: bytes, kind: str) -> ExtractedDocument:
    if kind == "pdf":
        return extract_pdf(data)
    if kind == "html":
        return extract_html(data)
    if kind == "text":
        return extract_text(data)
    raise ExtractionError(f"unsupported document type: {kind}")


def detect_kind(data: bytes, content_type: str | None, url: str | None = None) -> str:
    if data[:5] == b"%PDF-":
        return "pdf"
    ct = (content_type or "").lower()
    if "html" in ct or (url or "").lower().endswith((".html", ".htm")) or data[:200].lstrip().lower().startswith((b"<!doctype html", b"<html")):
        return "html"
    if ct.startswith("text/"):
        return "text"
    raise ExtractionError(f"unsupported content type: {content_type or 'unknown'}")
