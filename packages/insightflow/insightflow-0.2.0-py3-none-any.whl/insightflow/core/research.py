"""リサーチオーケストレーション。

key-aspects → 並列search → compose の一連のフローを協調実行し、
最終Reportを返す。interfaces層からの唯一のエントリポイント。
"""

import asyncio
import logging

from insightflow.core.compose import compose
from insightflow.core.generate_queries import generate_queries
from insightflow.core.prompts import build_aspect_prompt
from insightflow.core.search import search
from insightflow.models import LLMConfig, Report

logger = logging.getLogger(__name__)


async def research(
    topic: str,
    api_key: str,
    aspect_model: LLMConfig,
    search_model: LLMConfig,
    report_model: LLMConfig,
    language: str = "japanese",
    max_aspects: int = 5,
    concurrency: int = 3,
) -> Report:
    """リサーチオーケストレーションを実行する。

    key-aspects → 並列search → compose の順で実行し、
    最終的な統合Reportを返す。

    Args:
        topic: リサーチトピック
        api_key: OpenRouter API key (required)
        aspect_model: アスペクト抽出用LLMConfig（逐次使用、コピー不要）
        search_model: 検索用LLMConfig（並列実行前にmodel_copy()でN個の独立コピーを生成）
        report_model: レポート統合用LLMConfig（逐次使用、コピー不要）
        language: 出力言語 兼 検索スコープ指示（デフォルト: "japanese"）
        max_aspects: 生成アスペクト数上限（デフォルト: 5）
        concurrency: 並列search同時実行数上限（デフォルト: 3）

    Returns:
        Report: 統合レポート（compose出力そのまま）

    Raises:
        ValueError: max_aspects < 1 または concurrency < 1
        RuntimeError: 全searchが失敗した場合（成功0件）
        pydantic_ai例外: key-aspectsまたはcompose失敗時（そのまま伝播）
    """
    if max_aspects < 1:
        raise ValueError(f"max_aspects must be >= 1, got {max_aspects}")
    if concurrency < 1:
        raise ValueError(f"concurrency must be >= 1, got {concurrency}")

    # Step 1: key-aspects抽出
    logger.info(
        "Key-aspects extraction starting: topic=%r, model=%s, max_aspects=%d",
        topic,
        aspect_model.model,
        max_aspects,
    )
    try:
        system_prompt = build_aspect_prompt(max_aspects)
        aspects_result = await generate_queries(
            topic,
            api_key=api_key,
            system_prompt=system_prompt,
            config=aspect_model,
            max_queries=max_aspects,
        )
    except Exception:
        logger.error("Key-aspects extraction failed", exc_info=True)
        raise
    queries = aspects_result.output.queries
    logger.info(
        "Key-aspects extraction completed: %d queries", len(queries)
    )

    # Step 2: 並列search
    semaphore = asyncio.Semaphore(concurrency)
    logger.info(
        "Parallel search starting: %d queries, concurrency=%d",
        len(queries),
        concurrency,
    )

    async def _run_search(query_str: str, config: LLMConfig) -> Report:
        async with semaphore:
            return await search(query_str, api_key, config, language)

    search_configs = [search_model.model_copy() for _ in queries]
    tasks = [
        _run_search(query.text, config)
        for query, config in zip(queries, search_configs, strict=True)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 成功/失敗の分類
    successful_reports: list[Report] = []
    failed_queries: list[str] = []
    for query, result in zip(queries, results, strict=True):
        if isinstance(result, BaseException):
            failed_queries.append(query.text)
        else:
            successful_reports.append(result)

    success_count = len(successful_reports)
    total = len(queries)

    if success_count == 0:
        logger.error(
            "All searches failed: 0/%d succeeded",
            total,
        )
        raise RuntimeError(f"All searches failed: 0/{total} succeeded")

    if failed_queries:
        logger.warning(
            "Search partial failure: %d/%d succeeded, failed=[%s]",
            success_count,
            total,
            ", ".join(failed_queries),
        )

    logger.info("Parallel search completed: %d/%d succeeded", success_count, total)

    # Step 3: compose
    logger.info(
        "Compose starting: %d reports, model=%s",
        len(successful_reports),
        report_model.model,
    )
    try:
        final_report = await compose(topic, successful_reports, api_key, report_model, language)
    except Exception:
        logger.error("Compose failed", exc_info=True)
        raise
    logger.info("Compose completed")

    return final_report
