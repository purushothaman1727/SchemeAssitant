import hashlib
import ipaddress
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IngestionJob, Scheme, SchemeDocument, SchemeSource
from app.rag.chunking import chunk_pages, is_boilerplate
from app.rag.embeddings import Embedder
from app.rag.extract import ExtractionError, detect_kind, extract, looks_like_injection
from app.rag.store import StoredChunk, VectorStore

log = logging.getLogger("rag.ingest")

ALLOWED_HOST_SUFFIXES = (".gov.in", ".nic.in")
MAX_BYTES = 30 * 1024 * 1024


@dataclass
class Fetched:
    data: bytes
    content_type: str | None
    status: int


Fetcher = Callable[[str], Fetched]


class FetchError(Exception):
    pass


def check_url_allowed(url: str) -> None:
    parts = urlparse(url)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or not host:
        raise FetchError("only https URLs are fetched")
    try:
        ipaddress.ip_address(host)
        raise FetchError("IP-literal hosts are not allowed")
    except ValueError:
        pass
    if not host.endswith(ALLOWED_HOST_SUFFIXES):
        raise FetchError(f"host '{host}' is not an official .gov.in/.nic.in domain")


def http_fetcher(url: str) -> Fetched:
    check_url_allowed(url)
    try:
        with httpx.Client(timeout=30, follow_redirects=False,
                          headers={"User-Agent": "SchemeAssistantBot/0.1 (independent tool)"}) as c:
            r = c.get(url)
            hops = 0
            while r.is_redirect and hops < 3:  # re-validate every hop
                nxt = str(r.next_request.url)
                check_url_allowed(nxt)
                r = c.get(nxt)
                hops += 1
    except httpx.HTTPError as exc:
        raise FetchError(f"download failed: {type(exc).__name__}: {exc}") from exc
    if r.status_code != 200:
        raise FetchError(f"HTTP {r.status_code}")
    if len(r.content) > MAX_BYTES:
        raise FetchError("document too large")
    return Fetched(r.content, r.headers.get("content-type"), r.status_code)


@dataclass
class IngestEntry:
    scheme_ids: list[str]
    url: str
    title: str
    source_type: str = "page"
    local_path: str | None = None
    published_date: date | None = None


@dataclass
class IngestReport:
    job_id: int
    ok: int = 0
    duplicates: int = 0
    failed: int = 0
    chunks: int = 0
    errors: list[str] = field(default_factory=list)


def _source_row(db: Session, scheme_id: str, entry: IngestEntry) -> SchemeSource:
    row = db.scalar(select(SchemeSource).where(
        SchemeSource.scheme_id == scheme_id, SchemeSource.url == entry.url))
    if row is None:
        row = SchemeSource(scheme_id=scheme_id, url=entry.url, title=entry.title,
                           source_type=entry.source_type, verification_status="unverified")
        db.add(row)
        db.flush()
    return row


def _record_failure(db: Session, scheme_id: str, entry: IngestEntry, error: str) -> None:
    source = _source_row(db, scheme_id, entry)
    key = hashlib.sha256(f"failed:{entry.url}".encode()).hexdigest()
    doc = db.scalar(select(SchemeDocument).where(
        SchemeDocument.scheme_id == scheme_id, SchemeDocument.content_hash == key))
    if doc is None:
        doc = SchemeDocument(scheme_id=scheme_id, source_id=source.id, content_hash=key,
                             title=entry.title, status="failed")
        db.add(doc)
    doc.error = error[:2000]
    doc.status = "failed"
    source.notes = f"last ingest failed: {error[:300]}"


