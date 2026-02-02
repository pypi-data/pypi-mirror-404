"""Package-level settings for insightflow.

Provides InsightFlowSettings as the single source of truth for default models
and parameters across all interfaces (CLI, API, MCP).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class InsightFlowSettings(BaseSettings):
    """Package-level settings loaded from environment variables.

    Required:
        openrouter_api_key: OpenRouter API key (OPENROUTER_API_KEY)

    Optional with defaults:
        default_query_model: Default model for query generation
        default_search_model: Default model for search
        default_report_model: Default model for report generation
        default_language: Default output language
        default_max_aspects: Default maximum aspects to extract
        default_max_queries: Default maximum queries to generate
        default_concurrency: Default concurrent search limit
    """

    openrouter_api_key: str

    # Default models
    default_query_model: str = "openai/gpt-4.1-mini"
    default_search_model: str = "perplexity/sonar-reasoning-pro"
    default_report_model: str = "google/gemini-3-flash-preview"

    # Default parameters
    default_language: str = "japanese"
    default_max_aspects: int = 5
    default_max_queries: int = 5
    default_concurrency: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
