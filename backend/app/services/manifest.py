import json
from datetime import date
from pathlib import Path

from app.rag.ingest import IngestEntry

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = ROOT / "data" / "documents" / "manifest.json"


def load_entries(path: Path = DEFAULT_MANIFEST) -> list[IngestEntry]:
    entries = []
    for e in json.loads(path.read_text(encoding="utf-8"))["entries"]:
        lp = e.get("local_path")
        entries.append(IngestEntry(
            scheme_ids=e["scheme_ids"], url=e["url"], title=e["title"],
            source_type=e.get("source_type", "page"),
            local_path=str(ROOT / lp) if lp else None,
            published_date=date.fromisoformat(e["published_date"]) if e.get("published_date") else None,
        ))
    return entries
