from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.models import Scheme
from app.schemas.recommendation import (
    RecommendationRequest, RecommendationResponse, RuleOut, SchemeDetail, SchemePage,
    SchemeSummary, SourceOut,
)
from app.services.recommendation import recommend

router = APIRouter()


def _summary(s: Scheme) -> SchemeSummary:
    return SchemeSummary(
        id=s.id, name=s.name, name_ta=s.name_ta, jurisdiction=s.jurisdiction,
        applicable_state=s.applicable_state, category=s.category,
        beneficiary_types=s.beneficiary_types or [], summary=s.summary,
        verification_status=s.verification_status, operational_status=s.operational_status,
        is_cash_benefit=s.is_cash_benefit, date_checked=s.date_checked, official_url=s.official_url,
    )


@router.get("/schemes", response_model=SchemePage)
def list_schemes(
    q: str | None = Query(default=None, max_length=100),
    jurisdiction: str | None = Query(default=None, pattern="^(central|tamil_nadu)$"),
    category: str | None = Query(default=None, max_length=60),
    beneficiary_type: str | None = Query(default=None, max_length=60),
    state: str | None = Query(default=None, max_length=80),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_session),
) -> SchemePage:
    stmt = select(Scheme)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Scheme.name).like(like), func.lower(Scheme.summary).like(like)))
    if jurisdiction:
        stmt = stmt.where(Scheme.jurisdiction == jurisdiction)
    if category:
        stmt = stmt.where(Scheme.category == category)
    if state:
        stmt = stmt.where(or_(Scheme.applicable_state == "ALL", Scheme.applicable_state == state))
    rows = db.scalars(stmt.order_by(Scheme.jurisdiction, Scheme.name)).all()
    if beneficiary_type:  # JSON list membership, filtered in Python for DB portability
        rows = [r for r in rows if beneficiary_type in (r.beneficiary_types or [])]
    total = len(rows)
    start = (page - 1) * page_size
    return SchemePage(total=total, page=page, page_size=page_size,
                      items=[_summary(r) for r in rows[start:start + page_size]])


@router.get("/schemes/{scheme_id}", response_model=SchemeDetail)
def get_scheme(scheme_id: str, db: Session = Depends(get_session)) -> SchemeDetail:
    s = db.get(Scheme, scheme_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return SchemeDetail(
        **_summary(s).model_dump(), benefits=s.benefits,
        required_documents=s.required_documents or [], application_steps=s.application_steps or [],
        application_url=s.application_url, accepting_applications=s.accepting_applications,
        verification_notes=s.verification_notes,
        rules=[RuleOut(key=r.rule_key, field=r.field, operator=r.operator, value=r.value,
                       mandatory=r.mandatory, verified=r.verified, description=r.description)
               for r in s.rules],
        sources=[SourceOut(url=x.url, title=x.title, source_type=x.source_type,
                           verification_status=x.verification_status, date_checked=x.date_checked)
                 for x in s.sources],
    )


@router.post("/recommendations", response_model=RecommendationResponse)
def recommendations(body: RecommendationRequest, db: Session = Depends(get_session)) -> RecommendationResponse:
    # Computed from the request body only; the profile is not stored.
    return recommend(db, body.profile)
