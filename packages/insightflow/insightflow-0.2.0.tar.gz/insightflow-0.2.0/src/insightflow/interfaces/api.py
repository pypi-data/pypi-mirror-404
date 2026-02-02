"""FastAPI-based Web API interface.

Exposes insightflow core functions (research, aspects, search, compose)
via HTTP endpoints. Provides OpenAPI documentation via Swagger UI.

Demo implementation scope: No authentication, authorization, or rate limiting.
"""

import logging
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from insightflow import __version__
from insightflow.core.compose import compose
from insightflow.core.generate_queries import generate_queries
from insightflow.core.prompts import build_aspect_prompt
from insightflow.core.research import research
from insightflow.core.search import search
from insightflow.models import (
    SUPPORTED_PREFIXES,
    ResearchQueries,
    LLMConfig,
    ReasoningEffort,
    Report,
    SearchContextSize,
)
from insightflow.settings import InsightFlowSettings

logger = logging.getLogger(__name__)


# ============================================================
# Task 1.1: Settings
# ============================================================


class ApiSettings(BaseSettings):
    """API-specific settings loaded from environment variables.

    Optional with defaults:
        host: Server host (HOST, default: 0.0.0.0)
        port: Server port (PORT, default: 8000)
    """

    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# ============================================================
# Task 2.1: Request Models
# ============================================================


def _validate_model_prefix(v: str | None) -> str | None:
    """Validate model ID prefix if provided."""
    if v is not None and not any(v.startswith(p) for p in SUPPORTED_PREFIXES):
        raise ValueError(
            f"Unsupported model prefix. Must start with one of: {SUPPORTED_PREFIXES}"
        )
    return v


class AspectsRequest(BaseModel):
    """Request model for POST /aspects endpoint."""

    topic: Annotated[str, Field(min_length=1, description="Research topic")]
    model: str | None = Field(default=None, description="OpenRouter model ID")
    temperature: float | None = Field(
        default=None, ge=0, le=2, description="Generation temperature"
    )
    max_tokens: int | None = Field(
        default=None, gt=0, description="Maximum generation tokens"
    )
    reasoning_effort: ReasoningEffort | None = Field(
        default=None, description="Reasoning effort level"
    )
    language: str = Field(default="japanese", description="Output language")
    max_aspects: int = Field(default=5, ge=1, description="Maximum aspects to extract")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str | None) -> str | None:
        return _validate_model_prefix(v)


class SearchRequest(BaseModel):
    """Request model for POST /search endpoint."""

    query: Annotated[str, Field(min_length=1, description="Search query")]
    model: str | None = Field(default=None, description="OpenRouter model ID")
    temperature: float | None = Field(
        default=None, ge=0, le=2, description="Generation temperature"
    )
    max_tokens: int | None = Field(
        default=None, gt=0, description="Maximum generation tokens"
    )
    reasoning_effort: ReasoningEffort | None = Field(
        default=None, description="Reasoning effort level"
    )
    search_context_size: SearchContextSize | None = Field(
        default=None, description="Search context size (low/medium/high)"
    )
    language: str = Field(default="japanese", description="Output language")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str | None) -> str | None:
        return _validate_model_prefix(v)


class ComposeRequest(BaseModel):
    """Request model for POST /compose endpoint."""

    topic: Annotated[str, Field(min_length=1, description="Research topic")]
    reports: Annotated[
        list[Report], Field(min_length=1, description="Reports to compose")
    ]
    model: str | None = Field(default=None, description="OpenRouter model ID")
    temperature: float | None = Field(
        default=None, ge=0, le=2, description="Generation temperature"
    )
    max_tokens: int | None = Field(
        default=None, gt=0, description="Maximum generation tokens"
    )
    reasoning_effort: ReasoningEffort | None = Field(
        default=None, description="Reasoning effort level"
    )
    language: str = Field(default="japanese", description="Output language")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str | None) -> str | None:
        return _validate_model_prefix(v)


