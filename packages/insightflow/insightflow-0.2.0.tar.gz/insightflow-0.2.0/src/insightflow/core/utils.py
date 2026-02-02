"""Core utility functions for InsightFlow.

Provides shared helpers used across the insightflow system:
- build_runtime_context: Generate LLM instruction context with current time
- normalize_url: NFC-normalize and canonicalize URLs
- validate_citation_url: Check URL scheme is http/https
- merge_citations: Deduplicate citations by normalized URL
- wrap_output_type: Select pydantic-ai output wrapper based on LLMConfig
- unwrap_result: Extract output from pydantic-ai RunResult
"""

import unicodedata
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

from pydantic_ai import AgentRunResult, PromptedOutput

from insightflow.models import Citation, LLMConfig


def build_runtime_context(language: str = "japanese") -> str:
    """Generate runtime context string with current datetime and response language.

    Uses local timezone via datetime.now().astimezone().

    Args:
        language: Language for the LLM to respond in. Defaults to "japanese".

    Returns:
        Instruction string containing ISO datetime and language directive.
    """
    iso_datetime = datetime.now().astimezone().isoformat()
    return f"Current date and time: {iso_datetime}. Respond in {language}."


def normalize_url(url: str) -> str:
    """Normalize a URL for deduplication.

    Applies NFC unicode normalization, lowercases scheme and host,
    strips trailing slashes from path (preserving root "/"),
    and reassembles the URL. Returns the NFC-normalized input unchanged
    if it cannot be parsed as a valid URL (no scheme or netloc).

    Never raises exceptions.

    Args:
        url: URL string to normalize.

    Returns:
        Normalized URL string, or NFC-normalized input if unparseable.
    """
    if not url:
        return ""

    nfc_url = unicodedata.normalize("NFC", url)

    try:
        parts = urlsplit(nfc_url)
    except Exception:
        return nfc_url

    if not parts.scheme or not parts.netloc:
        return nfc_url

    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    if parts.path in ("", "/"):
        path = parts.path
    else:
        path = parts.path.rstrip("/")

    return urlunsplit((scheme, netloc, path, parts.query, parts.fragment))


def validate_citation_url(url: str) -> bool:
    """Check whether a URL has an http or https scheme.

    Used as a downstream filter for display/link rendering.
    Never raises exceptions.

    Args:
        url: URL string to validate.

    Returns:
        True if scheme is http or https, False otherwise.
    """
    try:
        return urlsplit(url).scheme.lower() in ("http", "https")
    except Exception:
        return False


def merge_citations(*citation_lists: list[Citation]) -> list[Citation]:
    """Merge multiple citation lists, deduplicating by normalized URL.

    Preserves the first occurrence of each unique URL (after normalization)
    with all its original fields. Returns citations in insertion order.

    Args:
        *citation_lists: Variable number of Citation lists to merge.

    Returns:
        Deduplicated list of Citations in first-occurrence order.
    """
    seen: dict[str, Citation] = {}
    for citations in citation_lists:
        for citation in citations:
            key = normalize_url(citation.url)
            if key not in seen:
                seen[key] = citation
    return list(seen.values())


def wrap_output_type[T](
    target_type: type[T], config: LLMConfig
) -> type[T] | PromptedOutput[T]:
    """Select the appropriate pydantic-ai output wrapper based on LLMConfig.

    Args:
        target_type: The Pydantic model type for structured output.
        config: LLMConfig instance determining wrapper selection.

    Returns:
        target_type directly for "tool" wrapper, or
        PromptedOutput(target_type) for "prompted" wrapper.
    """
    if config.output_wrapper == "tool":
        return target_type
    return PromptedOutput(target_type)


def unwrap_result[T](result: AgentRunResult[T]) -> T:
    """Extract the output value from a pydantic-ai AgentRunResult.

    Args:
        result: RunResult from a pydantic-ai agent run.

    Returns:
        The output value of type T.

    Raises:
        ValueError: If result.output is None.
    """
    if result.output is None:
        raise ValueError("Agent produced no output")
    return result.output
