"""LLM task result models.

Defines models for LLM task execution results:
- LLMUsage: Token and request usage information
- LLMTaskResult: Generic result wrapper with output, timing, and usage
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class LLMUsage(BaseModel):
    """LLM使用量情報。

    pydantic-ai の RunUsage から必要なフィールドを抽出した
    API公開用モデル。
    """

    requests: int = Field(description="総リクエスト数")
    input_tokens: int = Field(description="入力トークン数")
    output_tokens: int = Field(description="出力トークン数")


class LLMTaskResult(BaseModel, Generic[T]):
    """LLMタスク実行結果。

    run_llm_task の戻り値として使用。API レスポンスとしても
    そのままシリアライズ可能。
    """

    output: T = Field(description="タスク出力")
    elapsed_sec: float = Field(ge=0, description="実行時間（秒）")
    usage: LLMUsage = Field(description="使用量情報")
