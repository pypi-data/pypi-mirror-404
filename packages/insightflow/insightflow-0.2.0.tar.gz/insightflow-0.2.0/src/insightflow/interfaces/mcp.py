"""MCP server interface for insightflow.

Exposes the research function as an MCP tool for AI agents like Claude Code.
Follows MCP (Model Context Protocol) specification with stdio transport.

Entry point: python -m insightflow.interfaces.mcp
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from insightflow.settings import InsightFlowSettings

if TYPE_CHECKING:
    from mcp.server import Server

    from insightflow.models import LLMConfig

from insightflow import __version__

# Configure logging to stderr (stdout is used for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

def _check_api_key() -> None:
    """Check if OPENROUTER_API_KEY is set via pydantic-settings.

    Loads from environment variables and .env file automatically.
    Exits with code 1 if not set.
    """
    try:
        InsightFlowSettings()
    except ValidationError:
        logger.error("OPENROUTER_API_KEY environment variable is not set")
        sys.exit(1)


# Tool definition as a dictionary for MCP
RESEARCH_TOOL_SCHEMA: dict[str, Any] = {
    "name": "research",
    "description": (
        "Research a topic and generate a comprehensive report with citations. "
        "Searches multiple aspects of the topic in parallel and synthesizes findings."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic to research",
            },
            "aspect_model": {
                "type": "string",
                "description": "OpenRouter model ID for aspect extraction",
                "default": "openai/gpt-4.1-mini",
            },
            "search_model": {
                "type": "string",
                "description": "OpenRouter model ID for search",
                "default": "perplexity/sonar-reasoning-pro",
            },
            "report_model": {
                "type": "string",
                "description": "OpenRouter model ID for report generation",
                "default": "google/gemini-3-flash-preview",
            },
            "language": {
                "type": "string",
                "description": "Output language",
                "default": "japanese",
            },
            "max_aspects": {
                "type": "integer",
                "description": "Maximum number of aspects to generate",
                "default": 5,
            },
            "concurrency": {
                "type": "integer",
                "description": "Maximum concurrent searches",
                "default": 3,
            },
        },
        "required": ["topic"],
    },
}


def build_research_configs(
    params: dict[str, Any],
) -> tuple[LLMConfig, LLMConfig, LLMConfig]:
    """Build LLMConfig instances from MCP tool parameters.

    Args:
        params: Dictionary of tool parameters

    Returns:
        Tuple of (aspect_config, search_config, report_config)
    """
    from insightflow.models import LLMConfig

    settings = InsightFlowSettings()
    aspect_config = LLMConfig(
        model=params.get("aspect_model") or settings.default_query_model,
    )
    search_config = LLMConfig(
        model=params.get("search_model") or settings.default_search_model,
    )
    report_config = LLMConfig(
        model=params.get("report_model") or settings.default_report_model,
    )
    return aspect_config, search_config, report_config


async def handle_research(arguments: dict[str, Any]) -> str:
    """Execute research and return markdown content.

    Args:
        arguments: Tool call arguments

    Returns:
        Markdown report content

    Raises:
        ValueError: If required parameters are missing or invalid
        RuntimeError: If research fails
    """
    from insightflow.core.research import research

    # Validate required parameter
    topic = arguments.get("topic")
    if not topic:
        raise ValueError("Missing required parameter: topic")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Invalid parameter: topic must be a non-empty string")

    # Get optional parameters with defaults
    settings = InsightFlowSettings()
    language = arguments.get("language", settings.default_language)
    max_aspects = arguments.get("max_aspects", settings.default_max_aspects)
    concurrency = arguments.get("concurrency", settings.default_concurrency)

    # Validate integer parameters
    if not isinstance(max_aspects, int) or max_aspects < 1:
        msg = f"max_aspects must be a positive integer, got {max_aspects}"
        raise ValueError(f"Invalid parameter: {msg}")
    if not isinstance(concurrency, int) or concurrency < 1:
        msg = f"concurrency must be a positive integer, got {concurrency}"
        raise ValueError(f"Invalid parameter: {msg}")

    # Build LLMConfigs
    aspect_config, search_config, report_config = build_research_configs(arguments)

    logger.info("Research started: topic=%r", topic)

    try:
        report = await research(
            topic=topic,
            api_key=settings.openrouter_api_key,
            aspect_model=aspect_config,
            search_model=search_config,
            report_model=report_config,
            language=language,
            max_aspects=max_aspects,
            concurrency=concurrency,
        )
        logger.info("Research completed: topic=%r", topic)
        return report.content
    except asyncio.CancelledError:
        logger.info("Research cancelled: topic=%r", topic)
        raise
    except Exception as e:
        logger.error(
            "Research failed: topic=%r, error=%s", topic, str(e), exc_info=True
        )
        raise


def create_mcp_server() -> Server:
    """Create and configure the MCP server.

    Returns:
        Configured MCP Server instance
    """
    from mcp.server import Server
    from mcp.types import TextContent, Tool

    server = Server("insightflow")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return available tools."""
        return [
            Tool(
                name=RESEARCH_TOOL_SCHEMA["name"],
                description=RESEARCH_TOOL_SCHEMA["description"],
                inputSchema=RESEARCH_TOOL_SCHEMA["inputSchema"],
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute a tool call."""
        from mcp.shared.exceptions import McpError
        from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, ErrorData

        if name != "research":
            err = ErrorData(code=INVALID_PARAMS, message=f"Unknown tool: {name}")
            raise McpError(err)

        try:
            content = await handle_research(arguments)
            return [TextContent(type="text", text=content)]
        except ValueError as e:
            err = ErrorData(code=INVALID_PARAMS, message=str(e))
            raise McpError(err) from e
        except asyncio.CancelledError:
            # Re-raise CancelledError for proper cancellation handling
            raise
        except Exception as e:
            err = ErrorData(code=INTERNAL_ERROR, message=f"Research failed: {e}")
            raise McpError(err) from e

    return server


async def run_server() -> None:
    """Run the MCP server with stdio transport."""
    from mcp.server.stdio import stdio_server

    server = create_mcp_server()

    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


def main() -> None:
    """Entry point for the MCP server."""
    # Check for required API key (pydantic-settings auto-loads .env)
    _check_api_key()

    logger.info("Starting InsightFlow MCP server v%s", __version__)

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error("MCP server error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
