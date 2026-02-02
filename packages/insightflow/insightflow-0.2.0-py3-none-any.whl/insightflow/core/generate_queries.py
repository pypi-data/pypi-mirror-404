"""Generic query generation function.

Generates queries from a topic with optional context using pydantic-ai Agent.
This replaces extract_aspects and generate_gap_queries with a unified interface
where the application layer controls the system_prompt.
"""

import logging
import time
from typing import TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from insightflow.core.utils import unwrap_result, wrap_output_type
from insightflow.models import LLMConfig, Report, ResearchQueries
from insightflow.models.llm_result import LLMTaskResult, LLMUsage

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _format_reports(reports: list[Report]) -> str:
    """Format reports for inclusion in input_text.

    Args:
        reports: List of reports to format

    Returns:
        Formatted string representation of reports
    """
    parts = []
    for i, report in enumerate(reports, 1):
        parts.append(f"### Report {i}\n{report.content}\n")
    return "\n".join(parts)


def _deduplicate_queries(research_queries: ResearchQueries) -> ResearchQueries:
    """Remove duplicate queries based on exact text match.

    Args:
        research_queries: ResearchQueries before deduplication

    Returns:
        ResearchQueries with duplicates removed (preserves first occurrence)
    """
    seen: set[str] = set()
    unique = []
    for query in research_queries.queries:
        if query.text not in seen:
            seen.add(query.text)
            unique.append(query)
    return ResearchQueries(queries=unique)


async def generate_queries(
    topic: str,
    context: list[Report] | None = None,
    *,
    api_key: str,
    system_prompt: str,
    output_type: type[T] = ResearchQueries,
    config: LLMConfig,
    max_queries: int = 5,
    deduplicate: bool = True,
) -> LLMTaskResult[T]:
    """Generate queries from topic with optional context.

    What queries are generated is determined by system_prompt.
    Language, intent classification, etc. should be included in
    system_prompt by the application layer.

    Unlike search/compose, this function does NOT use instructions.
    The entire prompt context is controlled via system_prompt.

    Args:
        topic: Research topic (required, non-empty)
        context: Optional list of existing reports for context
        api_key: OpenRouter API key (required)
        system_prompt: Task-specific system prompt (required, non-empty)
        output_type: Pydantic model type for structured output
        config: LLM configuration (required)
        max_queries: Maximum queries to generate (default: 5)
        deduplicate: Whether to deduplicate ResearchQueries output

    Returns:
        LLMTaskResult containing output, elapsed_sec, and usage

    Raises:
        ValueError: If topic or system_prompt is empty/whitespace
        pydantic_ai exceptions: On LLM call failure
    """
    if not topic.strip():
        raise ValueError("topic must not be empty")

    if not system_prompt.strip():
        raise ValueError("system_prompt must not be empty")

    if max_queries < 1:
        raise ValueError("max_queries must be >= 1")

    # Build input_text
    if context is None:
        input_text = topic
    else:
        formatted_reports = _format_reports(context)
        input_text = f"# Topic\n{topic}\n\n# Context\n{formatted_reports}"

    logger.info(
        "Query generation started: topic=%r, context=%s, model=%s, max_queries=%d",
        topic,
        "yes" if context else "no",
        config.model,
        max_queries,
    )

    try:
        wrapped_type = wrap_output_type(output_type, config)

        provider = OpenRouterProvider(api_key=api_key)
        agent: Agent = Agent(
            OpenRouterModel(config.model, provider=provider),
            output_type=wrapped_type,
            system_prompt=system_prompt,
            model_settings=config.to_model_settings(),
            retries=3,
        )

        start = time.perf_counter()
        result = await agent.run(input_text)
        elapsed_sec = time.perf_counter() - start

        output = unwrap_result(result)
        run_usage = result.usage()

        usage = LLMUsage(
            requests=run_usage.requests,
            input_tokens=run_usage.input_tokens,
            output_tokens=run_usage.output_tokens,
        )

        # Deduplicate if enabled and output is ResearchQueries
        if deduplicate and isinstance(output, ResearchQueries):
            output = _deduplicate_queries(output)

        logger.info(
            "Query generation completed: queries=%s, elapsed_sec=%.2f",
            len(output.queries) if isinstance(output, ResearchQueries) else "N/A",
            elapsed_sec,
        )

        return LLMTaskResult(
            output=output,
            elapsed_sec=elapsed_sec,
            usage=usage,
        )

    except Exception:
        logger.error(
            "Query generation failed: topic=%r, model=%s",
            topic,
            config.model,
            exc_info=True,
        )
        raise
