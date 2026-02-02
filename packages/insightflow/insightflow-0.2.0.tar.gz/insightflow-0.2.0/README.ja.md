# insightflow

[![PyPI version](https://img.shields.io/pypi/v/insightflow)](https://pypi.org/project/insightflow/)
[![Python 3.12+](https://img.shields.io/pypi/pyversions/insightflow)](https://pypi.org/project/insightflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README.md)

Webコンテンツ、論文、ブログ、SNSを検索・分析し、クエリに対する包括的なレポートを生成するリサーチ自動化ツール。

[OpenRouter](https://openrouter.ai/) 経由で複数のLLMプロバイダー（OpenAI, Google, Perplexity, xAI）を活用し、トピックの多角的な調査を自動化します。

## 仕組み

```
トピック
  |
[1] アスペクト抽出 (openai/gpt-4.1-mini)
  |
  +-- 観点A --> [2] 並列Web検索 (perplexity/sonar-reasoning-pro) --> レポートA
  +-- 観点B --> [2] 並列Web検索                                  --> レポートB
  +-- 観点C --> [2] 並列Web検索                                  --> レポートC
                                                                      |
                                                        [3] レポート統合 (google/gemini-3-flash-preview)
                                                                      |
                                                          最終レポート (Markdown + 引用)
```

1. **アスペクト抽出** - LLMを使ってトピックの主要な観点を特定
2. **並列検索** - Web接続モデルで各観点を並列に検索
3. **レポート統合** - 全結果を引用付きMarkdownレポートに統合

## 前提条件

- Python 3.12 以上
- [OpenRouter](https://openrouter.ai/) の APIキー

## インストール

```bash
pip install insightflow
```

[uv](https://docs.astral.sh/uv/) の場合:

```bash
uv add insightflow
```

### エクストラ

| エクストラ | 内容 | pip | uv |
|-----------|------|-----|-----|
| `cli` | CLIインターフェース (Typer) | `pip install "insightflow[cli]"` | `uv add "insightflow[cli]"` |
| `api` | REST APIサーバー (FastAPI) | `pip install "insightflow[api]"` | `uv add "insightflow[api]"` |
| `mcp` | MCPサーバー (Claude Code等) | `pip install "insightflow[mcp]"` | `uv add "insightflow[mcp]"` |
| `all` | 全エクストラ | `pip install "insightflow[all]"` | `uv add "insightflow[all]"` |

## セットアップ

OpenRouter APIキーを環境変数に設定します。

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

または `.env` ファイルを作成:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

## 使い方

### Pythonライブラリとして

```python
import asyncio
import os
from insightflow.core import research
from insightflow.models import LLMConfig

api_key = os.environ["OPENROUTER_API_KEY"]

report = asyncio.run(research(
    topic="量子コンピューティングの最新動向",
    api_key=api_key,
    aspect_model=LLMConfig(model="openai/gpt-4.1-mini"),
    search_model=LLMConfig(model="perplexity/sonar-reasoning-pro"),
    report_model=LLMConfig(model="google/gemini-3-flash-preview"),
))

print(report.content)       # Markdownレポート
print(report.citations)     # 引用リスト
print(report.metadata)      # 処理時間、使用モデル等
```

個別の関数も利用可能です:

```python
from insightflow.core import generate_queries, search, compose, build_aspect_prompt
from insightflow.models import LLMConfig

# クエリ生成 (アスペクト抽出)
result = asyncio.run(generate_queries(
    topic="機械学習の最適化手法",
    api_key=api_key,
    system_prompt=build_aspect_prompt(max_aspects=5),
    config=LLMConfig(model="openai/gpt-4.1-mini"),
))

# 単一検索のみ
result = asyncio.run(search(
    query="Python パッケージング ベストプラクティス",
    api_key=api_key,
    config=LLMConfig(model="perplexity/sonar-reasoning-pro"),
))
```

### CLI

```bash
pip install "insightflow[cli]"  # or: uv add "insightflow[cli]"

# フルリサーチ
insightflow research "量子コンピューティングの最新動向"

# アスペクト抽出のみ
insightflow aspects "機械学習の最適化手法"

# 単一検索
insightflow search "Python パッケージング ベストプラクティス"

# オプション例
insightflow research "AI safety" \
  --language english \
  --max-aspects 3 \
  --search-model perplexity/sonar-pro \
  --json \
  -o report.json
```

`insightflow --help` で全オプションを確認できます。

> **Tip:** [uvx](https://docs.astral.sh/uv/concepts/tools/) を使えばインストール不要で実行できます:
> ```bash
> uvx --from "insightflow[cli]" insightflow research "量子コンピューティングの最新動向"
> ```

### REST API サーバー

```bash
pip install "insightflow[api]"  # or: uv add "insightflow[api]"
python -m uvicorn insightflow.interfaces.api:app
```

`http://localhost:8000/docs` で Swagger UI が開きます。

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "量子コンピューティング", "language": "japanese"}'
```

### MCP サーバー (Claude Code連携)

insightflowをClaude CodeのMCPツールとして使うと、Claudeが自律的にリサーチを実行できます。

**1. インストール & 登録**

```bash
pip install "insightflow[mcp]"  # or: uv add "insightflow[mcp]"

claude mcp add --transport stdio \
  --env OPENROUTER_API_KEY=sk-or-v1-... \
  insightflow -- python -m insightflow.interfaces.mcp
```

uvx を使う場合 (ローカルインストール不要):

```bash
claude mcp add --transport stdio \
  --env OPENROUTER_API_KEY=sk-or-v1-... \
  insightflow -- uvx --from "insightflow[mcp]" python -m insightflow.interfaces.mcp
```

> **手動設定 (代替方法)**
>
> `claude mcp add` の代わりに `~/.claude.json` を直接編集することもできます:
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
> チーム共有用にプロジェクトルートの `.mcp.json` も使えますが、APIキーは含めず `~/.claude.json` 側に記載してください。

**2. Claude Codeから利用**

設定後、Claude Codeが `research` ツールを認識します。会話の中で「〜について調べて」と依頼すると、insightflowを呼び出してリサーチを実行します。

ツールのパラメータ:

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|------|------|-----------|------|
| `topic` | string | Yes | - | リサーチトピック |
| `aspect_model` | string | No | `openai/gpt-4.1-mini` | アスペクト抽出モデル |
| `search_model` | string | No | `perplexity/sonar-reasoning-pro` | 検索モデル |
| `report_model` | string | No | `google/gemini-3-flash-preview` | レポート生成モデル |
| `language` | string | No | `japanese` | 出力言語 |
| `max_aspects` | integer | No | `5` | アスペクト数上限 |
| `concurrency` | integer | No | `3` | 並列検索数 |

## 設定

環境変数または `.env` ファイルで設定可能です。

| 環境変数 | 必須 | デフォルト | 説明 |
|---------|------|-----------|------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter APIキー |
| `DEFAULT_QUERY_MODEL` | No | `openai/gpt-4.1-mini` | クエリ/アスペクト抽出のデフォルトモデル |
| `DEFAULT_SEARCH_MODEL` | No | `perplexity/sonar-reasoning-pro` | 検索のデフォルトモデル |
| `DEFAULT_REPORT_MODEL` | No | `google/gemini-3-flash-preview` | レポート生成のデフォルトモデル |
| `DEFAULT_LANGUAGE` | No | `japanese` | デフォルト出力言語 |
| `DEFAULT_MAX_ASPECTS` | No | `5` | デフォルトアスペクト数 |
| `DEFAULT_CONCURRENCY` | No | `3` | デフォルト並列検索数 |

## 開発

```bash
git clone https://github.com/sync-dev-org/insightflow.git
cd insightflow
uv sync --all-extras

# テスト
uv run pytest

# Lint
uv run ruff check src/
uv run ruff format src/
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。
