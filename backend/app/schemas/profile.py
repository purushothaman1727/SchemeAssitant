from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DisabilityStatus = Literal["yes", "no", "prefer_not_to_say"]
DisabilityType = Literal["locomotor", "visual", "hearing", "intellectual", "multiple", "other"]
CertificateStatus = Literal["udid", "certificate_only", "none", "unknown"]
EducationLevel = Literal[
    "below_9", "class_9_10", "class_11_12", "diploma", "undergraduate",
    "postgraduate", "doctoral", "other",
]
YesNoUnknown = Literal["yes", "no", "unknown"]


class ApplicantProfile(BaseModel):
    """Minimal, self-reported profile. Every field except disability_status may be unknown."""

    model_config = ConfigDict(extra="forbid")

    applying_for: Literal["self", "child"] = "self"
    age: int | None = Field(default=None, ge=0, le=120)
    state: str | None = Field(default=None, max_length=80)
    district: str | None = Field(default=None, max_length=80)
    annual_family_income: int | None = Field(default=None, ge=0, le=10_000_000_000)
    occupation: str | None = Field(default=None, max_length=80)
    education_level: EducationLevel | None = None
    is_student: YesNoUnknown = "unknown"

    disability_status: DisabilityStatus = "prefer_not_to_say"
    disability_type: DisabilityType | None = None
    certificate_status: CertificateStatus | None = None
    disability_percentage: int | None = Field(default=None, ge=0, le=100)

    # Scheme-specific facts; asked only when a candidate scheme needs them.
    guardian_has_disability: bool | None = None
    is_bpl: bool | None = None
    is_widow: bool | None = None
    land_holding_hectares: float | None = Field(default=None, ge=0, le=100000)
    studying_in_notified_institute: bool | None = None
    registered_unemployed_over_1_year: bool | None = None
    high_support_need_certified: bool | None = None
    has_listed_chronic_condition: bool | None = None  # Parkinson's, spinal cord injury, MS, muscular dystrophy, leprosy-cured
    applicant_is_organisation: bool = False

    @field_validator("state", "district", "occupation")
    @classmethod
    def _clean(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = " ".join(v.split())
        return v or None

    @model_validator(mode="after")
    def _disability_details_only_when_yes(self):
        if self.disability_status != "yes":
            # Do not retain medical details the user did not affirmatively provide.
            self.disability_type = None
            self.certificate_status = None
            self.disability_percentage = None
        return self
