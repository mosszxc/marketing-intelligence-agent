"""State schema for the Marketing Intelligence Agent graph."""

from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import add_messages


class AgentOutput(TypedDict, total=False):
    """Output from an individual agent."""

    summary: str
    data: dict
    charts: list[str]  # base64-encoded PNGs
    sources: list[dict]  # [{title, url, snippet}]
    error: str | None


class EvaluationResult(TypedDict, total=False):
    """Evaluation scores for the response."""

    relevance: float
    completeness: float
    accuracy: float


class GraphState(TypedDict, total=False):
    """Top-level state passed through the LangGraph workflow.

    Fields:
        query: User's original question.
        plan: List of agent names the supervisor chose to invoke.
        agent_outputs: Collected outputs keyed by agent name.
        final_answer: Formatted markdown response for the user.
        evaluation: Optional quality scores.
        messages: Chat history (LangGraph managed).
    """

    query: str
    plan: list[str]
    agent_outputs: dict[str, AgentOutput]
    final_answer: str
    evaluation: EvaluationResult
    messages: Annotated[list, add_messages]
