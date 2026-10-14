"""CLI: seed schemes, then ingest official documents listed in data/documents/manifest.json.

    python -m app.scripts.ingest [--scheme SCHEME_ID]
"""
import argparse

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.rag.embeddings import build_embedder
from app.rag.ingest import run_ingestion
from app.rag.store import VectorStore
from app.services.manifest import DEFAULT_MANIFEST, ROOT, load_entries  # noqa: F401
from app.services.seed import seed_schemes

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheme", default=None)
    args = ap.parse_args()
    s = get_settings()
    import app.models  # noqa: F401

    Base.metadata.create_all(engine)
    db = SessionLocal()
    seed_schemes(db)
    embedder = build_embedder(s.embedding_backend, s.embedding_model, s.embedding_cache_dir)
    store = VectorStore(s.chroma_path)
    report = run_ingestion(db, store, embedder, load_entries(DEFAULT_MANIFEST),
                           chunk_size=s.chunk_size, overlap=s.chunk_overlap, scheme_id=args.scheme)
    print(f"job={report.job_id} ok={report.ok} duplicates={report.duplicates} "
          f"failed={report.failed} chunks={report.chunks} vectors_in_store={store.count()}")
    for err in report.errors:
        print("  FAILED:", err)


if __name__ == "__main__":
    main()
