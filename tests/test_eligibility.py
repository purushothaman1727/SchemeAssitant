import ast
from pathlib import Path

import pytest

from app.eligibility.engine import (
    MORE_INFO, NO_MATCH, POTENTIALLY_ELIGIBLE, UNVERIFIED, evaluate_all, evaluate_scheme,
)
from app.eligibility.specs import RuleSpec, SchemeSpec, spec_from_dict
from app.schemas.profile import ApplicantProfile
from app.services.seed import load_dataset

SPECS = {s["id"]: spec_from_dict(s) for s in load_dataset()["schemes"]}


def P(**kw) -> ApplicantProfile:
    return ApplicantProfile(**kw)


def status(scheme_id, profile):
    return evaluate_scheme(SPECS[scheme_id], profile).status


# Synthetic profile: child with a 40% disability studying in class IX, Tamil Nadu.
def child_pre_matric(**over):
    base = dict(applying_for="child", age=14, state="Tamil Nadu", annual_family_income=250000,
                education_level="class_9_10", is_student="yes", disability_status="yes",
                disability_type="locomotor", certificate_status="udid", disability_percentage=40)
    base.update(over)
    return P(**base)


# ---- boundaries ----------------------------------------------------------------------
def test_pre_matric_boundary_values_are_inclusive():
    assert status("pre-matric-swd", child_pre_matric()) == POTENTIALLY_ELIGIBLE


@pytest.mark.parametrize("over", [
    {"annual_family_income": 250001},
    {"disability_percentage": 39},
    {"education_level": "undergraduate"},
    {"disability_status": "no"},
])
def test_pre_matric_just_outside_boundary(over):
    assert status("pre-matric-swd", child_pre_matric(**over)) == NO_MATCH


def test_top_class_income_ceiling_is_8_lakh():
    base = dict(age=22, state="Kerala", education_level="postgraduate", disability_status="yes",
                disability_percentage=60, studying_in_notified_institute=True)
    assert status("top-class-swd", P(annual_family_income=800000, **base)) == POTENTIALLY_ELIGIBLE
    assert status("top-class-swd", P(annual_family_income=800001, **base)) == NO_MATCH


# ---- unknown / incomplete ------------------------------------------------------------
def test_missing_percentage_requests_more_information_not_rejection():
    ev = evaluate_scheme(SPECS["pre-matric-swd"], child_pre_matric(disability_percentage=None))
    assert ev.status == MORE_INFO
    assert "disability_percentage" in ev.missing_fields


def test_empty_profile_is_never_rejected_for_missing_data():
    ev = evaluate_scheme(SPECS["post-matric-swd"], P())
    assert ev.status == MORE_INFO
    assert {"annual_family_income", "education_level"} <= set(ev.missing_fields)


def test_prefer_not_to_say_is_not_treated_as_no_disability():
    ev = evaluate_scheme(SPECS["pre-matric-swd"], child_pre_matric(disability_status="prefer_not_to_say"))
    assert ev.status == MORE_INFO


def test_prefer_not_to_say_still_matches_udid_information():
    assert status("udid", P(disability_status="prefer_not_to_say")) == POTENTIALLY_ELIGIBLE


def test_no_disability_does_not_match_disability_schemes():
    assert status("udid", P(disability_status="no")) == NO_MATCH
    assert status("tn-travel-concession", P(state="Tamil Nadu", disability_status="no")) == NO_MATCH


def test_disability_details_dropped_when_not_yes():
    p = P(disability_status="no", disability_percentage=80, disability_type="visual")
    assert p.disability_percentage is None and p.disability_type is None


# ---- state restrictions --------------------------------------------------------------
def test_tamil_nadu_scheme_rejects_other_state():
    p = P(state="Karnataka", disability_status="yes", disability_percentage=50)
    assert status("tn-maintenance-allowance", p) == NO_MATCH


def test_state_match_is_case_and_space_insensitive():
    p = P(state="  tamil   nadu ", disability_status="yes", disability_percentage=80)
    assert status("tn-maintenance-allowance", p) == POTENTIALLY_ELIGIBLE


# ---- composite categories (TN maintenance allowance, Policy Note Table 9) ------------------
def maint(**kw):
    base = dict(state="Tamil Nadu", disability_status="yes")
    base.update(kw)
    return evaluate_scheme(SPECS["tn-maintenance-allowance"], P(**base))


def test_maintenance_severe_75_percent_qualifies_for_any_type():
    assert maint(disability_percentage=75, disability_type="locomotor").status == POTENTIALLY_ELIGIBLE
    assert maint(disability_percentage=74, disability_type="locomotor",
                 has_listed_chronic_condition=False).status == NO_MATCH


def test_maintenance_intellectual_disability_needs_40_percent():
    assert maint(disability_percentage=40, disability_type="intellectual").status == POTENTIALLY_ELIGIBLE
    assert maint(disability_percentage=39, disability_type="intellectual",
                 has_listed_chronic_condition=False).status == NO_MATCH


