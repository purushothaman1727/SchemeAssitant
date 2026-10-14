from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Scheme(TimestampMixin, Base):
    __tablename__ = "schemes"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)  # stable slug
    name: Mapped[str] = mapped_column(String(300))
    name_ta: Mapped[str | None] = mapped_column(String(400))
    jurisdiction: Mapped[str] = mapped_column(String(20))  # central | tamil_nadu
    applicable_state: Mapped[str] = mapped_column(String(80), default="ALL")
    category: Mapped[str] = mapped_column(String(60))  # scholarship, pension, ...
    beneficiary_types: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text, default="")
    benefits: Mapped[str | None] = mapped_column(Text)  # only if verified
    required_documents: Mapped[list] = mapped_column(JSON, default=list)
    application_steps: Mapped[list] = mapped_column(JSON, default=list)
    official_url: Mapped[str | None] = mapped_column(String(600))
    application_url: Mapped[str | None] = mapped_column(String(600))
    operational_status: Mapped[str] = mapped_column(String(30), default="unverified")
    # active | discontinued | renamed | unverified
    accepting_applications: Mapped[bool | None] = mapped_column(Boolean)  # None = unknown
    is_cash_benefit: Mapped[bool] = mapped_column(Boolean, default=True)
    verification_status: Mapped[str] = mapped_column(String(30), default="unverified")
    # verified | partially_verified | unverified
    date_checked: Mapped[date | None] = mapped_column(Date)
    verification_notes: Mapped[str | None] = mapped_column(Text)

    rules: Mapped[list["EligibilityRule"]] = relationship(
        back_populates="scheme", cascade="all, delete-orphan"
    )
    sources: Mapped[list["SchemeSource"]] = relationship(
        back_populates="scheme", cascade="all, delete-orphan"
    )
    documents: Mapped[list["SchemeDocument"]] = relationship(
        back_populates="scheme", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_schemes_jurisdiction", "jurisdiction"),
        Index("ix_schemes_category", "category"),
    )


class EligibilityRule(TimestampMixin, Base):
    __tablename__ = "eligibility_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scheme_id: Mapped[str] = mapped_column(ForeignKey("schemes.id", ondelete="CASCADE"))
    rule_key: Mapped[str] = mapped_column(String(80))
    field: Mapped[str] = mapped_column(String(80))
    operator: Mapped[str] = mapped_column(String(20))  # gte lte eq in is_true ...
    value: Mapped[object] = mapped_column(JSON)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str | None] = mapped_column(String(600))

    scheme: Mapped[Scheme] = relationship(back_populates="rules")

    __table_args__ = (UniqueConstraint("scheme_id", "rule_key", name="uq_rule_scheme_key"),)


class SchemeSource(TimestampMixin, Base):
    __tablename__ = "scheme_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scheme_id: Mapped[str] = mapped_column(ForeignKey("schemes.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(600))
    title: Mapped[str | None] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(30))  # portal | guideline_pdf | circular | page
    applicable_state: Mapped[str] = mapped_column(String(80), default="ALL")
    verification_status: Mapped[str] = mapped_column(String(30), default="unverified")
    http_status: Mapped[int | None] = mapped_column(Integer)
    date_checked: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    scheme: Mapped[Scheme] = relationship(back_populates="sources")

    __table_args__ = (UniqueConstraint("scheme_id", "url", name="uq_source_scheme_url"),)


class SchemeDocument(TimestampMixin, Base):
    __tablename__ = "scheme_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scheme_id: Mapped[str] = mapped_column(ForeignKey("schemes.id", ondelete="CASCADE"))
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("scheme_sources.id", ondelete="SET NULL")
    )
    title: Mapped[str | None] = mapped_column(String(300))
    local_path: Mapped[str | None] = mapped_column(String(600))
    content_hash: Mapped[str] = mapped_column(String(64))
    page_count: Mapped[int | None] = mapped_column(Integer)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    published_date: Mapped[date | None] = mapped_column(Date)
    verified_date: Mapped[date | None] = mapped_column(Date)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_outdated: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="ok")  # ok | failed
    error: Mapped[str | None] = mapped_column(Text)

    scheme: Mapped[Scheme] = relationship(back_populates="documents")

    __table_args__ = (
        UniqueConstraint("scheme_id", "content_hash", name="uq_doc_scheme_hash"),
        Index("ix_scheme_documents_scheme", "scheme_id"),
    )
