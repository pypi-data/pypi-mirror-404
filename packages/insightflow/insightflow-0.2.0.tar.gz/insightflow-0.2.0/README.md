# insightflow

[![PyPI version](https://img.shields.io/pypi/v/insightflow)](https://pypi.org/project/insightflow/)
[![Python 3.12+](https://img.shields.io/pypi/pyversions/insightflow)](https://pypi.org/project/insightflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Japanese / 日本語](README.ja.md)

Automated research tool that searches and analyzes web content, papers, blogs, and social media to generate comprehensive reports for any query.

Leverages multiple LLM providers (OpenAI, Google, Perplexity, xAI) via [OpenRouter](https://openrouter.ai/) to automate multi-perspective research on any topic.

## How It Works

```
Topic
  |
[1] Aspect Extraction (openai/gpt-4.1-mini)
  |
  +-- Aspect A --> [2] Parallel Web Search (perplexity/sonar-reasoning-pro) --> Report A
  +-- Aspect B --> [2] Parallel Web Search                                  --> Report B
  +-- Aspect C --> [2] Parallel Web Search                                  --> Report C
                                                                                 |
                                                            [3] Report Synthesis (google/gemini-3-flash-preview)
                                                                                 |
                                                                    Final Report (Markdown + Citations)
```

1. **Aspect Extraction** - Identifies key perspectives of the topic using an LLM
2. **Parallel Search** - Searches each aspect concurrently via web-connected models
3. **Report Synthesis** - Merges all findings into a single, cited Markdown report

## Prerequisites

- Python 3.12+
- [OpenRouter](https://openrouter.ai/) API key

## Installation

```bash
pip install insightflow
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add insightflow
```

### Extras

| Extra | Description | pip | uv |
|-------|-------------|-----|-----|
| `cli` | CLI interface (Typer) | `pip install "insightflow[cli]"` | `uv add "insightflow[cli]"` |
| `api` | REST API server (FastAPI) | `pip install "insightflow[api]"` | `uv add "insightflow[api]"` |
| `mcp` | MCP server (Claude Code, etc.) | `pip install "insightflow[mcp]"` | `uv add "insightflow[mcp]"` |
| `all` | All extras | `pip install "insightflow[all]"` | `uv add "insightflow[all]"` |

## Setup

Set your OpenRouter API key as an environment variable:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

Or create a `.env` file in your project root:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

## Usage

### Python Library

```python
import asyncio
import os
from insightflow.core import research
from insightflow.models import LLMConfig

api_key = os.environ["OPENROUTER_API_KEY"]

report = asyncio.run(research(
    topic="Recent trends in quantum computing",
    api_key=api_key,
    aspect_model=LLMConfig(model="openai/gpt-4.1-mini"),
    search_model=LLMConfig(model="perplexity/sonar-reasoning-pro"),
    report_model=LLMConfig(model="google/gemini-3-flash-preview"),
))

print(report.content)       # Markdown report
print(report.citations)     # List of citations
print(report.metadata)      # Elapsed time, model used, etc.
```

Individual functions are also available:

```python
from insightflow.core import generate_queries, search, compose, build_aspect_prompt
from insightflow.models import LLMConfig

# Query generation (aspect extraction)
result = asyncio.run(generate_queries(
    topic="ML optimization techniques",
    api_key=api_key,
    system_prompt=build_aspect_prompt(max_aspects=5),
    config=LLMConfig(model="openai/gpt-4.1-mini"),
))

# Single search query
result = asyncio.run(search(
    query="Python packaging best practices",
    api_key=api_key,
    config=LLMConfig(model="perplexity/sonar-reasoning-pro"),
))
```

### CLI

```bash
pip install "insightflow[cli]"  # or: uv add "insightflow[cli]"

# Full research
insightflow research "Recent trends in quantum computing"

# Aspect extraction only
insightflow aspects "ML optimization techniques"

# Single search
insightflow search "Python packaging best practices"

# With options
insightflow research "AI safety" \
  --language english \
  --max-aspects 3 \
  --search-model perplexity/sonar-pro \
  --json \
  -o report.json
```

Run `insightflow --help` for all available options.

> **Tip:** You can also run insightflow without installing via [uvx](https://docs.astral.sh/uv/concepts/tools/):
> ```bash
> uvx --from "insightflow[cli]" insightflow research "Recent trends in quantum computing"
> ```

### REST API Server

```bash
pip install "insightflow[api]"  # or: uv add "insightflow[api]"
python -m uvicorn insightflow.interfaces.api:app
```

Swagger UI is available at `http://localhost:8000/docs`.

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "quantum computing", "language": "english"}'
```

### MCP Server (Claude Code Integration)

Use insightflow as an MCP tool in Claude Code so that Claude can autonomously run research.

**1. Install & Register**

```bash
pip install "insightflow[mcp]"  # or: uv add "insightflow[mcp]"

claude mcp add --transport stdio \
  --env OPENROUTER_API_KEY=sk-or-v1-... \
  insightflow -- python -m insightflow.interfaces.mcp
```

With uvx (no local install required):

```bash
claude mcp add --transport stdio \
  --env OPENROUTER_API_KEY=sk-or-v1-... \
  insightflow -- uvx --from "insightflow[mcp]" python -m insightflow.interfaces.mcp
```

> **Manual configuration (alternative)**
>
> Instead of `claude mcp add`, you can edit `~/.claude.json` directly:
>
> ```json
> {
>   "mcpServers": {
>     "insightflow": {
>       "command": "python",
>       "args": ["-m", "insightflow.interfaces.mcp"],
>       "env": {
>         "OPENROUTER_API_KEY": "sk-or-v1-..."
>       }
>     }
>   }
> }
> ```
>
> You can also use `.mcp.json` in your project root for team sharing, but **do not** include API keys in it — use `~/.claude.json` for secrets.

**2. Use from Claude Code**

Once configured, Claude Code recognizes the `research` tool. Ask Claude to research a topic in conversation and it will call insightflow automatically.

Tool parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic` | string | Yes | - | Research topic |
| `aspect_model` | string | No | `openai/gpt-4.1-mini` | Model for aspect extraction |
| `search_model` | string | No | `perplexity/sonar-reasoning-pro` | Model for search |
| `report_model` | string | No | `google/gemini-3-flash-preview` | Model for report generation |
| `language` | string | No | `japanese` | Output language |
| `max_aspects` | integer | No | `5` | Maximum number of aspects |
| `concurrency` | integer | No | `3` | Maximum concurrent searches |

## Configuration

Configurable via environment variables or `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key |
| `DEFAULT_QUERY_MODEL` | No | `openai/gpt-4.1-mini` | Default query/aspect extraction model |
| `DEFAULT_SEARCH_MODEL` | No | `perplexity/sonar-reasoning-pro` | Default search model |
| `DEFAULT_REPORT_MODEL` | No | `google/gemini-3-flash-preview` | Default report generation model |
| `DEFAULT_LANGUAGE` | No | `japanese` | Default output language |
| `DEFAULT_MAX_ASPECTS` | No | `5` | Default number of aspects |
| `DEFAULT_CONCURRENCY` | No | `3` | Default concurrent searches |

## Development

```bash
git clone https://github.com/sync-dev-org/insightflow.git
cd insightflow
uv sync --all-extras

# Test
uv run pytest

# Lint
uv run ruff check src/
uv run ruff format src/
```

## License

MIT License - See [LICENSE](LICENSE) for details.
