"""Shared FastAPI dependencies. Tests override these via app.dependency_overrides."""
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.rag.embeddings import Embedder, build_embedder
from app.rag.store import VectorStore
from app.rag.ingest import Fetcher, http_fetcher
from app.services.llm import LLMClient, build_llm


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache
def get_embedder() -> Embedder:
    s = get_settings()
    return build_embedder(s.embedding_backend, s.embedding_model, s.embedding_cache_dir)


@lru_cache
def get_store() -> VectorStore:
    return VectorStore(get_settings().chroma_path)


@lru_cache
def get_llm() -> LLMClient:
    return build_llm(get_settings())


def get_fetcher() -> Fetcher:
    return http_fetcher
