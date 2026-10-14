"""Recommendation ranking. Statuses come from the deterministic engine; ranking only orders them."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.eligibility.engine import (
    MORE_INFO, NO_MATCH, POTENTIALLY_ELIGIBLE, UNVERIFIED, Evaluation, evaluate_scheme,
)
from app.models import Scheme, SchemeDocument
from app.schemas.profile import ApplicantProfile
from app.schemas.recommendation import RecommendationCard, RecommendationResponse

JURISDICTION_LABEL = {"central": "Central Government", "tamil_nadu": "Tamil Nadu Government"}
_ELIGIBILITY_WEIGHT = {POTENTIALLY_ELIGIBLE: 1.0, MORE_INFO: 0.5, UNVERIFIED: 0.2, NO_MATCH: 0.0}
# weights sum to 100; no benefit amounts are used anywhere in ranking
W_ELIGIBILITY, W_RELEVANCE, W_STATE, W_EVIDENCE, W_COMPLETE = 50, 15, 10, 10, 15


def profile_audiences(p: ApplicantProfile) -> set[str]:
    a: set[str] = set()
    if p.disability_status == "yes":
        a.add("person_with_disability")
    if p.is_student == "yes":
        a.add("student")
    if p.applying_for == "child" or (p.age is not None and p.age < 18):
        a.add("child")
    if p.age is not None and p.age >= 60:
        a.add("senior_citizen")
    if p.is_widow:
        a.add("widow")
    if p.land_holding_hectares is not None:
        a.add("farmer")
    if p.registered_unemployed_over_1_year:
        a.add("job_seeker")
    if p.guardian_has_disability:
        a.add("family_of_person_with_disability")
    if p.high_support_need_certified:
        a.add("caregiver")
    return a


def _same_state(a: str | None, b: str | None) -> bool:
    return bool(a and b and " ".join(a.lower().split()) == " ".join(b.lower().split()))


def _why_relevant(s: Scheme, p: ApplicantProfile, audiences: set[str]) -> list[str]:
    why = []
    if s.jurisdiction == "tamil_nadu" and _same_state(p.state, "Tamil Nadu"):
        why.append("Tamil Nadu scheme and you indicated Tamil Nadu as your state.")
    elif s.jurisdiction == "central":
        why.append("Central Government scheme that is not limited to one state.")
    overlap = audiences & set(s.beneficiary_types or [])
    labels = {
        "person_with_disability": "it is meant for persons with disabilities, which you indicated",
        "student": "it is meant for students",
        "child": "it covers children / school-age applicants",
        "senior_citizen": "it is meant for senior citizens",
        "widow": "it is meant for widows",
        "farmer": "it is meant for farmers",
        "job_seeker": "it is meant for registered job seekers",
        "family_of_person_with_disability": "it is meant for families of persons with disabilities",
        "caregiver": "it is meant for care takers",
    }
    for key in sorted(overlap):
        if key in labels:
            why.append(f"Relevant because {labels[key]}.")
    return why


def _limitations(s: Scheme, ev: Evaluation) -> list[str]:
    out = []
    if s.verification_status != "verified":
        out.append(f"Scheme record is {s.verification_status.replace('_', ' ')}; see verification notes on the scheme page.")
    if s.accepting_applications is None:
        out.append("Whether applications are currently open could not be confirmed; check the official portal.")
    if not s.is_cash_benefit:
        out.append("This is not a direct cash-benefit scheme.")
    if s.operational_status == "unverified":
        out.append("Current operational status could not be verified.")
    return out


def rank_score(s: Scheme, ev: Evaluation, p: ApplicantProfile, audiences: set[str], has_docs: bool) -> float:
    elig = _ELIGIBILITY_WEIGHT[ev.status]
    types = set(s.beneficiary_types or [])
    relevance = (len(audiences & types) / len(types)) if types else 0.0
    if s.applicable_state == "ALL":
        state = 0.5
    else:
        state = 1.0 if _same_state(p.state, s.applicable_state) else 0.0
    mandatory = [r for r in ev.rule_results if r.mandatory]
    complete = 1.0 - (len(ev.missing_fields) / len(mandatory)) if mandatory else 0.0
    total = (W_ELIGIBILITY * elig + W_RELEVANCE * min(relevance * 2, 1.0) + W_STATE * state
             + W_EVIDENCE * (1.0 if has_docs else 0.0) + W_COMPLETE * max(complete, 0.0))
    return round(total, 2)


def recommend(db: Session, profile: ApplicantProfile) -> RecommendationResponse:
    schemes = db.scalars(select(Scheme).order_by(Scheme.id)).all()
    doc_counts = dict(db.execute(
        select(SchemeDocument.scheme_id, func.count()).where(SchemeDocument.status == "ok",
                                                             SchemeDocument.is_outdated.is_(False))
        .group_by(SchemeDocument.scheme_id)).all())
    audiences = profile_audiences(profile)

    cards: list[RecommendationCard] = []
    for s in schemes:
        ev = evaluate_scheme(s, profile)
        cards.append(RecommendationCard(
            scheme_id=s.id, name=s.name, name_ta=s.name_ta, jurisdiction=s.jurisdiction,
            jurisdiction_label=JURISDICTION_LABEL.get(s.jurisdiction, s.jurisdiction),
            category=s.category, status=ev.status,
            why_relevant=_why_relevant(s, profile, audiences), reasons=ev.reasons,
            missing_fields=ev.missing_fields,
            benefits=s.benefits,  # only text recorded in the verified dataset, else None
            required_documents=s.required_documents or [], application_steps=s.application_steps or [],
            official_url=s.official_url, application_url=s.application_url,
            last_verified=s.date_checked, verification_status=s.verification_status,
            accepting_applications=s.accepting_applications, limitations=_limitations(s, ev),
            score=rank_score(s, ev, profile, audiences, doc_counts.get(s.id, 0) > 0),
            show_by_default=ev.status != NO_MATCH,
        ))
    cards.sort(key=lambda c: (-c.score, c.scheme_id))
    counts: dict[str, int] = {}
    for c in cards:
        counts[c.status] = counts.get(c.status, 0) + 1
    return RecommendationResponse(results=cards, counts=counts)