class ResearchRequest(BaseModel):
    """Request model for POST /research endpoint."""

    topic: Annotated[str, Field(min_length=1, description="Research topic")]

    # Aspect model settings
    aspect_model: str | None = Field(default=None, description="Aspect extraction model")
    aspect_temperature: float | None = Field(
        default=None, ge=0, le=2, description="Aspect model temperature"
    )
    aspect_max_tokens: int | None = Field(
        default=None, gt=0, description="Aspect model max tokens"
    )
    aspect_reasoning_effort: ReasoningEffort | None = Field(
        default=None, description="Aspect model reasoning effort"
    )

    # Search model settings
    search_model: str | None = Field(default=None, description="Search model")
    search_temperature: float | None = Field(
        default=None, ge=0, le=2, description="Search model temperature"
    )
    search_max_tokens: int | None = Field(
        default=None, gt=0, description="Search model max tokens"
    )
    search_reasoning_effort: ReasoningEffort | None = Field(
        default=None, description="Search model reasoning effort"
    )
    search_context_size: SearchContextSize | None = Field(
        default=None, description="Search context size"
    )

    # Report model settings
    report_model: str | None = Field(default=None, description="Report generation model")
    report_temperature: float | None = Field(
        default=None, ge=0, le=2, description="Report model temperature"
    )
    report_max_tokens: int | None = Field(
        default=None, gt=0, description="Report model max tokens"
    )
    report_reasoning_effort: ReasoningEffort | None = Field(
        default=None, description="Report model reasoning effort"
    )

    # Common settings
    language: str = Field(default="japanese", description="Output language")
    max_aspects: int = Field(default=5, ge=1, description="Maximum aspects to extract")
    concurrency: int = Field(default=3, ge=1, description="Concurrent search limit")

    @field_validator("aspect_model", "search_model", "report_model")
    @classmethod
    def validate_model(cls, v: str | None) -> str | None:
        return _validate_model_prefix(v)


# ============================================================
# Task 3.1: Error Response Models
# ============================================================


class ErrorResponse(BaseModel):
    """Unified error response format."""

    detail: str = Field(description="Error description")
    error_type: str = Field(description="Error type (ValidationError, LLMError, InternalError)")
    context: dict | None = Field(default=None, description="Additional context")


# ============================================================
# LLMConfig Builder Helpers
# ============================================================


def _build_llm_config(
    default_model: str,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    reasoning_effort: ReasoningEffort | None = None,
    search_context_size: SearchContextSize | None = None,
) -> LLMConfig:
    """Build LLMConfig from request parameters with defaults.

    Args:
        default_model: Default model ID to use if model is None
        model: Optional model ID override
        temperature: Optional temperature override
        max_tokens: Optional max_tokens override
        reasoning_effort: Optional reasoning_effort override
        search_context_size: Optional search_context_size override

    Returns:
        LLMConfig: Configured LLM settings
    """
    config_kwargs: dict = {"model": model or default_model}

    if temperature is not None:
        config_kwargs["temperature"] = temperature
    if max_tokens is not None:
        config_kwargs["max_tokens"] = max_tokens
    if reasoning_effort is not None:
        config_kwargs["reasoning_effort"] = reasoning_effort
    if search_context_size is not None:
        config_kwargs["search_context_size"] = search_context_size

    return LLMConfig(**config_kwargs)


# ============================================================
# Task 1.2: FastAPI Application
# ============================================================

# Load settings (will raise ValidationError if OPENROUTER_API_KEY missing)
shared_settings = InsightFlowSettings()
api_settings = ApiSettings()

app = FastAPI(
    title="InsightFlow API",
    description="Research automation API for web content analysis and report generation",
    version=__version__,
)