def ingest_entry(db: Session, store: VectorStore, embedder: Embedder, entry: IngestEntry,
                 fetcher: Fetcher, chunk_size: int, overlap: int) -> tuple[int, int]:
    """Returns (chunks_added, duplicates_skipped). Raises on fetch/extract failure."""
    if entry.local_path and Path(entry.local_path).is_file():
        data, ctype = Path(entry.local_path).read_bytes(), None
    else:
        fetched = fetcher(entry.url)
        data, ctype = fetched.data, fetched.content_type
    if not data:
        raise ExtractionError("empty document")

    kind = detect_kind(data, ctype, entry.url)
    doc_hash = hashlib.sha256(data).hexdigest()
    extracted = extract(data, kind)
    chunks = chunk_pages(extracted.pages, chunk_size, overlap)
    if not chunks:
        raise ExtractionError("no usable text after cleaning")
    vectors = embedder.embed([c.text for c in chunks])
    today = date.today()

    added = dup = 0
    for scheme_id in entry.scheme_ids:
        scheme = db.get(Scheme, scheme_id)
        if scheme is None:
            raise ValueError(f"unknown scheme id '{scheme_id}'")
        if db.scalar(select(SchemeDocument).where(
                SchemeDocument.scheme_id == scheme_id, SchemeDocument.content_hash == doc_hash)):
            dup += 1
            continue

        source = _source_row(db, scheme_id, entry)
        previous = db.scalars(select(SchemeDocument).where(
            SchemeDocument.scheme_id == scheme_id, SchemeDocument.source_id == source.id,
            SchemeDocument.status == "ok", SchemeDocument.is_outdated.is_(False))).all()
        version = max([p.version for p in previous], default=0) + 1
        for p in previous:  # superseded: keep the record, drop its vectors
            p.is_outdated = True
            store.delete_document(p.id)

        doc = SchemeDocument(
            scheme_id=scheme_id, source_id=source.id, title=entry.title, content_hash=doc_hash,
            local_path=entry.local_path, page_count=extracted.page_count, chunk_count=len(chunks),
            published_date=entry.published_date, verified_date=today, version=version, status="ok")
        db.add(doc)
        db.flush()

        stored = []
        for c, vec in zip(chunks, vectors):
            stored.append(StoredChunk(
                id=f"{doc.id}-{c.index}", text=c.text, embedding=vec,
                metadata={
                    "document_id": doc.id, "chunk_index": c.index, "scheme_id": scheme_id,
                    "jurisdiction": scheme.jurisdiction, "state": scheme.applicable_state,
                    "source_url": entry.url, "title": entry.title, "page": c.page or 0,
                    "version": version, "verified_date": today.isoformat(),
                    "source_status": scheme.verification_status, "is_outdated": False,
                    "suspicious": looks_like_injection(c.text),
                    "boilerplate": is_boilerplate(c.text),
                }))
        store.upsert(stored)
        added += len(stored)
    return added, dup


def run_ingestion(db: Session, store: VectorStore, embedder: Embedder, entries: list[IngestEntry],
                  fetcher: Fetcher = http_fetcher, chunk_size: int = 900, overlap: int = 150,
                  scheme_id: str | None = None) -> IngestReport:
    job = IngestionJob(scheme_id=scheme_id, status="running")
    db.add(job)
    db.commit()
    report = IngestReport(job_id=job.id)
    for entry in entries:
        if scheme_id and scheme_id not in entry.scheme_ids:
            continue
        try:
            added, dup = ingest_entry(db, store, embedder, entry, fetcher, chunk_size, overlap)
            db.commit()
            report.chunks += added
            report.duplicates += dup
            report.ok += 1 if added else 0
        except Exception as exc:  # recorded, not fatal for the batch
            db.rollback()
            msg = f"{entry.url}: {type(exc).__name__}: {exc}"
            log.warning("ingest failed", extra={"ctx": {"url": entry.url, "error": str(exc)[:200]}})
            report.failed += 1
            report.errors.append(msg)
            for sid in entry.scheme_ids:
                if db.get(Scheme, sid):
                    _record_failure(db, sid, entry, msg)
            db.commit()
    job = db.get(IngestionJob, job.id)
    job.documents_ok, job.documents_failed, job.errors = report.ok, report.failed, report.errors
    job.status = ("failed" if report.failed and not report.ok
                  else "completed_with_errors" if report.failed else "completed")
    job.finished_at = datetime.utcnow()
    db.commit()
    return report
