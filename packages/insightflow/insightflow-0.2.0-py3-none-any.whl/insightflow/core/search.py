"""Unified search function.

Executes a single-query web search via pydantic-ai Agent, applying
provider-specific system prompts, inline citation parsing, and
core-utils integration (build_runtime_context, wrap/unwrap, merge_citations).
"""

import logging
import re
import time
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from insightflow.core.utils import (
    build_runtime_context,
    merge_citations,
    normalize_url,
    unwrap_result,
    wrap_output_type,
)
from insightflow.models import (
    Citation,
    LLMConfig,
    LLMReport,
    Report,
    ReportMetadata,
)

logger = logging.getLogger(__name__)

# x-ai/モデルのインライン引用パターン: [[N]](URL)
_XAI_INLINE_PATTERN: re.Pattern[str] = re.compile(
    r"\[\[\d+\]\]\((https?://[^\s\)]+)\)"
)

# [Pending] 他モデルのパターン（実レスポンス確認後に追加）
# PERPLEXITY_INLINE_PATTERN: re.Pattern[str] = ...
# GOOGLE_INLINE_PATTERN: re.Pattern[str] = ...
# OPENAI_INLINE_PATTERN: re.Pattern[str] = ...

PROVIDER_PROMPTS: dict[str, str] = {
    "perplexity": (
        "You are a web search researcher. Conduct accurate and comprehensive "
        "research on the given query and generate a response with explicit sources.\n\n"
        "## Output Format\n"
        "- Respond in Markdown format\n"
        "- Include Citation information for sources\n"
        "- Include reference URLs in the citations field\n"
        "- Output in the language specified in runtime instructions\n\n"
        "## Multilingual Research\n"
        "- Research in BOTH the specified language AND English to gather comprehensive information\n\n"
        "## Provider-Specific\n"
        "- Leverage the built-in search capability to retrieve the latest information"
    ),
    "google": (
        "You are a web search researcher. Conduct accurate and comprehensive "
        "research on the given query and generate a response with explicit sources.\n\n"
        "## Output Format\n"
        "- Respond in Markdown format\n"
        "- Include Citation information for sources\n"
        "- Include reference URLs in the citations field\n"
        "- Output in the language specified in runtime instructions\n\n"
        "## Multilingual Research\n"
        "- Research in BOTH the specified language AND English to gather comprehensive information\n\n"
        "## Provider-Specific\n"
        "- Leverage Exa search results to gather reliable information"
    ),
    "x-ai": (
        "You are a web search researcher. Conduct accurate and comprehensive "
        "research on the given query and generate a response with explicit sources.\n\n"
        "## Output Format\n"
        "- Respond in Markdown format\n"
        "- Include Citation information for sources\n"
        "- Format inline citations in the body as [[N]](URL)\n"
        "- Also include reference URLs in the citations field\n"
        "- Output in the language specified in runtime instructions\n\n"
        "## Multilingual Research\n"
        "- Research in BOTH the specified language AND English to gather comprehensive information\n\n"
        "## Provider-Specific\n"
        "- Leverage web search capability to gather the latest and comprehensive information"
    ),
    "openai": (
        "You are a web search researcher. Conduct accurate and comprehensive "
        "research on the given query and generate a response with explicit sources.\n\n"
        "## Output Format\n"
        "- Respond in Markdown format\n"
        "- Include Citation information for sources\n"
        "- Include reference URLs in the citations field\n"
        "- Output in the language specified in runtime instructions\n\n"
        "## Multilingual Research\n"
        "- Research in BOTH the specified language AND English to gather comprehensive information\n\n"
        "## Provider-Specific\n"
        "- Leverage native search capability to retrieve accurate and up-to-date information"
    ),
    "anthropic": (
        "You are a web search researcher. Conduct accurate and comprehensive "
        "research on the given query and generate a response with explicit sources.\n\n"
        "## Output Format\n"
        "- Respond in Markdown format\n"
        "- Include Citation information for sources\n"
        "- Include reference URLs in the citations field\n"
        "- Output in the language specified in runtime instructions\n\n"
        "## Multilingual Research\n"
        "- Research in BOTH the specified language AND English to gather comprehensive information\n\n"
        "## Provider-Specific\n"
        "- Leverage web search capability to gather the latest and comprehensive information"
    ),
}


