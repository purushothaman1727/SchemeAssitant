from app.models import Scheme


def test_health_reports_database_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "database": True}


def test_all_phase1_tables_exist(db):
    from sqlalchemy import inspect

    names = set(inspect(db.get_bind()).get_table_names())
    required = {
        "schemes", "eligibility_rules", "scheme_sources", "scheme_documents",
        "applicant_profiles", "recommendation_results", "chat_sessions",
        "chat_messages", "admin_users", "ingestion_jobs",
    }
    assert required <= names


def test_profile_validate_normalises_and_adds_notes(client):
    r = client.post("/api/profile/validate", json={
        "state": "  Tamil   Nadu ", "disability_status": "no", "disability_percentage": 80})
    assert r.status_code == 200
    body = r.json()
    assert body["profile"]["state"] == "Tamil Nadu"
    assert body["profile"]["disability_percentage"] is None
    assert any("Age not provided" in n for n in body["notes"])


def test_profile_validate_rejects_bad_input(client):
    assert client.post("/api/profile/validate", json={"age": 500}).status_code == 422
    assert client.post("/api/profile/validate", json={"disability_status": "maybe"}).status_code == 422
    assert client.post("/api/profile/validate", json={"surprise": 1}).status_code == 422


def test_scheme_persistence_roundtrip(db):
    db.add(Scheme(id="demo", name="Demo", jurisdiction="central", category="test"))
    db.commit()
    assert db.get(Scheme, "demo").name == "Demo"
