from urllib.parse import urlparse

import pytest

from app.models import EligibilityRule, Scheme, SchemeSource
from app.services.seed import load_dataset, seed_schemes

DATA = load_dataset()["schemes"]
ALLOWED_OPERATORS = {"eq", "gte", "lte", "between", "in", "is_true", "any_of", "all_of"}
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")
VERIFICATION = {"verified", "partially_verified", "unverified"}


def test_exactly_20_unique_schemes():
    ids = [s["id"] for s in DATA]
    assert len(ids) == 20
    assert len(set(ids)) == 20


def test_names_are_not_duplicated():
    names = [s["name"].lower() for s in DATA]
    assert len(set(names)) == len(names)


def test_central_and_tamil_nadu_both_present():
    juris = {s["jurisdiction"] for s in DATA}
    assert juris == {"central", "tamil_nadu"}
    assert sum(s["jurisdiction"] == "tamil_nadu" for s in DATA) == 5


@pytest.mark.parametrize("s", DATA, ids=lambda s: s["id"])
def test_scheme_record_is_complete(s):
    assert s["verification_status"] in VERIFICATION
    assert s["date_checked"]
    assert s["official_url"]
    assert s["sources"], "every scheme needs at least one recorded source"
    assert s["applicable_state"]
    assert s["verification_notes"]


@pytest.mark.parametrize("s", DATA, ids=lambda s: s["id"])
def test_urls_are_official_hosts(s):
    urls = [s["official_url"], s["application_url"]] + [x["url"] for x in s["sources"]]
    for url in filter(None, urls):
        host = urlparse(url).hostname or ""
        assert host.endswith(OFFICIAL_SUFFIXES), f"{url} is not an official .gov.in/.nic.in host"


@pytest.mark.parametrize("s", DATA, ids=lambda s: s["id"])
def test_rules_are_well_formed_and_not_overclaimed(s):
    for r in s["rules"]:
        assert r["operator"] in ALLOWED_OPERATORS
        assert r["description"]
    if s["verification_status"] == "unverified":
        assert not any(r["verified"] for r in s["rules"]), "unverified scheme cannot hold verified rules"


def test_udid_and_sipda_are_not_cash_benefit_schemes():
    by_id = {s["id"]: s for s in DATA}
    assert by_id["udid"]["is_cash_benefit"] is False
    assert by_id["sipda"]["is_cash_benefit"] is False
    assert by_id["udid"]["benefits"] is None


def test_no_scheme_claims_to_be_accepting_applications_without_evidence():
    # Only UDID had a live portal confirmed; everything else must be unknown (None).
    claimed = [s["id"] for s in DATA if s["accepting_applications"] is True]
    assert claimed == ["udid"]


def test_seed_persists_and_is_idempotent(db):
    assert seed_schemes(db) == 20
    assert seed_schemes(db) == 20
    assert db.query(Scheme).count() == 20
    expected_rules = sum(len(s["rules"]) for s in DATA)
    assert db.query(EligibilityRule).count() == expected_rules
    assert db.query(SchemeSource).count() == sum(len(s["sources"]) for s in DATA)


def test_benefit_text_never_leaks_provenance_or_unread_amounts():
    for s in DATA:
        text = (s["benefits"] or "").lower()
        assert "search result" not in text and "aggregator" not in text, s["id"]
        if s["verification_status"] == "unverified":
            assert s["benefits"] is None, s["id"]
    pm_kmy = next(s for s in DATA if s["id"] == "pm-kmy")
    assert pm_kmy["benefits"] is None  # amount only seen via a search quote, not read in the document
