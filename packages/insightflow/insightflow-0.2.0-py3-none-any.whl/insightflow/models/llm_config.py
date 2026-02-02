"""LLMConfig model for provider-agnostic LLM configuration.

Abstracts provider-specific differences (reasoning, search, output wrapper)
across OpenRouter-connected LLM providers (Perplexity, Google, xAI, OpenAI)
and provides unified conversion to pydantic-ai ModelSettings.

Uses PROVIDER_CAPABILITIES dict with longest-prefix-match to resolve
provider/model-series capabilities declaratively.
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_ai.settings import ModelSettings

ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]
SearchContextSize = Literal["low", "medium", "high"]
OutputWrapper = Literal["prompted", "tool"]
ReasoningStyle = Literal["effort", "enabled", "none"]
SearchMode = Literal["builtin", "online_suffix"]

SUPPORTED_PREFIXES: tuple[str, ...] = (
    "perplexity/",
    "google/",
    "x-ai/",
    "openai/",
    "anthropic/",
)

_SEARCH_CONTEXT_TO_MAX_RESULTS: dict[str, int] = {
    "low": 3,
    "medium": 5,
    "high": 10,
}


@dataclass(frozen=True)
class ProviderConfig:
    """Provider/model-series capability definition."""

    reasoning_style: ReasoningStyle
    reasoning_values: tuple[str, ...] | None
    reasoning_required: bool
    output_wrapper: OutputWrapper
    search_mode: SearchMode
    max_completion_tokens: int  # Model's maximum output tokens (OpenRouter spec)


PROVIDER_CAPABILITIES: dict[str, ProviderConfig] = {
    "perplexity/": ProviderConfig(
        reasoning_style="none",
        reasoning_values=None,
        reasoning_required=False,
        output_wrapper="prompted",
        search_mode="builtin",
        max_completion_tokens=8192,  # Conservative (official limit unknown)
    ),
    "google/gemini-3-pro": ProviderConfig(
        reasoning_style="effort",
        reasoning_values=("low", "high"),
        reasoning_required=True,
        output_wrapper="tool",
        search_mode="online_suffix",
        max_completion_tokens=65535,
    ),
    "google/": ProviderConfig(
        reasoning_style="effort",
        reasoning_values=("minimal", "low", "medium", "high"),
        reasoning_required=False,
        output_wrapper="tool",
        search_mode="online_suffix",
        max_completion_tokens=65535,
    ),
    "x-ai/": ProviderConfig(
        reasoning_style="enabled",
        reasoning_values=None,
        reasoning_required=False,
        output_wrapper="prompted",
        search_mode="online_suffix",
        max_completion_tokens=32768,  # Conservative
    ),
    "openai/gpt-5": ProviderConfig(
        reasoning_style="effort",
        reasoning_values=("low", "medium", "high"),
        reasoning_required=False,
        output_wrapper="prompted",  # tool/native unstable with :online search
        search_mode="online_suffix",
        max_completion_tokens=128000,
    ),
    "openai/": ProviderConfig(
        reasoning_style="none",
        reasoning_values=None,
        reasoning_required=False,
        output_wrapper="tool",
        search_mode="online_suffix",
        max_completion_tokens=32768,  # gpt-4.1-mini etc.
    ),
    "anthropic/": ProviderConfig(
        reasoning_style="effort",
        reasoning_values=("minimal", "low", "medium", "high", "xhigh"),
        reasoning_required=False,
        output_wrapper="tool",  # requires beta header via extra_headers
        search_mode="online_suffix",
        max_completion_tokens=64000,
    ),
}


class LLMConfig(BaseModel):
    """Provider-agnostic LLM configuration model.

    Encapsulates model ID, generation parameters, reasoning effort,
    and search context size. Provides provider-aware conversion to
    pydantic-ai ModelSettings via to_model_settings().

    Concurrency contract:
        This model is intentionally mutable (no frozen=True).
        When sharing an instance across parallel executions (e.g.,
        research layer's concurrent searches), callers MUST create
        a defensive copy via model_copy() before passing to each
        concurrent task. Core-layer functions treat LLMConfig as
        read-only and never mutate it.
    """

    model: str = Field(description="OpenRouter model ID (e.g. 'perplexity/sonar-pro')")
    temperature: float = Field(
        default=0.7, ge=0, le=2, description="Generation temperature"
    )
    max_tokens: int = Field(default=4096, gt=0, description="Maximum generation tokens")
    reasoning_effort: ReasoningEffort = Field(
        default="none", description="Reasoning effort level"
    )
    search_context_size: SearchContextSize = Field(
        default="high", description="Search context size"
    )

    @field_validator("model")
    @classmethod
    def validate_model_prefix(cls, v: str) -> str:
        """Validate that model ID starts with a supported prefix."""
        if not any(v.startswith(p) for p in SUPPORTED_PREFIXES):
            raise ValueError(
                "Unsupported model prefix. "
                f"Must start with one of: {SUPPORTED_PREFIXES}"
            )
        return v

    @model_validator(mode="after")
    def validate_provider_compatibility(self) -> "LLMConfig":
        """Validate provider/setting compatibility using PROVIDER_CAPABILITIES."""
        config = self._provider_config
        if config.reasoning_style == "none" and self.reasoning_effort != "none":
            raise ValueError(f"Model {self.model} does not support reasoning_effort")
        if config.reasoning_required and self.reasoning_effort == "none":
            raise ValueError(f"Model {self.model} requires reasoning_effort")
        if config.reasoning_values and self.reasoning_effort not in (
            "none",
            *config.reasoning_values,
        ):
            raise ValueError(
                f"Model {self.model} only supports "
                f"reasoning_effort: {config.reasoning_values}"
            )
        # max_tokens limit check
        if self.max_tokens > config.max_completion_tokens:
            raise ValueError(
                f"max_tokens ({self.max_tokens}) exceeds model limit "
                f"({config.max_completion_tokens}) for {self.model}"
            )
        return self

    @property
    def provider(self) -> str:
        """Extract provider name from model ID (before slash)."""
        return self.model.split("/")[0]

    @property
    def _provider_config(self) -> ProviderConfig:
        """Resolve ProviderConfig via longest-prefix-match on model ID.

        Strips ':online' suffix before matching. Sorts PROVIDER_CAPABILITIES
        keys by length descending and returns the first startswith match.
        """
        # Strip :online suffix for model identification
        model_base = self.model.split(":")[0]
        # Sort keys by length descending for longest-prefix-match
        sorted_keys = sorted(PROVIDER_CAPABILITIES.keys(), key=len, reverse=True)
        for prefix in sorted_keys:
            if model_base.startswith(prefix):
                return PROVIDER_CAPABILITIES[prefix]
        # Should not reach here due to field_validator, but satisfy type checker
        raise ValueError(f"No provider config found for model: {self.model}")

    @property
    def output_wrapper(self) -> OutputWrapper:
        """Return output wrapper type based on ProviderConfig."""
        return self._provider_config.output_wrapper

    @property
    def _is_search_model(self) -> bool:
        """Check if model is a search-capable model."""
        config = self._provider_config
        return config.search_mode == "builtin" or self.model.endswith(":online")

    def to_model_settings(self) -> ModelSettings:
        """Convert to pydantic-ai ModelSettings.

        Includes provider-specific reasoning and search parameters
        in the extra_body when applicable.
        """
        settings: dict = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        extra_body: dict = {}
        config = self._provider_config

        # Reasoning settings based on ProviderConfig.reasoning_style
        if self.reasoning_effort != "none":
            if config.reasoning_style == "effort":
                extra_body["reasoning"] = {"effort": self.reasoning_effort}
            elif config.reasoning_style == "enabled":
                extra_body["reasoning"] = {"enabled": True}

        # Search settings based on ProviderConfig.search_mode
        if self._is_search_model:
            if config.search_mode == "builtin":
                # Perplexity: native search with search_context_size
                extra_body["web_search_options"] = {
                    "search_context_size": self.search_context_size
                }
            elif self.provider == "google":
                # Google :online models use plugins with Exa
                extra_body["plugins"] = [
                    {
                        "id": "web",
                        "engine": "exa",
                        "max_results": _SEARCH_CONTEXT_TO_MAX_RESULTS[
                            self.search_context_size
                        ],
                    }
                ]
            else:
                # x-ai and openai :online models
                extra_body["web_search_options"] = {
                    "search_context_size": self.search_context_size
                }

        if extra_body:
            settings["extra_body"] = extra_body

        # Anthropic: add beta header for structured outputs via OpenRouter
        if self.provider == "anthropic":
            settings["extra_headers"] = {
                "anthropic-beta": "structured-outputs-2025-11-13"
            }

        return ModelSettings(**settings)
