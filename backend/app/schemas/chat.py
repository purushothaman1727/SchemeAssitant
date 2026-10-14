from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.profile import ApplicantProfile


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    language: Literal["en", "ta", "auto"] = "auto"
    profile: ApplicantProfile | None = None
    history: list[HistoryMessage] = Field(default_factory=list, max_length=12)
    # Messages are persisted only when the user explicitly opts in.
    store_history: bool = False
    session_id: str | None = Field(default=None, max_length=36)


class Citation(BaseModel):
    ref: str  # E1 (document passage) or S1 (structured scheme record)
    title: str
    url: str | None
    page: int | None = None
    verified_date: str | None = None
    scheme_ids: list[str] = []


class ChatResponse(BaseModel):
    answer: str
    language: Literal["en", "ta"]
    citations: list[Citation]
    clarifying_questions: list[str]
    schemes_discussed: list[str]
    grounded: bool  # True only if evidence/records were available and the answer validated
    llm_used: bool
    notice: str | None = None
    session_id: str | None = None
