"""CLI interface for insightflow.

Typer-based CLI providing subcommands for research, aspects, search, and compose.
For debugging and parameter tuning purposes.
"""

import asyncio
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from insightflow import core
from insightflow.models import ResearchQueries, LLMConfig, Report
from insightflow import __version__
from insightflow.settings import InsightFlowSettings

# Typer app
app = typer.Typer(
    name="insightflow",
    help="AI-powered research automation tool",
    add_completion=False,
)

logger = logging.getLogger(__name__)


def _setup_logging(verbose: int) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)
    """
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    # Configure root logger for insightflow
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    # Set level for insightflow loggers
    logging.getLogger("insightflow").setLevel(level)


def _check_api_key() -> None:
    """Check if OPENROUTER_API_KEY is set via pydantic-settings.

    Loads from environment variables and .env file automatically.

    Raises:
        typer.Exit: If API key is not set
    """
    try:
        InsightFlowSettings()
    except ValidationError:
        typer.echo(
            "Error: Configuration: OPENROUTER_API_KEY environment variable not set. "
            "Set it in .env or export it.",
            err=True,
        )
        raise typer.Exit(code=1)


def _write_output(
    content: str,
    output: Path | None,
) -> None:
    """Write content to stdout or file.

    Args:
        content: Content to write
        output: Output file path (None for stdout)
    """
    if output:
        output.write_text(content)
    else:
        typer.echo(content)


def _format_report_output(
    report: Report,
    json_output: bool,
) -> str:
    """Format Report for output.

    Args:
        report: Report to format
        json_output: Whether to output as JSON

    Returns:
        Formatted string (markdown or JSON)
    """
    if json_output:
        return report.model_dump_json(indent=2)
    return report.content


def _format_aspects_output(
    queries: ResearchQueries,
    json_output: bool,
) -> str:
    """Format ResearchQueries for output.

    Args:
        queries: ResearchQueries to format
        json_output: Whether to output as JSON

    Returns:
        Formatted string (list or JSON)
    """
    if json_output:
        return queries.model_dump_json(indent=2)
    return "\n".join(f"- [{q.intent}] {q.text}" for q in queries.queries)


def _handle_error(
    e: Exception,
    verbose: int,
) -> None:
    """Handle and display errors.

    Args:
        e: Exception that occurred
        verbose: Verbosity level for traceback
    """
    # Classify error type
    error_type = "Internal"
    message = str(e)

    if isinstance(e, ValueError):
        error_type = "Validation"
    elif isinstance(e, FileNotFoundError):
        error_type = "File"
    elif isinstance(e, json.JSONDecodeError):
        error_type = "Validation"
        message = f"Invalid JSON: {e.msg}"
    elif isinstance(e, RuntimeError):
        error_type = "Internal"

    # Show error message
    typer.echo(f"Error: {error_type}: {message}", err=True)

    # Show traceback if verbose
    if verbose >= 1:
        typer.echo("\n" + traceback.format_exc(), err=True)


def _build_llm_config(
    model: str | None,
    temperature: float | None,
    max_tokens: int | None,
    reasoning_effort: str | None,
    search_context_size: str | None,
    default_model: str,
) -> LLMConfig:
    """Build LLMConfig from CLI options.

    Args:
        model: Model ID (None for default)
        temperature: Temperature (None for default)
        max_tokens: Max tokens (None for default)
        reasoning_effort: Reasoning effort (None for default)
        search_context_size: Search context size (None for default)
        default_model: Default model ID

    Returns:
        LLMConfig instance
    """
    kwargs: dict = {"model": model or default_model}

    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if reasoning_effort is not None:
        kwargs["reasoning_effort"] = reasoning_effort
    if search_context_size is not None:
        kwargs["search_context_size"] = search_context_size

    return LLMConfig(**kwargs)


def _version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        typer.echo(f"insightflow {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
) -> None:
    """insightflow - AI-powered research automation tool."""
    pass


@app.command()
def research(
    topic: Annotated[str, typer.Argument(help="Research topic")],
    # Aspect model settings
    aspect_model: Annotated[
        str | None, typer.Option("--aspect-model", help="Model for aspect extraction")
    ] = None,
    aspect_temperature: Annotated[
        float | None,
        typer.Option("--aspect-temperature", help="Temperature for aspect model"),
    ] = None,
    aspect_max_tokens: Annotated[
        int | None,
        typer.Option("--aspect-max-tokens", help="Max tokens for aspect model"),
    ] = None,
    aspect_reasoning_effort: Annotated[
        str | None,
        typer.Option("--aspect-reasoning-effort", help="Aspect reasoning"),
    ] = None,
    # Search model settings
    search_model: Annotated[
        str | None, typer.Option("--search-model", help="Model for search")
    ] = None,
    search_temperature: Annotated[
        float | None,
        typer.Option("--search-temperature", help="Temperature for search model"),
    ] = None,
    search_max_tokens: Annotated[
        int | None,
        typer.Option("--search-max-tokens", help="Max tokens for search model"),
    ] = None,
    search_reasoning_effort: Annotated[
        str | None,
        typer.Option("--search-reasoning-effort", help="Search reasoning"),
    ] = None,
    search_context_size: Annotated[
        str | None,
        typer.Option("--search-context-size", help="Context size (low/medium/high)"),
    ] = None,
    # Report model settings
    report_model: Annotated[
        str | None, typer.Option("--report-model", help="Model for report generation")
    ] = None,
    report_temperature: Annotated[
        float | None,
        typer.Option("--report-temperature", help="Temperature for report model"),
    ] = None,
    report_max_tokens: Annotated[
        int | None,
        typer.Option("--report-max-tokens", help="Max tokens for report model"),
    ] = None,
    report_reasoning_effort: Annotated[
        str | None,
        typer.Option("--report-reasoning-effort", help="Report reasoning"),
    ] = None,
    # Common settings
    language: Annotated[
        str, typer.Option("-l", "--language", help="Output language")
    ] = "japanese",
    max_aspects: Annotated[
        int, typer.Option("--max-aspects", help="Max aspects to generate")
    ] = 5,
    concurrency: Annotated[
        int, typer.Option("--concurrency", help="Max concurrent searches")
    ] = 3,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", help="Output file path")
    ] = None,
    verbose: Annotated[
        int, typer.Option("-v", "--verbose", count=True, help="Verbosity level")
    ] = 0,
) -> None:
    """Execute full research on a topic."""
    _setup_logging(verbose)
    _check_api_key()

    try:
        # Build LLMConfigs
        settings = InsightFlowSettings()
        aspect_config = _build_llm_config(
            model=aspect_model,
            temperature=aspect_temperature,
            max_tokens=aspect_max_tokens,
            reasoning_effort=aspect_reasoning_effort,
            search_context_size=None,
            default_model=settings.default_query_model,
        )
        search_config = _build_llm_config(
            model=search_model,
            temperature=search_temperature,
            max_tokens=search_max_tokens,
            reasoning_effort=search_reasoning_effort,
            search_context_size=search_context_size,
            default_model=settings.default_search_model,
        )
        report_config = _build_llm_config(
            model=report_model,
            temperature=report_temperature,
            max_tokens=report_max_tokens,
            reasoning_effort=report_reasoning_effort,
            search_context_size=None,
            default_model=settings.default_report_model,
        )

        # Execute research
        result = asyncio.run(
            core.research(
                topic=topic,
                api_key=settings.openrouter_api_key,
                aspect_model=aspect_config,
                search_model=search_config,
                report_model=report_config,
                language=language,
                max_aspects=max_aspects,
                concurrency=concurrency,
            )
        )

        # Output result
        formatted = _format_report_output(result, json_output)
        _write_output(formatted, output)

    except Exception as e:
        _handle_error(e, verbose)
        raise typer.Exit(code=1) from None


@app.command()
def aspects(
    topic: Annotated[str, typer.Argument(help="Topic to extract aspects from")],
    model: Annotated[
        str | None, typer.Option("--model", help="LLM model to use")
    ] = None,
    temperature: Annotated[
        float | None, typer.Option("--temperature", help="Temperature (0-2)")
    ] = None,
    max_tokens: Annotated[
        int | None, typer.Option("--max-tokens", help="Max tokens")
    ] = None,
    reasoning_effort: Annotated[
        str | None, typer.Option("--reasoning-effort", help="Reasoning effort level")
    ] = None,
    language: Annotated[
        str, typer.Option("-l", "--language", help="Output language")
    ] = "japanese",
    max_aspects: Annotated[
        int, typer.Option("--max-aspects", help="Max aspects")
    ] = 5,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", help="Output file")
    ] = None,
    verbose: Annotated[
        int, typer.Option("-v", "--verbose", count=True, help="Verbosity")
    ] = 0,
) -> None:
    """Extract key aspects from a topic."""
    _setup_logging(verbose)
    _check_api_key()

    try:
        settings = InsightFlowSettings()
        config = _build_llm_config(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            search_context_size=None,
            default_model=settings.default_query_model,
        )

        system_prompt = core.build_aspect_prompt(max_aspects, language)
        result = asyncio.run(
            core.generate_queries(
                topic=topic,
                api_key=settings.openrouter_api_key,
                system_prompt=system_prompt,
                config=config,
                max_queries=max_aspects,
            )
        )

        formatted = _format_aspects_output(result.output, json_output)
        _write_output(formatted, output)

    except Exception as e:
        _handle_error(e, verbose)
        raise typer.Exit(code=1) from None


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
    model: Annotated[
        str | None, typer.Option("--model", help="LLM model to use")
    ] = None,
    temperature: Annotated[
        float | None, typer.Option("--temperature", help="Temperature (0-2)")
    ] = None,
    max_tokens: Annotated[
        int | None, typer.Option("--max-tokens", help="Max tokens")
    ] = None,
    reasoning_effort: Annotated[
        str | None, typer.Option("--reasoning-effort", help="Reasoning effort level")
    ] = None,
    search_context_size: Annotated[
        str | None,
        typer.Option("--search-context-size", help="Context size (low/medium/high)"),
    ] = None,
    language: Annotated[
        str, typer.Option("-l", "--language", help="Output language")
    ] = "japanese",
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", help="Output file")
    ] = None,
    verbose: Annotated[
        int, typer.Option("-v", "--verbose", count=True, help="Verbosity")
    ] = 0,
) -> None:
    """Execute a single search query."""
    _setup_logging(verbose)
    _check_api_key()

    try:
        settings = InsightFlowSettings()
        config = _build_llm_config(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            search_context_size=search_context_size,
            default_model=settings.default_search_model,
        )

        result = asyncio.run(
            core.search(
                query=query,
                api_key=settings.openrouter_api_key,
                config=config,
                language=language,
            )
        )

        formatted = _format_report_output(result, json_output)
        _write_output(formatted, output)

    except Exception as e:
        _handle_error(e, verbose)
        raise typer.Exit(code=1) from None


@app.command()
def compose(
    topic: Annotated[str, typer.Argument(help="Topic for the composed report")],
    reports: Annotated[
        list[Path], typer.Option("--reports", help="Report JSON files")
    ],
    model: Annotated[
        str | None, typer.Option("--model", help="LLM model to use")
    ] = None,
    temperature: Annotated[
        float | None, typer.Option("--temperature", help="Temperature (0-2)")
    ] = None,
    max_tokens: Annotated[
        int | None, typer.Option("--max-tokens", help="Max tokens")
    ] = None,
    reasoning_effort: Annotated[
        str | None, typer.Option("--reasoning-effort", help="Reasoning effort level")
    ] = None,
    language: Annotated[
        str, typer.Option("-l", "--language", help="Output language")
    ] = "japanese",
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", help="Output file")
    ] = None,
    verbose: Annotated[
        int, typer.Option("-v", "--verbose", count=True, help="Verbosity")
    ] = 0,
) -> None:
    """Compose multiple reports into one."""
    _setup_logging(verbose)
    _check_api_key()

    try:
        # Load and validate report files
        loaded_reports: list[Report] = []
        for report_path in reports:
            if not report_path.exists():
                raise FileNotFoundError(
                    f"Cannot read '{report_path}': No such file or directory"
                )
            try:
                content = report_path.read_text()
                report_data = json.loads(content)
                loaded_reports.append(Report.model_validate(report_data))
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in '{report_path}': {e.msg}"
                ) from e

        settings = InsightFlowSettings()
        config = _build_llm_config(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            search_context_size=None,
            default_model=settings.default_report_model,
        )

        result = asyncio.run(
            core.compose(
                topic=topic,
                reports=loaded_reports,
                api_key=settings.openrouter_api_key,
                config=config,
                language=language,
            )
        )

        formatted = _format_report_output(result, json_output)
        _write_output(formatted, output)

    except Exception as e:
        _handle_error(e, verbose)
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
