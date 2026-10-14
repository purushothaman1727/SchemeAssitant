from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.profile import ApplicantProfile

router = APIRouter()


class ProfileValidationResponse(BaseModel):
    valid: bool
    profile: ApplicantProfile
    notes: list[str]


@router.post("/profile/validate", response_model=ProfileValidationResponse)
def validate_profile(profile: ApplicantProfile) -> ProfileValidationResponse:
    """Validate and normalise a profile. Nothing is stored."""
    notes: list[str] = []
    if profile.age is None:
        notes.append("Age not provided; age-based schemes cannot be assessed.")
    if profile.state is None:
        notes.append("State not provided; state-specific schemes cannot be assessed.")
    if profile.disability_status == "prefer_not_to_say":
        notes.append("Disability status not disclosed; disability-specific schemes will need more information.")
    if profile.applying_for == "child" and profile.age is not None and profile.age >= 18:
        notes.append("Applying for a child but the age given is 18 or above; please check.")
    return ProfileValidationResponse(valid=True, profile=profile, notes=notes)