def _build_system_prompt(provider: str) -> str:
    """プロバイダに応じたsystem promptを返す。

    Args:
        provider: モデルプロバイダ名（LLMConfig.provider値）

    Returns:
        str: system prompt文字列

    Raises:
        KeyError: 未知のプロバイダ
    """
    return PROVIDER_PROMPTS[provider]


def _parse_inline_citations(
    content: str,
    provider: str,
) -> list[Citation]:
    """本文中のインライン引用をパースしCitationリストを返す。

    Args:
        content: LLM出力の本文テキスト
        provider: モデルプロバイダ名（LLMConfig.provider値）

    Returns:
        list[Citation]: パースされたCitation（URL正規化済み）。
        パース失敗時は空リスト。
    """
    if not content:
        return []

    try:
        if provider == "x-ai":
            urls = _XAI_INLINE_PATTERN.findall(content)
            return [
                Citation(url=normalize_url(url), title="", content=url)
                for url in urls
            ]
        # Pending: perplexity, google, openai (実レスポンス形式確認後にパターン追加)
        return []
    except Exception:
        logger.debug("Inline citation parse failed for provider=%s, content_length=%d", provider, len(content))
        return []


async def search(
    query: str,
    api_key: str,
    config: LLMConfig,
    language: str = "japanese",
) -> Report:
    """単一クエリのWeb検索を実行し、Reportを返す。

    pydantic-ai Agentを直接生成・実行（tech.md #6 直接使用パターン）:
    - system_prompt = _build_system_prompt(config.provider)
    - instructions = build_runtime_context(language)
    - output_type = wrap_output_type(LLMReport, config)

    Args:
        query: 検索クエリ文字列
        api_key: OpenRouter API key (required)
        config: LLM設定 (required)
        language: レスポンス言語 (default: "japanese")

    Returns:
        Report: 検索結果（content, citations, metadata）

    Raises:
        ValueError: queryが空の場合
        pydantic_ai例外: LLM呼び出し失敗時
        ValidationError: 出力バリデーション失敗時
    """
    if not query.strip():
        raise ValueError("query must not be empty")

    logger.info("Search started: query=%r, model=%s, language=%s", query, config.model, language)

    try:
        system_prompt = _build_system_prompt(config.provider)
        instructions = build_runtime_context(language)
        wrapped_type = wrap_output_type(LLMReport, config)

        provider = OpenRouterProvider(api_key=api_key)
        agent: Agent = Agent(
            OpenRouterModel(config.model, provider=provider),
            output_type=wrapped_type,
            system_prompt=system_prompt,
            model_settings=config.to_model_settings(),
            retries=3,
        )

        start = time.perf_counter()
        result = await agent.run(query, instructions=instructions)
        elapsed_sec = time.perf_counter() - start

        llm_report = unwrap_result(result)
        run_usage = result.usage()

        inline_citations = _parse_inline_citations(llm_report.content, config.provider)
        merged = merge_citations(llm_report.citations, inline_citations)

        retries = run_usage.requests - 1

        metadata = ReportMetadata(
            model=config.model,
            elapsed_sec=elapsed_sec,
            retries=retries,
            created_at=datetime.now().astimezone(),
        )

        report = Report(
            content=llm_report.content,
            citations=merged,
            metadata=metadata,
        )

        logger.info("Search completed: elapsed_sec=%.2f, citations=%d", elapsed_sec, len(merged))
        return report

    except Exception:
        # Log and re-raise without wrapping (tech.md: exception propagation strategy)
        logger.error("Search failed: query=%r, model=%s", query, config.model, exc_info=True)
        raise
