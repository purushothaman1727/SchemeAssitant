from datetime import datetime, timedelta

import fitz
import pytest

from app.api.deps import get_embedder, get_fetcher, get_store
from app.main import app
from app.models import (
    AdminUser, ApplicantProfile, ChatMessage, ChatSession, RecommendationResult, Scheme,
)
from app.rag.embeddings import HashingEmbedder
from app.rag.ingest import Fetched, FetchError
from app.rag.store import VectorStore
from app.scripts.create_admin import upsert_admin
from app.services.retention import purge_expired
from app.services.seed import seed_schemes

PASSWORD = "correct horse battery staple"


@pytest.fixture
def admin(db):
    upsert_admin(db, "admin", PASSWORD)
    return db


def token(client) -> dict:
    r = client.post("/api/admin/login", json={"username": "admin", "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


NEW = {
    "id": "demo-scheme", "name": "Demo Scheme For Tests", "jurisdiction": "central", "category": "scholarship",
    "official_url": "https://depwd.gov.in/en/demo/", "verification_status": "partially_verified",
    "date_checked": "2026-10-14",
    "rules": [{"key": "min_age", "field": "age", "operator": "gte", "value": 18, "verified": True,
               "description": "Age 18 or above."}],
    "sources": [{"url": "https://depwd.gov.in/en/demo/", "title": "Demo page"}],
}


# ---- authentication ----------------------------------------------------------------------
@pytest.mark.parametrize("method,path", [
    ("get", "/api/admin/sources"), ("get", "/api/admin/ingestion-jobs"),
    ("post", "/api/admin/ingest"), ("post", "/api/admin/schemes"), ("patch", "/api/admin/schemes/x"),
])
def test_admin_endpoints_reject_anonymous(client, admin, method, path):
    r = getattr(client, method)(path, **({"json": {}} if method != "get" else {}))
    assert r.status_code == 401


def test_login_success_and_wrong_password(client, admin):
    assert token(client)
    r = client.post("/api/admin/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401
    r = client.post("/api/admin/login", json={"username": "nobody", "password": PASSWORD})
    assert r.status_code == 401 and r.json()["detail"] == "Incorrect username or password"


def test_tampered_or_foreign_token_is_rejected(client, admin):
    import jwt

    good = token(client)["Authorization"].split()[1]
    assert client.get("/api/admin/sources", headers={"Authorization": f"Bearer {good}x"}).status_code == 401
    forged = jwt.encode({"sub": "admin", "scope": "admin", "exp": 9999999999}, "wrong-secret", algorithm="HS256")
    assert client.get("/api/admin/sources", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    no_scope = jwt.encode({"sub": "admin", "exp": 9999999999},
                          "test-secret-not-for-production-0123456789", algorithm="HS256")
    assert client.get("/api/admin/sources", headers={"Authorization": f"Bearer {no_scope}"}).status_code == 401


def test_deactivated_admin_token_stops_working(client, admin):
    h = token(client)
    admin.query(AdminUser).update({"is_active": False})
    admin.commit()
    assert client.get("/api/admin/sources", headers=h).status_code == 401


def test_login_is_rate_limited(client, admin):
    codes = [client.post("/api/admin/login", json={"username": "admin", "password": "bad"}).status_code
             for _ in range(7)]
    assert codes[:5] == [401] * 5
    assert 429 in codes[5:]


def test_password_policy_and_reset(db):
    with pytest.raises(ValueError):
        upsert_admin(db, "a", "short")
    assert upsert_admin(db, "a", PASSWORD) is True
    assert upsert_admin(db, "a", PASSWORD + "!") is False
    assert db.query(AdminUser).count() == 1
    assert PASSWORD not in db.query(AdminUser).one().password_hash


# ---- scheme management ---------------------------------------------------------------------
def test_create_scheme_roundtrip_is_public_afterwards(client, admin):
    h = token(client)
    r = client.post("/api/admin/schemes", json=NEW, headers=h)
    assert r.status_code == 201, r.text
    assert r.json()["rules"][0]["verified"] is True
    assert client.get("/api/schemes/demo-scheme").status_code == 200
    assert client.post("/api/admin/schemes", json=NEW, headers=h).status_code == 409


@pytest.mark.parametrize("patch", [
    {"official_url": "https://example.com/x"},
    {"official_url": "http://depwd.gov.in/x"},
    {"id": "Bad ID"},
    {"jurisdiction": "mars"},
    {"rules": [{"key": "r1", "field": "not_a_field", "operator": "eq", "value": 1, "description": "typo field"}]},
    {"rules": [{"key": "r1", "field": "age", "operator": "weird", "value": 1, "description": "bad operator"}]},
    {"rules": [{"key": "r1", "field": "age", "operator": "between", "value": [1], "description": "bad between"}]},
    {"verification_status": "unverified"},  # a verified rule is present
    {"accepting_applications": True, "date_checked": None},
])
def test_create_scheme_validation(client, admin, patch):
    body = {**NEW, **patch}
    assert client.post("/api/admin/schemes", json=body, headers=token(client)).status_code == 422


def test_patch_scheme_updates_fields(client, admin):
    seed_schemes(admin)
    h = token(client)
    r = client.patch("/api/admin/schemes/adip", headers=h, json={
        "accepting_applications": False, "date_checked": "2026-10-14",
        "verification_notes": "Checked portal; closed."})
    assert r.status_code == 200
    body = client.get("/api/schemes/adip").json()
    assert body["accepting_applications"] is False and body["verification_notes"].startswith("Checked")
    assert client.patch("/api/admin/schemes/nope", headers=h, json={"summary": "x"}).status_code == 404


def test_patch_cannot_promote_rules_on_unverified_scheme(client, admin):
    seed_schemes(admin)
    h = token(client)
    rule = {"key": "min_age", "field": "age", "operator": "gte", "value": 60, "verified": True,
            "description": "Age 60 or above."}
    r = client.patch("/api/admin/schemes/ignoa-ps", headers=h, json={"rules": [rule]})
    assert r.status_code == 422
    admin.expire_all()
    assert admin.get(Scheme, "ignoa-ps").verification_status == "unverified"  # rolled back
    ok = client.patch("/api/admin/schemes/ignoa-ps", headers=h, json={
        "rules": [rule], "verification_status": "verified", "date_checked": "2026-10-14"})
    assert ok.status_code == 200


def test_edited_rules_change_eligibility_results(client, admin):
    seed_schemes(admin)
    h = token(client)
    rule = {"key": "min_age", "field": "age", "operator": "gte", "value": 60, "verified": True,
            "description": "Age 60 or above."}
    client.patch("/api/admin/schemes/ignoa-ps", headers=h, json={
        "rules": [rule], "verification_status": "verified", "operational_status": "active",
        "date_checked": "2026-10-14"})
    r = client.post("/api/recommendations", json={"profile": {"age": 70}}).json()
    assert next(c for c in r["results"] if c["scheme_id"] == "ignoa-ps")["status"] == "potentially_eligible"
    r = client.post("/api/recommendations", json={"profile": {"age": 30}}).json()
    assert next(c for c in r["results"] if c["scheme_id"] == "ignoa-ps")["status"] == "does_not_match"


# ---- ingestion + sources ---------------------------------------------------------------------
def _pdf(text):
    d = fitz.open()
    p = d.new_page()
    p.insert_textbox(fitz.Rect(40, 40, 550, 800), text, fontsize=11)
    return d.tobytes()


@pytest.fixture
def ingest_env(tmp_path):
    store = VectorStore(str(tmp_path / "chroma"))
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_embedder] = lambda: HashingEmbedder()
    yield store
    app.dependency_overrides.clear()


def test_admin_ingest_runs_job_and_reports_failures(client, admin, ingest_env):
    seed_schemes(admin)
    good = _pdf("ADIP provides aids and appliances to persons with disabilities. " * 4)

    def fetcher(url):
        if "adip" in url:
            return Fetched(good, "application/pdf", 200)
        raise FetchError("HTTP 503")

    app.dependency_overrides[get_fetcher] = lambda: fetcher
    h = token(client)
    assert client.post("/api/admin/ingest", json={"scheme_id": "adip"}, headers=h).status_code == 202
    jobs = client.get("/api/admin/ingestion-jobs", headers=h).json()
    assert jobs and jobs[0]["status"] == "completed" and jobs[0]["documents_ok"] == 1
    assert ingest_env.count() > 0

    assert client.post("/api/admin/ingest", json={"scheme_id": "ddrs"}, headers=h).status_code == 202
    jobs = client.get("/api/admin/ingestion-jobs", headers=h).json()
    assert jobs[0]["status"] == "failed" and "503" in jobs[0]["errors"][0]

    src = client.get("/api/admin/sources", params={"scheme_id": "ddrs"}, headers=h).json()
    assert src["items"][0]["documents_failed"] == 1 and "503" in src["items"][0]["last_error"]
    assert client.post("/api/admin/ingest", json={"scheme_id": "nope"}, headers=h).status_code == 404


def test_sources_listing_paginates(client, admin):
    seed_schemes(admin)
    h = token(client)
    r = client.get("/api/admin/sources", params={"page_size": 5, "page": 2}, headers=h).json()
    assert r["total"] >= 20 and len(r["items"]) == 5
    assert client.get("/api/admin/sources", params={"page_size": 500}, headers=h).status_code == 422


# ---- retention ---------------------------------------------------------------------------------
def test_purge_removes_only_expired_records(db):
    now = datetime.utcnow()
    old, fresh = now - timedelta(days=1), now + timedelta(days=5)
    db.add_all([ApplicantProfile(id="p-old", expires_at=old), ApplicantProfile(id="p-new", expires_at=fresh)])
    db.flush()
    db.add_all([RecommendationResult(id="r-old", profile_id="p-old", expires_at=fresh),
                RecommendationResult(id="r-new", profile_id="p-new", expires_at=fresh),
                ChatSession(id="s-old", expires_at=old), ChatSession(id="s-new", expires_at=fresh)])
    db.flush()
    db.add_all([ChatMessage(session_id="s-old", role="user", content="x"),
                ChatMessage(session_id="s-new", role="user", content="y")])
    db.commit()
    counts = purge_expired(db)
    assert counts == {"chat_messages": 1, "chat_sessions": 1, "recommendation_results": 1,
                      "applicant_profiles": 1}
    assert {p.id for p in db.query(ApplicantProfile)} == {"p-new"}
    assert {s.id for s in db.query(ChatSession)} == {"s-new"}
    assert db.query(ChatMessage).count() == 1


# ---- hardening -----------------------------------------------------------------------------------
def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert r.headers["cache-control"] == "no-store"


def test_api_docs_reachable_and_all_required_endpoints_documented(client):
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    for p in ["/api/health", "/api/schemes", "/api/schemes/{scheme_id}", "/api/profile/validate",
              "/api/recommendations", "/api/chat", "/api/admin/ingest", "/api/admin/sources",
              "/api/admin/schemes", "/api/admin/schemes/{scheme_id}"]:
        assert p in paths, p


def test_no_secret_fields_in_public_responses(client, admin):
    seed_schemes(admin)
    text = (client.get("/api/schemes").text + client.get("/api/schemes/adip").text
            + client.get("/api/health").text)
    for needle in ("password", "jwt", "secret", "api_key"):
        assert needle not in text.lower()


def test_cors_only_allows_configured_origin(client):
    ok = client.options("/api/health", headers={"Origin": "http://localhost:5173",
                                                "Access-Control-Request-Method": "GET"})
    bad = client.options("/api/health", headers={"Origin": "https://evil.example",
                                                 "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in bad.headers
