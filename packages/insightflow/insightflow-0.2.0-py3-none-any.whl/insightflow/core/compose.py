"""Report composition function.

Integrates multiple search results (Reports) into a comprehensive
report using LLM via pydantic-ai Agent direct execution.
"""

import logging
import time
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from insightflow.core.utils import (
    build_runtime_context,
    merge_citations,
    unwrap_result,
    wrap_output_type,
)
from insightflow.models import (
    LLMConfig,
    LLMReport,
    Report,
    ReportMetadata,
)

logger = logging.getLogger(__name__)


def _build_system_prompt() -> str:
    """統合レポート生成用のsystem promptを返す。

    Returns:
        str: system prompt文字列（静的、引数なし）
    """
    return (
        "You are a research synthesis expert. Integrate multiple research reports "
        "into a comprehensive and coherent report.\n\n"
        "## Task\n"
        "- Synthesize information from multiple sources meaningfully, not just concatenate\n"
        "- Identify and highlight common themes across sources\n"
        "- Clearly point out contradictions or inconsistencies between sources\n\n"
        "## Output Format\n"
        "- Respond in Markdown format\n"
        "- Organize information with logical structure (sections)\n"
        "- Prioritize important findings\n"
        "- Output in the language specified in runtime instructions"
    )


def _build_user_prompt(topic: str, reports: list[Report]) -> str:
    """topic + reportsからユーザープロンプトを構築する。

    Args:
        topic: リサーチトピック
        reports: 統合対象のReportリスト（1件以上）

    Returns:
        str: ユーザープロンプト文字列
    """
    lines = [
        f"# Topic: {topic}\n",
        f"## {len(reports)} Research Reports\n",
    ]

    for i, report in enumerate(reports, 1):
        lines.append(f"### Report {i}\n{report.content}\n")

    lines.append(
        "## Task\n"
        "Integrate the above reports into a comprehensive report. "
        "Highlight common themes and contradictions."
    )

    return "\n".join(lines)


async def compose(
    topic: str,
    reports: list[Report],
    api_key: str,
    config: LLMConfig,
    language: str = "japanese",
) -> Report:
    """複数の検索結果を統合し包括的なレポートを生成する。

    pydantic-ai Agentを直接生成・実行（tech.md #6 直接使用パターン）:
    - system_prompt = _build_system_prompt()
    - instructions = build_runtime_context(language)
    - output_type = wrap_output_type(LLMReport, config)

    Args:
        topic: リサーチトピック
        reports: 統合対象のReportリスト（1件以上）
        api_key: OpenRouter API key (required)
        config: LLM設定 (required)
        language: レスポンス言語 (default: "japanese")

    Returns:
        Report: 統合レポート（content, citations, metadata）

    Raises:
        ValueError: reportsが空の場合
        pydantic_ai例外: LLM呼び出し失敗時
        ValidationError: 出力バリデーション失敗時
    """
    if not reports:
        raise ValueError("reports must not be empty")

    input_lengths = [len(r.content) for r in reports]
    logger.info(
        "Compose started: topic=%r, model=%s, reports=%d, input_lengths=%s, language=%s",
        topic, config.model, len(reports), input_lengths, language,
    )

    try:
        system_prompt = _build_system_prompt()
        user_prompt = _build_user_prompt(topic, reports)
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
        result = await agent.run(user_prompt, instructions=instructions)
        elapsed_sec = time.perf_counter() - start

        llm_report = unwrap_result(result)
        run_usage = result.usage()

        # Citationマージ: 入力Reportsのcitationsのみをmerge
        # LLMReport.citationsは使用しない（入力Reportsのcitationsのみ）
        merged = merge_citations(*[r.citations for r in reports])

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

        logger.info("Compose completed: elapsed_sec=%.2f, citations=%d", elapsed_sec, len(merged))
        return report

    except Exception:
        # Log and re-raise without wrapping (tech.md: exception propagation strategy)
        logger.error("Compose failed: topic=%r, model=%s", topic, config.model, exc_info=True)
        raise