def test_maintenance_listed_condition_at_40_percent_qualifies():
    assert maint(disability_percentage=40, disability_type="locomotor",
                 has_listed_chronic_condition=True).status == POTENTIALLY_ELIGIBLE


def test_maintenance_50_percent_locomotor_is_not_assumed_eligible():
    ev = maint(disability_percentage=50, disability_type="locomotor")
    assert ev.status == MORE_INFO
    assert ev.missing_fields == ["has_listed_chronic_condition"]
    assert maint(disability_percentage=50, disability_type="locomotor",
                 has_listed_chronic_condition=False).status == NO_MATCH


def test_free_coaching_explains_its_purpose_even_when_eligible():
    ev = evaluate_scheme(SPECS["free-coaching-swd"], P(applying_for="child", age=14, state="Kerala",
                         annual_family_income=100000, disability_status="yes", disability_percentage=50))
    assert ev.status == POTENTIALLY_ELIGIBLE
    assert any(r.startswith("Note:") and "competitive" in r for r in ev.reasons)


def test_unknown_state_asks_for_it():
    ev = evaluate_scheme(SPECS["tn-travel-concession"], P(disability_status="yes"))
    assert ev.status == MORE_INFO and "state" in ev.missing_fields


def test_tn_unemployment_needs_registration_fact():
    ev = evaluate_scheme(SPECS["tn-unemployment-allowance"], P(state="Tamil Nadu", disability_status="yes"))
    assert ev.status == MORE_INFO
    assert "registered_unemployed_over_1_year" in ev.missing_fields


# ---- unverified / missing rules ------------------------------------------------------
@pytest.mark.parametrize("sid", ["ignd-ps", "ignoa-ps", "ignw-ps", "pm-jay"])
def test_unverified_schemes_never_claim_eligibility_or_rejection(sid):
    p = P(age=70, state="Tamil Nadu", disability_status="no", is_bpl=True, is_widow=True)
    assert status(sid, p) == UNVERIFIED


@pytest.mark.parametrize("sid", ["adip", "national-fund-pwd"])
def test_schemes_without_rules_are_unverified(sid):
    assert SPECS[sid].rules == []
    assert status(sid, P(disability_status="yes", disability_percentage=80)) == UNVERIFIED


def test_unverified_failing_rule_does_not_reject():
    spec = SchemeSpec(id="x", verification_status="partially_verified", rules=[
        RuleSpec("age", "age", "gte", 60, verified=False, description="age 60+")])
    assert evaluate_scheme(spec, P(age=30)).status == UNVERIFIED


def test_discontinued_scheme_is_not_recommended():
    spec = SchemeSpec(id="old", operational_status="discontinued", rules=[
        RuleSpec("a", "age", "gte", 1, verified=True)])
    assert evaluate_scheme(spec, P(age=30)).status == UNVERIFIED


def test_organisation_only_schemes_do_not_match_individuals():
    assert status("sipda", P(disability_status="yes")) == NO_MATCH
    assert status("ddrs", P(disability_status="yes")) == NO_MATCH


# ---- operator boundaries on a synthetic verified spec ----------------------------------
@pytest.mark.parametrize("age,expected", [(17, NO_MATCH), (18, POTENTIALLY_ELIGIBLE),
                                          (40, POTENTIALLY_ELIGIBLE), (41, NO_MATCH)])
def test_between_operator_is_inclusive(age, expected):
    spec = SchemeSpec(id="b", rules=[RuleSpec("age", "age", "between", [18, 40], verified=True,
                                              description="age 18-40")])
    assert evaluate_scheme(spec, P(age=age)).status == expected


# ---- whole dataset -----------------------------------------------------------------------
def test_every_scheme_gets_a_valid_status_with_a_reason():
    valid = {POTENTIALLY_ELIGIBLE, MORE_INFO, NO_MATCH, UNVERIFIED}
    for profile in (P(), child_pre_matric(), P(age=65, state="Tamil Nadu", disability_status="no")):
        results = evaluate_all(SPECS.values(), profile)
        assert len(results) == 20
        assert all(r.status in valid and r.reasons for r in results)


def test_adult_without_disability_has_no_scheme_eligible():
    results = evaluate_all(SPECS.values(), P(age=30, state="Tamil Nadu", disability_status="no"))
    assert {r.scheme_id for r in results if r.status == POTENTIALLY_ELIGIBLE} == set()


def test_engine_has_no_llm_or_network_imports():
    src = Path(__file__).parents[1] / "backend" / "app" / "eligibility" / "engine.py"
    imported = set()
    for node in ast.walk(ast.parse(src.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imported |= {n.name.split(".")[0] for n in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert not imported & {"httpx", "requests", "openai", "groq", "app", "chromadb"}


def test_unverified_reason_text_has_clean_punctuation():
    ev = evaluate_scheme(SPECS["pm-kmy"], P(age=30))
    text = " ".join(ev.reasons)
    assert ".;" not in text and ".." not in text
