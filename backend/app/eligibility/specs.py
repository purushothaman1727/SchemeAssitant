"""Plain-data scheme specs so the engine can run from JSON or ORM objects alike."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleSpec:
    rule_key: str
    field: str
    operator: str
    value: Any
    mandatory: bool = True
    verified: bool = False
    description: str = ""


@dataclass
class SchemeSpec:
    id: str
    verification_status: str = "verified"
    operational_status: str = "active"
    rules: list[RuleSpec] = field(default_factory=list)


def spec_from_dict(item: dict) -> SchemeSpec:
    return SchemeSpec(
        id=item["id"],
        verification_status=item.get("verification_status", "unverified"),
        operational_status=item.get("operational_status", "unverified"),
        rules=[
            RuleSpec(
                rule_key=r["key"], field=r["field"], operator=r["operator"], value=r["value"],
                mandatory=r.get("mandatory", True), verified=r.get("verified", False),
                description=r.get("description", ""),
            )
            for r in item.get("rules", [])
        ],
    )
