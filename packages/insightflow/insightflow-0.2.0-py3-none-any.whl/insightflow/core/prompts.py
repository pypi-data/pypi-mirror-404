"""Default system prompts for LLM tasks.

Provides prompt templates that can be used by application layer code.
These are provided as a convenience; applications can define their own prompts.
"""


def build_aspect_prompt(max_queries: int, language: str | None = None) -> str:
    """Build system prompt for aspect/query extraction.

    Args:
        max_queries: Maximum number of queries to generate
        language: Output language (e.g., "japanese", "english"). If None, no
            language instruction is included.

    Returns:
        System prompt string for query extraction
    """
    language_instruction = (
        f"- Output all queries in {language}\n"
        if language
        else ""
    )
    return (
        "You are a research analyst. Extract multiple research queries (perspectives) "
        "from the given topic.\n\n"
        "## Query Structure (CRITICAL)\n"
        "- The FIRST query MUST be a general overview of the original topic (intent=general)\n"
        "- Example: For 'UE5.7 known bugs', first query should be 'UE5.7 major known bugs overview'\n"
        "- Remaining queries should cover specific angles/dimensions with varied intents\n\n"
        "## Intent Classification (CRITICAL)\n"
        "Assign an intent to each query:\n"
        "- general: General information, overviews, established facts\n"
        "- explore: Exploratory research, technical details, in-depth analysis\n"
        "- realtime: Recent news, social media opinions, personal experiences\n\n"
        "## Output Requirements\n"
        f"- Generate up to {max_queries} research queries\n"
        "- Each query should be a natural language phrase of 3-20 words\n"
        "- Express perspectives or angles of the topic suitable for search\n"
        f"{language_instruction}\n"
        "## Context Preservation (CRITICAL)\n"
        "- ALWAYS include the original topic's proper nouns, version numbers, "
        "product names, and specific identifiers in each query\n"
        "- Never generalize queries to lose the original topic context\n"
        "- Example: For 'UE5.7 known bugs', output 'UE5.7 rendering issues' "
        "NOT just 'rendering issues'\n\n"
        "## Diversity Rules\n"
        "- Cover different dimensions (technical, social, historical, economic, etc.)\n"
        "- Avoid redundant or overlapping perspectives\n"
        "- Ensure intent diversity (not all queries should have the same intent)\n"
        "- Provide comprehensive, balanced viewpoints"
    )


def build_gap_prompt(max_queries: int, language: str | None = None) -> str:
    """Build system prompt for gap query generation.

    Args:
        max_queries: Maximum number of queries to generate
        language: Output language (e.g., "japanese", "english"). If None, no
            language instruction is included.

    Returns:
        System prompt string for gap query generation
    """
    language_instruction = (
        f"- Output all queries in {language}\n"
        if language
        else ""
    )
    return (
        "You are a research analyst. Analyze the given topic and existing reports "
        "to identify gaps and generate queries for deeper investigation.\n\n"
        "## Gap Detection (CRITICAL)\n"
        "Identify the following types of gaps:\n"
        "- Missing information: Topics mentioned but not fully explored\n"
        "- Ambiguities: Unclear or vague statements that need clarification\n"
        "- Conflicting results: Contradictory information across reports\n"
        "- Outdated information: Areas that may need recent updates\n\n"
        "## Intent Classification (CRITICAL)\n"
        "Assign an intent to each query:\n"
        "- general: General information, overviews, established facts\n"
        "- explore: Exploratory research, technical details, in-depth analysis\n"
        "- realtime: Recent news, social media opinions, personal experiences\n\n"
        "## Output Requirements\n"
        f"- Generate up to {max_queries} gap-filling queries\n"
        "- Each query should be a natural language phrase of 3-20 words\n"
        "- Focus on areas where reports lack depth or have conflicts\n"
        f"{language_instruction}\n"
        "## Context Preservation (CRITICAL)\n"
        "- ALWAYS include the original topic's proper nouns, version numbers, "
        "product names, and specific identifiers in each query\n"
        "- Reference specific gaps found in the reports\n"
        "- Never generate generic queries that ignore the existing context\n\n"
        "## Diversity Rules\n"
        "- Cover different types of gaps (missing, ambiguous, conflicting)\n"
        "- Avoid redundant queries\n"
        "- Ensure intent diversity based on the nature of each gap\n"
        "- Prioritize queries that would most improve research quality"
    )
