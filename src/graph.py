"""LangGraph workflow for the Marketing Intelligence Agent."""

import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.analytics import run_analytics, run_analytics_no_llm
from src.agents.report import format_report
from src.agents.research import run_research, run_research_no_llm
from src.agents.supervisor import classify_query
from src.state import GraphState


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def supervisor(state: GraphState) -> dict:
    """Classify the query and decide which agents to invoke."""
    query = state.get("query", "")
    plan = classify_query(query)
    return {"plan": plan}


def route_agents(state: GraphState) -> str:
    """Conditional edge: pick next agent or go to synthesize."""
    plan = state.get("plan", [])
    outputs = state.get("agent_outputs", {})

    for agent_name in plan:
        if agent_name not in outputs:
            return agent_name

    return "synthesize"


def _make_analytics_node(*, inject_error: bool = False):
    """Factory: returns analytics node, optionally with injected error."""

    def analytics_agent(state: GraphState) -> dict:
        """Analyze campaign data using the analytics agent."""
        query = state.get("query", "")
        outputs = dict(state.get("agent_outputs", {}))

        if inject_error:
            outputs["analytics"] = {
                "summary": "",
                "data": {},
                "charts": [],
                "sources": [],
                "error": "Analytics agent error: injected failure for testing",
            }
            return {"agent_outputs": outputs}

        try:
            if os.getenv("OPENAI_API_KEY"):
                result = run_analytics(query)
            else:
                result = run_analytics_no_llm(query)
        except Exception as exc:
            result = {
                "summary": "",
                "data": {},
                "charts": [],
                "sources": [],
                "error": f"Analytics agent error: {exc}",
            }

        outputs["analytics"] = result
        return {"agent_outputs": outputs}

    return analytics_agent


def _make_research_node():
    """Factory: returns research node with error handling."""

    def research_agent(state: GraphState) -> dict:
        """Search the web for market intelligence."""
        query = state.get("query", "")
        outputs = dict(state.get("agent_outputs", {}))

        try:
            if os.getenv("OPENAI_API_KEY"):
                result = run_research(query)
            else:
                result = run_research_no_llm(query)
        except Exception as exc:
            result = {
                "summary": "",
                "data": {},
                "charts": [],
                "sources": [],
                "error": f"Research agent error: {exc}",
            }

        outputs["research"] = result
        return {"agent_outputs": outputs}

    return research_agent


def synthesize(state: GraphState) -> dict:
    """Combine agent outputs into a formatted report."""
    query = state.get("query", "")
    outputs = state.get("agent_outputs", {})
    final_answer = format_report(query, outputs)
    return {"final_answer": final_answer}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(
    *,
    human_in_the_loop: bool = False,
    inject_analytics_error: bool = False,
) -> StateGraph:
    """Construct and return the compiled LangGraph workflow.

    Args:
        human_in_the_loop: If True, interrupt after supervisor so the user
            can review/modify the plan before agents execute.
        inject_analytics_error: If True, analytics node always returns an error.
            Used for testing error recovery.
    """
    workflow = StateGraph(GraphState)

    # Nodes
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("analytics", _make_analytics_node(inject_error=inject_analytics_error))
    workflow.add_node("research", _make_research_node())
    workflow.add_node("synthesize", synthesize)

    # Edges
    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_agents,
        {
            "analytics": "analytics",
            "research": "research",
            "synthesize": "synthesize",
        },
    )
    workflow.add_conditional_edges(
        "analytics",
        route_agents,
        {
            "research": "research",
            "synthesize": "synthesize",
        },
    )
    workflow.add_edge("research", "synthesize")
    workflow.add_edge("synthesize", END)

    # Checkpointer — always enabled for thread-based state persistence
    checkpointer = MemorySaver()

    # Human-in-the-loop: interrupt after supervisor, before agents execute
    interrupt_before = ["analytics", "research"] if human_in_the_loop else None

    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
    )


# Allow `python -m src.graph` for quick testing
if __name__ == "__main__":
    graph = build_graph()

    queries = [
        "Покажи ROI по каналам",
        "Какие тренды в AI маркетинге?",
        "Сравни наш ROI с рыночными бенчмарками",
    ]

    for q in queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {q}")
        print("=" * 60)
        config = {"configurable": {"thread_id": q}}
        result = graph.invoke({"query": q}, config)
        print(f"PLAN: {result.get('plan', [])}")
        print(result.get("final_answer", "No answer")[:500])
        print()
