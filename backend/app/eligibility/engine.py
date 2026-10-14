"""Deterministic eligibility engine.

No LLM, no network, no database access: callers pass scheme specs and a profile.
The LLM may explain a result but can never change it.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Protocol

POTENTIALLY_ELIGIBLE = "potentially_eligible"
MORE_INFO = "more_information_required"
NO_MATCH = "does_not_match"
UNVERIFIED = "information_unverified"


class RuleOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class RuleLike(Protocol):
    rule_key: str
    field: str
    operator: str
    value: Any
    mandatory: bool
    verified: bool
    description: str


class SchemeLike(Protocol):
    id: str
    verification_status: str
    operational_status: str
    rules: Iterable[RuleLike]


@dataclass
class RuleResult:
    key: str
    field: str
    outcome: RuleOutcome
    mandatory: bool
    verified: bool
    description: str
    message: str
    missing: list[str] = field(default_factory=list)  # profile fields that were unknown


@dataclass
class Evaluation:
    scheme_id: str
    status: str
    reasons: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    rule_results: list[RuleResult] = field(default_factory=list)


def _norm(v: Any) -> Any:
    return v.strip().lower() if isinstance(v, str) else v


def _get(profile: Any, name: str) -> Any:
    value = profile.get(name) if isinstance(profile, dict) else getattr(profile, name, None)
    return None if value == "unknown" else value


def _combine(op: str, outcomes: list[RuleOutcome]) -> RuleOutcome:
    if op == "any_of":
        if RuleOutcome.PASS in outcomes:
            return RuleOutcome.PASS
        return RuleOutcome.FAIL if all(o is RuleOutcome.FAIL for o in outcomes) else RuleOutcome.UNKNOWN
    # all_of
    if RuleOutcome.FAIL in outcomes:
        return RuleOutcome.FAIL
    return RuleOutcome.PASS if all(o is RuleOutcome.PASS for o in outcomes) else RuleOutcome.UNKNOWN


def _eval(field_name: str, op: str, expected: Any, profile: Any,
          description: str) -> tuple[RuleOutcome, str, list[str]]:
    """Evaluate one condition. `any_of` / `all_of` take a list of {field, operator, value}."""
    if op in ("any_of", "all_of"):
        subs = [_eval(c.get("field", ""), c["operator"], c["value"], profile, description)
                for c in expected]
        outcome = _combine(op, [s[0] for s in subs])
        missing: list[str] = []
        if outcome is RuleOutcome.UNKNOWN:
            for s in subs:
                missing += [m for m in s[2] if m not in missing]
        return outcome, description, missing

    actual = _get(profile, field_name)

    # Declining to state disability status never counts as "no disability".
    if field_name == "disability_status" and actual == "prefer_not_to_say":
        if op == "in" and "prefer_not_to_say" in expected:
            return RuleOutcome.PASS, "Disability status was not disclosed; this scheme may still apply.", []
        return (RuleOutcome.UNKNOWN,
                "Disability status was not disclosed, so this cannot be checked.", [field_name])

    if actual is None:
        return RuleOutcome.UNKNOWN, f"'{field_name}' was not provided.", [field_name]

    try:
        if op == "eq":
            ok = _norm(actual) == _norm(expected)
        elif op == "gte":
            ok = actual >= expected
        elif op == "lte":
            ok = actual <= expected
        elif op == "between":
            ok = expected[0] <= actual <= expected[1]
        elif op == "in":
            ok = _norm(actual) in [_norm(e) for e in expected]
        elif op == "is_true":
            ok = bool(actual) is bool(expected)
        else:
            return RuleOutcome.UNKNOWN, f"Unsupported operator '{op}'.", []
    except TypeError:
        return RuleOutcome.UNKNOWN, f"'{field_name}' has an unexpected value.", []

    return (RuleOutcome.PASS if ok else RuleOutcome.FAIL), description, []


def evaluate_scheme(scheme: SchemeLike, profile: Any) -> Evaluation:
    rules = list(scheme.rules)
    results: list[RuleResult] = []
    for r in rules:
        outcome, message, missing = _eval(r.field, r.operator, r.value, profile, r.description)
        results.append(RuleResult(r.rule_key, r.field, outcome, r.mandatory, r.verified,
                                  r.description, message, missing))
    mandatory = [r for r in results if r.mandatory]
    ev = Evaluation(scheme_id=scheme.id, status=UNVERIFIED, rule_results=results)

    if scheme.operational_status == "discontinued":
        ev.reasons.append("This scheme is recorded as discontinued; check the official source.")
        return ev
    if not rules or scheme.verification_status == "unverified":
        ev.reasons.append(
            "Reliable current eligibility rules for this scheme could not be verified, "
            "so no eligibility assessment is made."
        )
        return ev

    verified_fail = [r for r in mandatory if r.verified and r.outcome is RuleOutcome.FAIL]
    if verified_fail:
        ev.status = NO_MATCH
        ev.reasons = [f"Does not meet: {r.description}" for r in verified_fail]
        return ev

    unknown = [r for r in mandatory if r.verified and r.outcome is RuleOutcome.UNKNOWN]
    if unknown:
        ev.status = MORE_INFO
        ev.missing_fields = sorted({m for r in unknown for m in (r.missing or [r.field])})
        ev.reasons = [
            f"Needed to check: {r.description}" + (f" ({r.message})" if r.message != r.description else "")
            for r in unknown
        ]
        return ev

    unverified = [r for r in mandatory if not r.verified]
    if unverified:
        ev.status = UNVERIFIED
        ev.reasons = [
            "Some eligibility conditions come from unofficial sources and are not verified: "
            + "; ".join(r.description.rstrip(". ") for r in unverified) + "."
        ]
        return ev

    ev.status = POTENTIALLY_ELIGIBLE
    ev.reasons = [f"Meets: {r.description}" for r in mandatory if r.outcome is RuleOutcome.PASS]
    ev.reasons += [f"Note: {r.description}" for r in results if not r.mandatory and r.verified]
    ev.reasons.append(
        "Based on the verified criteria checked here. Official verification and additional "
        "checks (documents, slots, application window) may still apply."
    )
    return ev


def evaluate_all(schemes: Iterable[SchemeLike], profile: Any) -> list[Evaluation]:
    return [evaluate_scheme(s, profile) for s in schemes]