# ============================================================
# Task 4: Endpoints
# ============================================================


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        {"status": "ok"} with HTTP 200
    """
    return {"status": "ok"}


@app.post("/aspects", response_model=ResearchQueries)
async def aspects_endpoint(request: AspectsRequest) -> ResearchQueries:
    """Extract research queries (key aspects) from a topic.

    Args:
        request: AspectsRequest with topic and optional model settings

    Returns:
        ResearchQueries: Extracted queries with intent classification

    Raises:
        HTTPException: 422 for validation errors, 500 for internal errors
    """
    logger.info("POST /aspects: topic=%r", request.topic)

    try:
        config = _build_llm_config(
            default_model=shared_settings.default_query_model,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            reasoning_effort=request.reasoning_effort,
        )
    except ValueError as e:
        logger.warning("LLMConfig validation failed: %s", e)
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                detail=str(e),
                error_type="ValidationError",
                context={"model": request.model},
            ).model_dump(),
        )

    try:
        system_prompt = build_aspect_prompt(request.max_aspects, request.language)
        result = await generate_queries(
            request.topic,
            api_key=shared_settings.openrouter_api_key,
            system_prompt=system_prompt,
            config=config,
            max_queries=request.max_aspects,
        )
        logger.info("POST /aspects completed: %d queries", len(result.output.queries))
        return result.output
    except Exception as e:
        logger.error("POST /aspects failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=str(e),
                error_type="InternalError",
            ).model_dump(),
        )


@app.post("/search", response_model=Report)
async def search_endpoint(request: SearchRequest) -> Report:
    """Execute a web search query.

    Args:
        request: SearchRequest with query and optional model settings

    Returns:
        Report: Search results with content, citations, and metadata

    Raises:
        HTTPException: 422 for validation errors, 500 for internal errors
    """
    logger.info("POST /search: query=%r", request.query)

    try:
        config = _build_llm_config(
            default_model=shared_settings.default_search_model,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            reasoning_effort=request.reasoning_effort,
            search_context_size=request.search_context_size,
        )
    except ValueError as e:
        logger.warning("LLMConfig validation failed: %s", e)
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                detail=str(e),
                error_type="ValidationError",
                context={"model": request.model},
            ).model_dump(),
        )

    try:
        result = await search(request.query, shared_settings.openrouter_api_key, config, request.language)
        logger.info("POST /search completed: %d citations", len(result.citations))
        return result
    except Exception as e:
        logger.error("POST /search failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=str(e),
                error_type="InternalError",
            ).model_dump(),
        )


@app.post("/compose", response_model=Report)
async def compose_endpoint(request: ComposeRequest) -> Report:
    """Compose multiple reports into a unified report.

    Args:
        request: ComposeRequest with topic, reports, and optional model settings

    Returns:
        Report: Composed report with content, citations, and metadata

    Raises:
        HTTPException: 422 for validation errors, 500 for internal errors
    """
    logger.info("POST /compose: topic=%r, reports=%d", request.topic, len(request.reports))

    try:
        config = _build_llm_config(
            default_model=shared_settings.default_report_model,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            reasoning_effort=request.reasoning_effort,
        )
    except ValueError as e:
        logger.warning("LLMConfig validation failed: %s", e)
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                detail=str(e),
                error_type="ValidationError",
                context={"model": request.model},
            ).model_dump(),
        )

    try:
        result = await compose(request.topic, request.reports, shared_settings.openrouter_api_key, config, request.language)
        logger.info("POST /compose completed: %d citations", len(result.citations))
        return result
    except Exception as e:
        logger.error("POST /compose failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=str(e),
                error_type="InternalError",
            ).model_dump(),
        )


@app.post("/research", response_model=Report)
async def research_endpoint(request: ResearchRequest) -> Report:
    """Execute a full research workflow.

    Orchestrates aspect extraction, parallel search, and report composition.

    Args:
        request: ResearchRequest with topic and optional model/parameter settings

    Returns:
        Report: Final research report with content, citations, and metadata

    Raises:
        HTTPException: 422 for validation errors, 500 for internal errors
    """
    logger.info("POST /research: topic=%r", request.topic)

    try:
        aspect_config = _build_llm_config(
            default_model=shared_settings.default_query_model,
            model=request.aspect_model,
            temperature=request.aspect_temperature,
            max_tokens=request.aspect_max_tokens,
            reasoning_effort=request.aspect_reasoning_effort,
        )
        search_config = _build_llm_config(
            default_model=shared_settings.default_search_model,
            model=request.search_model,
            temperature=request.search_temperature,
            max_tokens=request.search_max_tokens,
            reasoning_effort=request.search_reasoning_effort,
            search_context_size=request.search_context_size,
        )
        report_config = _build_llm_config(
            default_model=shared_settings.default_report_model,
            model=request.report_model,
            temperature=request.report_temperature,
            max_tokens=request.report_max_tokens,
            reasoning_effort=request.report_reasoning_effort,
        )
    except ValueError as e:
        logger.warning("LLMConfig validation failed: %s", e)
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                detail=str(e),
                error_type="ValidationError",
            ).model_dump(),
        )

    try:
        result = await research(
            topic=request.topic,
            api_key=shared_settings.openrouter_api_key,
            aspect_model=aspect_config,
            search_model=search_config,
            report_model=report_config,
            language=request.language,
            max_aspects=request.max_aspects,
            concurrency=request.concurrency,
        )
        logger.info("POST /research completed: %d citations", len(result.citations))
        return result
    except Exception as e:
        logger.error("POST /research failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                detail=str(e),
                error_type="InternalError",
            ).model_dump(),
        )


# ============================================================
# Server Entry Point
# ============================================================


def main() -> None:
    """Run the API server with uvicorn."""
    import uvicorn

    uvicorn.run(
        "insightflow.interfaces.api:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
