"""Research query Pydantic models.

Defines models for research query generation:
- ResearchQuery: A single research query with intent classification
- ResearchQueries: Collection of queries (pydantic-ai output_type, min 1 element)
"""

from typing import Literal

from pydantic import BaseModel, Field


class ResearchQuery(BaseModel):
    """A single research query with intent classification.

    Represents one research query as a natural language phrase (3-20 words)
    with an intent classification for pipeline-layer model selection.
    Used by aspects extraction and gap query generation.
    """

    text: str = Field(
        min_length=1,
        description="Search query string (natural language phrase of 3-20 words)",
    )
    intent: Literal["general", "explore", "realtime"] = Field(
        description=(
            "Search intent classification:\n"
            "- general: General information, overviews, established facts\n"
            "- explore: Exploratory research, technical details, in-depth analysis\n"
            "- realtime: Recent news, social media opinions, personal experiences"
        ),
    )


class ResearchQueries(BaseModel):
    """Collection of research queries (pydantic-ai output_type).

    Aggregates multiple ResearchQuery instances. Requires at least one
    query (min_length=1). When used as pydantic-ai output_type,
    validation failure triggers automatic retry.
    """

    queries: list[ResearchQuery] = Field(
        min_length=1,
        description="List of research queries",
    )
