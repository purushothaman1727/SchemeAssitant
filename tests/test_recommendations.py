import pytest

from app.eligibility.engine import MORE_INFO, NO_MATCH, POTENTIALLY_ELIGIBLE, UNVERIFIED
from app.schemas.profile import ApplicantProfile
from app.services.recommendation import profile_audiences, recommend
from app.services.seed import seed_schemes


@pytest.fixture
def seeded(db):
    seed_schemes(db)
    return db


def P(**kw):
    return ApplicantProfile(**kw)


def by_id(resp):
    return {c.scheme_id: c for c in resp.results}


def child_profile(**over):
    base = dict(applying_for="child", age=14, state="Tamil Nadu", annual_family_income=200000,
                education_level="class_9_10", is_student="yes", disability_status="yes",
                disability_percentage=50, disability_type="locomotor", certificate_status="udid")
    base.update(over)
    return P(**base)


def test_returns_all_20_cards_with_required_fields(seeded):
    resp = recommend(seeded, child_profile())
    assert len(resp.results) == 20
    assert sum(resp.counts.values()) == 20
    c = by_id(resp)["pre-matric-swd"]
    assert c.status == POTENTIALLY_ELIGIBLE
    assert c.jurisdiction_label == "Central Government"
    assert c.official_url and c.last_verified and c.required_documents and c.application_steps
    assert c.reasons and c.why_relevant


def test_potentially_eligible_ranks_above_unverified_and_no_match(seeded):
    resp = recommend(seeded, child_profile())
    order = {c.scheme_id: i for i, c in enumerate(resp.results)}
    assert order["pre-matric-swd"] < order["pm-jay"]
    assert order["pre-matric-swd"] < order["post-matric-swd"]  # class 9-10 is not post-matric
    scores = [c.score for c in resp.results]
    assert scores == sorted(scores, reverse=True)


def test_tamil_nadu_user_gets_tn_schemes_ahead_of_other_state_user(seeded):
    tn = by_id(recommend(seeded, P(state="Tamil Nadu", disability_status="yes", disability_percentage=60)))
    other = by_id(recommend(seeded, P(state="Kerala", disability_status="yes", disability_percentage=60)))
    assert tn["tn-travel-concession"].status == POTENTIALLY_ELIGIBLE
    assert other["tn-travel-concession"].status == NO_MATCH
    assert tn["tn-travel-concession"].score > other["tn-travel-concession"].score


def test_no_match_cards_are_hidden_by_default_but_returned(seeded):
    resp = recommend(seeded, P(state="Kerala", disability_status="no", age=30))
    hidden = [c for c in resp.results if not c.show_by_default]
    assert hidden and all(c.status == NO_MATCH for c in hidden)
    assert all(c.show_by_default for c in resp.results if c.status != NO_MATCH)


def test_adult_without_disability_gets_no_eligible_scheme(seeded):
    resp = recommend(seeded, P(age=30, state="Karnataka", disability_status="no", annual_family_income=900000))
    assert resp.counts.get(POTENTIALLY_ELIGIBLE, 0) == 0


def test_prefer_not_to_say_keeps_disability_schemes_visible(seeded):
    cards = by_id(recommend(seeded, P(state="Tamil Nadu", disability_status="prefer_not_to_say")))
    assert cards["tn-travel-concession"].status == MORE_INFO
    assert cards["tn-travel-concession"].show_by_default
    assert cards["udid"].status == POTENTIALLY_ELIGIBLE


def test_unverified_schemes_never_show_benefit_amounts(seeded):
    for c in recommend(seeded, P(age=70, state="Tamil Nadu")).results:
        if c.status == UNVERIFIED and c.scheme_id in {"ignd-ps", "ignoa-ps", "ignw-ps"}:
            assert c.benefits is None
            assert c.limitations


def test_missing_application_window_is_flagged_as_limitation(seeded):
    c = by_id(recommend(seeded, child_profile()))["pre-matric-swd"]
    assert c.accepting_applications is None
    assert any("applications are currently open" in x for x in c.limitations)


def test_audience_derivation():
    a = profile_audiences(P(applying_for="child", age=10, is_student="yes", disability_status="yes",
                            guardian_has_disability=True))
    assert {"child", "student", "person_with_disability", "family_of_person_with_disability"} <= a
    assert profile_audiences(P(age=65)) == {"senior_citizen"}
    assert profile_audiences(P()) == set()


# ---- API -----------------------------------------------------------------------------------
def test_recommendations_endpoint_and_nothing_persisted(client, seeded):
    from app.models import ApplicantProfile as Stored

    r = client.post("/api/recommendations", json={"profile": {"age": 14, "state": "Tamil Nadu",
                    "disability_status": "yes", "disability_percentage": 45}})
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 20 and "not an application" in body["disclaimer"]
    assert seeded.query(Stored).count() == 0


def test_recommendations_validates_profile(client, seeded):
    assert client.post("/api/recommendations", json={"profile": {"age": -3}}).status_code == 422
    assert client.post("/api/recommendations", json={}).status_code == 422


def test_scheme_list_filters_and_pagination(client, seeded):
    r = client.get("/api/schemes", params={"jurisdiction": "tamil_nadu"})
    assert r.json()["total"] == 5
    r = client.get("/api/schemes", params={"page_size": 7, "page": 3})
    assert len(r.json()["items"]) == 6 and r.json()["total"] == 20
    r = client.get("/api/schemes", params={"q": "scholarship", "jurisdiction": "central"})
    assert r.json()["total"] >= 3
    r = client.get("/api/schemes", params={"beneficiary_type": "senior_citizen"})
    assert {s["id"] for s in r.json()["items"]} == {"ignoa-ps", "pm-jay"}
    assert client.get("/api/schemes", params={"jurisdiction": "mars"}).status_code == 422
    assert client.get("/api/schemes", params={"page_size": 1000}).status_code == 422


def test_scheme_detail_includes_rules_and_sources(client, seeded):
    r = client.get("/api/schemes/pre-matric-swd")
    assert r.status_code == 200
    body = r.json()
    assert any(x["key"] == "income_ceiling" and x["value"] == 250000 for x in body["rules"])
    assert body["sources"] and body["verification_status"] == "verified"
    assert client.get("/api/schemes/does-not-exist").status_code == 404
