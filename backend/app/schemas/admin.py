from datetime import date, datetime
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.profile import ApplicantProfile

OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")
OPERATORS = {"eq", "gte", "lte", "between", "in", "is_true", "any_of", "all_of"}
PROFILE_FIELDS = set(ApplicantProfile.model_fields)


def _official_https(url: str | None) -> str | None:
    if url is None:
        return None
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not host.endswith(OFFICIAL_SUFFIXES):
        raise ValueError("must be an https URL on an official .gov.in or .nic.in host")
    return url


def _check_condition(field: str, op: str, value: Any) -> None:
    if op not in OPERATORS:
        raise ValueError(f"unknown operator '{op}'")
    if op in ("any_of", "all_of"):
        if not isinstance(value, list) or not value:
            raise ValueError(f"{op} needs a non-empty list of conditions")
        for c in value:
            if not isinstance(c, dict) or "operator" not in c or "value" not in c:
                raise ValueError("each sub-condition needs 'operator' and 'value'")
            _check_condition(c.get("field", ""), c["operator"], c["value"])
        return
    if field not in PROFILE_FIELDS:
        raise ValueError(f"'{field}' is not a profile field; the rule could never be evaluated")
    if op == "between" and not (isinstance(value, list) and len(value) == 2):
        raise ValueError("between needs [low, high]")
    if op == "in" and not isinstance(value, list):
        raise ValueError("in needs a list")


class RuleIn(BaseModel):
    key: str = Field(pattern=r"^[a-z0-9_]{2,80}$")
    field: str = Field(max_length=80)
    operator: str
    value: Any
    mandatory: bool = True
    verified: bool = False
    description: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def _valid(self):
        _check_condition(self.field, self.operator, self.value)
        return self


class SourceIn(BaseModel):
    url: str
    title: str | None = Field(default=None, max_length=300)
    source_type: Literal["portal", "page", "guideline_pdf", "circular", "policy_note"] = "page"
    verification_status: Literal["verified", "partially_verified", "unverified"] = "unverified"

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        return _official_https(v)  # type: ignore[return-value]


class SchemeBase(BaseModel):
    name: str = Field(min_length=3, max_length=300)
    name_ta: str | None = Field(default=None, max_length=400)
    jurisdiction: Literal["central", "tamil_nadu"]
    applicable_state: str = Field(default="ALL", max_length=80)
    category: str = Field(min_length=2, max_length=60)
    beneficiary_types: list[str] = []
    summary: str = Field(default="", max_length=4000)
    benefits: str | None = Field(default=None, max_length=4000)
    required_documents: list[str] = []
    application_steps: list[str] = []
    official_url: str | None = None
    application_url: str | None = None
    operational_status: Literal["active", "discontinued", "renamed", "unverified"] = "unverified"
    accepting_applications: bool | None = None
    is_cash_benefit: bool = True
    verification_status: Literal["verified", "partially_verified", "unverified"] = "unverified"
    date_checked: date | None = None
    verification_notes: str | None = Field(default=None, max_length=4000)

    @field_validator("official_url", "application_url")
    @classmethod
    def _urls(cls, v):
        return _official_https(v)


class SchemeCreate(SchemeBase):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,79}$")
    rules: list[RuleIn] = []
    sources: list[SourceIn] = []

    @model_validator(mode="after")
    def _verified_rules_need_verified_scheme(self):
        if any(r.verified for r in self.rules) and (
                self.verification_status == "unverified" or self.date_checked is None):
            raise ValueError("verified rules require verification_status != 'unverified' and date_checked")
        if self.accepting_applications is True and self.date_checked is None:
            raise ValueError("accepting_applications=true requires date_checked")
        return self


class SchemeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=300)
    name_ta: str | None = Field(default=None, max_length=400)
    applicable_state: str | None = Field(default=None, max_length=80)
    category: str | None = Field(default=None, max_length=60)
    beneficiary_types: list[str] | None = None
    summary: str | None = Field(default=None, max_length=4000)
    benefits: str | None = Field(default=None, max_length=4000)
    required_documents: list[str] | None = None
    application_steps: list[str] | None = None
    official_url: str | None = None
    application_url: str | None = None
    operational_status: Literal["active", "discontinued", "renamed", "unverified"] | None = None
    accepting_applications: bool | None = None
    is_cash_benefit: bool | None = None
    verification_status: Literal["verified", "partially_verified", "unverified"] | None = None
    date_checked: date | None = None
    verification_notes: str | None = Field(default=None, max_length=4000)
    rules: list[RuleIn] | None = None
    sources: list[SourceIn] | None = None

    @field_validator("official_url", "application_url")
    @classmethod
    def _urls(cls, v):
        return _official_https(v)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class IngestRequest(BaseModel):
    scheme_id: str | None = Field(default=None, max_length=80)


class IngestStarted(BaseModel):
    job_id: int
    status: str


class IngestionJobOut(BaseModel):
    id: int
    scheme_id: str | None
    status: str
    documents_ok: int
    documents_failed: int
    errors: list[str]
    started_at: datetime
    finished_at: datetime | None


class SourceAdminOut(BaseModel):
    id: int
    scheme_id: str
    url: str
    title: str | None
    source_type: str
    verification_status: str
    date_checked: date | None
    notes: str | None
    documents_ok: int
    documents_failed: int
    last_error: str | None


class SourcePage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SourceAdminOut]
