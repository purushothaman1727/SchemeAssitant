import json
from pathlib import Path

import pytest

from app.schemas.profile import ApplicantProfile
from app.services.recommendation import recommend
from app.services.seed import seed_schemes

PATH = Path(__file__).parents[1] / "data" / "sample_profiles.json"
PROFILES = json.loads(PATH.read_text(encoding="utf-8"))["profiles"]


@pytest.mark.parametrize("sample", PROFILES, ids=lambda s: s["id"])
def test_sample_profile_expectations(db, sample):
    seed_schemes(db)
    resp = recommend(db, ApplicantProfile(**sample["profile"]))
    got = {c.scheme_id: c.status for c in resp.results}
    for scheme_id, expected in sample["expect"].items():
        assert got[scheme_id] == expected, f"{sample['id']}: {scheme_id} was {got[scheme_id]}"


def test_sample_profiles_are_valid_and_unique():
    ids = [p["id"] for p in PROFILES]
    assert len(ids) == len(set(ids))
    for p in PROFILES:
        ApplicantProfile(**p["profile"])  # raises if the sample is malformed
