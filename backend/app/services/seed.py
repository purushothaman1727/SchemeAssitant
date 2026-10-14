"""Load data/schemes.json into the database (idempotent upsert)."""
import json
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import EligibilityRule, Scheme, SchemeSource

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "data" / "schemes.json"

SCHEME_FIELDS = (
    "name", "name_ta", "jurisdiction", "applicable_state", "category", "beneficiary_types",
    "summary", "benefits", "required_documents", "application_steps", "official_url",
    "application_url", "operational_status", "accepting_applications", "is_cash_benefit",
    "verification_status", "verification_notes",
)


def load_dataset(path: Path = DEFAULT_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def seed_schemes(db: Session, path: Path = DEFAULT_PATH) -> int:
    data = load_dataset(path)
    for item in data["schemes"]:
        checked = _d(item.get("date_checked"))
        scheme = db.get(Scheme, item["id"]) or Scheme(id=item["id"])
        for field in SCHEME_FIELDS:
            setattr(scheme, field, item.get(field))
        scheme.date_checked = checked
        db.add(scheme)
        db.flush()

        scheme.rules.clear()
        scheme.sources.clear()
        db.flush()
        for r in item.get("rules", []):
            scheme.rules.append(
                EligibilityRule(
                    rule_key=r["key"], field=r["field"], operator=r["operator"], value=r["value"],
                    mandatory=r.get("mandatory", True), verified=r.get("verified", False),
                    description=r.get("description", ""), source_url=item.get("official_url"),
                )
            )
        for s in item.get("sources", []):
            scheme.sources.append(
                SchemeSource(
                    url=s["url"], title=s.get("title"), source_type=s.get("source_type", "page"),
                    applicable_state=item.get("applicable_state", "ALL"),
                    verification_status=s.get("verification_status", "unverified"),
                    date_checked=checked,
                )
            )
    db.commit()
    return len(data["schemes"])
