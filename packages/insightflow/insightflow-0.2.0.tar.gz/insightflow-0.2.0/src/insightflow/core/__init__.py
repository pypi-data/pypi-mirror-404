"""InsightFlow core package.

Public API exports for core-layer functions.
"""

from insightflow.core.compose import compose
from insightflow.core.generate_queries import generate_queries
from insightflow.core.prompts import build_aspect_prompt, build_gap_prompt
from insightflow.core.research import research
from insightflow.core.search import search
from insightflow.core.utils import (
    build_runtime_context,
    merge_citations,
    normalize_url,
    unwrap_result,
    validate_citation_url,
    wrap_output_type,
)

__all__ = [
    "build_aspect_prompt",
    "build_gap_prompt",
    "build_runtime_context",
    "compose",
    "generate_queries",
    "merge_citations",
    "normalize_url",
    "research",
    "search",
    "unwrap_result",
    "validate_citation_url",
    "wrap_output_type",
]
