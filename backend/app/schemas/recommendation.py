from datetime import date

from pydantic import BaseModel, Field

from app.schemas.profile import ApplicantProfile


class RecommendationCard(BaseModel):
    scheme_id: str
    name: str
    name_ta: str | None = None
    jurisdiction: str  # central | tamil_nadu
    jurisdiction_label: str
    category: str
    status: str  # potentially_eligible | more_information_required | does_not_match | information_unverified
    why_relevant: list[str]
    reasons: list[str]
    missing_fields: list[str]
    benefits: str | None
    required_documents: list[str]
    application_steps: list[str]
    official_url: str | None
    application_url: str | None
    last_verified: date | None
    verification_status: str
    accepting_applications: bool | None
    limitations: list[str]
    score: float
    show_by_default: bool


class RecommendationRequest(BaseModel):
    profile: ApplicantProfile


class RecommendationResponse(BaseModel):
    results: list[RecommendationCard]
    counts: dict[str, int]
    disclaimer: str = Field(
        default="Preliminary guidance only. This is not an application, a guarantee of "
        "eligibility, or an official decision. Confirm every detail with the official source."
    )


class SchemeSummary(BaseModel):
    id: str
    name: str
    name_ta: str | None
    jurisdiction: str
    applicable_state: str
    category: str
    beneficiary_types: list[str]
    summary: str
    verification_status: str
    operational_status: str
    is_cash_benefit: bool
    date_checked: date | None
    official_url: str | None


class RuleOut(BaseModel):
    key: str
    field: str
    operator: str
    value: object
    mandatory: bool
    verified: bool
    description: str


class SourceOut(BaseModel):
    url: str
    title: str | None
    source_type: str
    verification_status: str
    date_checked: date | None


class SchemeDetail(SchemeSummary):
    benefits: str | None
    required_documents: list[str]
    application_steps: list[str]
    application_url: str | None
    accepting_applications: bool | None
    verification_notes: str | None
    rules: list[RuleOut]
    sources: list[SourceOut]


class SchemePage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SchemeSummary]
