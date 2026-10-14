import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_embedder, get_fetcher, get_session, get_store
from app.api.schemes import _summary
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.limiter import limiter
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models import AdminUser, EligibilityRule, IngestionJob, Scheme, SchemeDocument, SchemeSource
from app.rag.ingest import run_ingestion
from app.schemas.admin import (
    IngestionJobOut, IngestRequest, IngestStarted, LoginRequest, SchemeCreate, SchemeUpdate,
    SourceAdminOut, SourcePage, TokenResponse,
)
from app.schemas.recommendation import RuleOut, SchemeDetail, SourceOut
from app.services.manifest import load_entries

log = logging.getLogger("admin")
router = APIRouter(prefix="/admin", tags=["admin"])
_bearer = HTTPBearer(auto_error=False)


def require_admin(creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
                  db: Session = Depends(get_session)) -> AdminUser:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated",
                                 headers={"WWW-Authenticate": "Bearer"})
    if creds is None:
        raise unauthorized
    username = decode_access_token(creds.credentials, get_settings())
    if username is None:
        raise unauthorized
    user = db.scalar(select(AdminUser).where(AdminUser.username == username))
    if user is None or not user.is_active:
        raise unauthorized
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_session)) -> TokenResponse:
    user = db.scalar(select(AdminUser).where(AdminUser.username == body.username))
    ok = verify_password(body.password, user.password_hash if user else None)
    if not (ok and user and user.is_active):
        log.warning("admin login failed")  # no username/password in logs
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password")
    s = get_settings()
    return TokenResponse(access_token=create_access_token(user.username, s),
                         expires_in=s.jwt_expire_minutes * 60)


def _detail(s: Scheme) -> SchemeDetail:
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


def _apply_rules(db: Session, s: Scheme, rules) -> None:
    s.rules.clear()
    db.flush()  # delete old rows first: new rules may reuse the same (scheme, key)
    for r in rules:
        s.rules.append(EligibilityRule(
            rule_key=r.key, field=r.field, operator=r.operator, value=r.value, mandatory=r.mandatory,
            verified=r.verified, description=r.description, source_url=s.official_url))


def _apply_sources(db: Session, s: Scheme, sources) -> None:
    s.sources.clear()
    db.flush()
    for x in sources:
        s.sources.append(SchemeSource(
            url=x.url, title=x.title, source_type=x.source_type,
            verification_status=x.verification_status, applicable_state=s.applicable_state,
            date_checked=s.date_checked))


@router.post("/schemes", response_model=SchemeDetail, status_code=201)
def create_scheme(body: SchemeCreate, admin: AdminUser = Depends(require_admin),
                  db: Session = Depends(get_session)) -> SchemeDetail:
    if db.get(Scheme, body.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "A scheme with this id already exists")
    data = body.model_dump(exclude={"rules", "sources"})
    s = Scheme(**data)
    db.add(s)
    db.flush()
    _apply_rules(db, s, body.rules)
    _apply_sources(db, s, body.sources)
    db.commit()
    log.info("scheme created", extra={"ctx": {"scheme": s.id, "by": admin.username}})
    return _detail(s)


@router.patch("/schemes/{scheme_id}", response_model=SchemeDetail)
def update_scheme(scheme_id: str, body: SchemeUpdate, admin: AdminUser = Depends(require_admin),
                  db: Session = Depends(get_session)) -> SchemeDetail:
    s = db.get(Scheme, scheme_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scheme not found")
    changes = body.model_dump(exclude_unset=True, exclude={"rules", "sources"})
    for k, v in changes.items():
        setattr(s, k, v)
    if body.rules is not None:
        _apply_rules(db, s, body.rules)
    if body.sources is not None:
        _apply_sources(db, s, body.sources)

    # Same invariants as creation, evaluated on the resulting record.
    if any(r.verified for r in s.rules) and (s.verification_status == "unverified" or s.date_checked is None):
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Verified rules require verification_status != 'unverified' and date_checked")
    if s.accepting_applications is True and s.date_checked is None:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "accepting_applications=true requires date_checked")
    db.commit()
    log.info("scheme updated", extra={"ctx": {"scheme": s.id, "by": admin.username,
                                              "fields": sorted(body.model_fields_set)}})
    return _detail(s)


@router.get("/sources", response_model=SourcePage)
def list_sources(scheme_id: str | None = Query(default=None, max_length=80),
                 page: int = Query(default=1, ge=1), page_size: int = Query(default=25, ge=1, le=100),
                 _: AdminUser = Depends(require_admin), db: Session = Depends(get_session)) -> SourcePage:
    stmt = select(SchemeSource)
    if scheme_id:
        stmt = stmt.where(SchemeSource.scheme_id == scheme_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(SchemeSource.scheme_id, SchemeSource.url)
                      .offset((page - 1) * page_size).limit(page_size)).all()
    items = []
    for r in rows:
        docs = db.scalars(select(SchemeDocument).where(SchemeDocument.source_id == r.id)).all()
        failed = [d for d in docs if d.status == "failed"]
        items.append(SourceAdminOut(
            id=r.id, scheme_id=r.scheme_id, url=r.url, title=r.title, source_type=r.source_type,
            verification_status=r.verification_status, date_checked=r.date_checked, notes=r.notes,
            documents_ok=sum(1 for d in docs if d.status == "ok" and not d.is_outdated),
            documents_failed=len(failed), last_error=failed[-1].error if failed else None))
    return SourcePage(total=total, page=page, page_size=page_size, items=items)


def _run_ingest_job(scheme_id: str | None, store, embedder, fetcher) -> None:
    s = get_settings()
    db = SessionLocal()
    try:
        run_ingestion(db, store, embedder, load_entries(), fetcher, s.chunk_size, s.chunk_overlap,
                      scheme_id=scheme_id)
    except Exception:  # job row already records per-document failures
        log.exception("ingestion job crashed")
    finally:
        db.close()


@router.post("/ingest", response_model=IngestStarted, status_code=202)
def start_ingest(body: IngestRequest, background: BackgroundTasks,
                 _: AdminUser = Depends(require_admin), db: Session = Depends(get_session),
                 store=Depends(get_store), embedder=Depends(get_embedder),
                 fetcher=Depends(get_fetcher)) -> IngestStarted:
    if body.scheme_id and db.get(Scheme, body.scheme_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scheme not found")
    background.add_task(_run_ingest_job, body.scheme_id, store, embedder, fetcher)
    return IngestStarted(job_id=0, status="started")


@router.get("/ingestion-jobs", response_model=list[IngestionJobOut])
def list_jobs(limit: int = Query(default=20, ge=1, le=100), _: AdminUser = Depends(require_admin),
              db: Session = Depends(get_session)) -> list[IngestionJobOut]:
    rows = db.scalars(select(IngestionJob).order_by(IngestionJob.id.desc()).limit(limit)).all()
    return [IngestionJobOut(id=j.id, scheme_id=j.scheme_id, status=j.status,
                            documents_ok=j.documents_ok, documents_failed=j.documents_failed,
                            errors=j.errors or [], started_at=j.started_at, finished_at=j.finished_at)
            for j in rows]
