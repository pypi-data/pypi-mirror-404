"""Report-related Pydantic models.

Defines the core data models for research reports:
- Citation: Reference information (URL validation is core-utils responsibility)
- ReportMetadata: Report generation metadata
- LLMReport: pydantic-ai output_type for LLM-generated content
- Report: Complete report combining LLM output with metadata
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator


class Citation(BaseModel):
    """Citation reference with minimal validation.

    Represents a source reference with URL, optional title, and content.
    URL scheme/netloc validation is NOT performed here to avoid rejecting
    entire LLM structured outputs due to a single malformed URL.
    Scheme validation is core-utils validate_citation_url's responsibility
    (downstream filter for display/link rendering).
    """

    url: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    title: str = ""
    content: Annotated[str, StringConstraints(min_length=1)]


class ReportMetadata(BaseModel):
    """Report generation metadata.

    Holds application-level information about how a report was generated,
    including the LLM model used, processing time, retry count, and
    creation timestamp. The created_at field requires timezone-aware
    datetime to ensure consistent time representation.
    """

    model: str = Field(description="使用したLLMモデルのOpenRouter ID")
    elapsed_sec: float = Field(ge=0, description="処理時間（秒）")
    retries: int = Field(ge=0, default=0, description="pydantic-ai内部リトライ回数")
    created_at: datetime = Field(description="レポート生成日時（timezone-aware必須）")

    @field_validator("created_at")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Reject naive datetime (must be timezone-aware)."""
        if v.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        return v


class LLMReport(BaseModel):
    """LLM-generated report content (pydantic-ai output_type).

    Designed to be used as the output_type for pydantic-ai Agent.
    Contains only information that the LLM can directly generate.
    Field descriptions serve as generation guidance for the LLM.
    """

    content: str = Field(description="Markdown形式のレポート本文")
    citations: list[Citation] = Field(
        default_factory=list,
        description="レポートで参照した情報源のリスト",
    )


class Report(BaseModel):
    """Complete report combining LLM output with application metadata.

    The external-facing report type used as the return value of
    search/compose functions. Combines LLM-generated content and
    citations with application-level metadata (processing time, etc.).
    """

    content: str = Field(description="Markdown形式のレポート本文")
    citations: list[Citation] = Field(
        default_factory=list,
        description="重複排除・正規化済みの引用リスト（空リスト許容）",
    )
    metadata: ReportMetadata
