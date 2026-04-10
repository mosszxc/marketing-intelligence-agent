"""Tests for Phase 7: Production LangGraph Features.

TDD — tests written before implementation.
Covers: checkpointing, human-in-the-loop, streaming, error recovery.
"""

import uuid

from src.graph import build_graph


# ---------------------------------------------------------------------------
# 7.1 Checkpointing + Memory
# ---------------------------------------------------------------------------

class TestCheckpointing:
    def test_graph_accepts_thread_config(self):
        """Graph invoked with thread_id config does not error."""
        graph = build_graph()
        config = {"configurable": {"thread_id": "test-thread-1"}}
        result = graph.invoke({"query": "ROI по каналам"}, config)
        assert result["final_answer"]
        assert "analytics" in result["agent_outputs"]

    def test_thread_isolation(self):
        """Different thread_ids produce independent state."""
        graph = build_graph()
        config_a = {"configurable": {"thread_id": str(uuid.uuid4())}}
        config_b = {"configurable": {"thread_id": str(uuid.uuid4())}}

        result_a = graph.invoke({"query": "ROI по каналам"}, config_a)
        result_b = graph.invoke({"query": "Тренды на рынке"}, config_b)

        # Thread A got analytics, thread B got research — independent
        assert "analytics" in result_a["agent_outputs"]
        assert "research" in result_b["agent_outputs"]

    def test_state_persists_across_invocations(self):
        """Second invoke on same thread_id can access checkpointed state."""
        graph = build_graph()
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # First query
        graph.invoke({"query": "ROI по каналам"}, config)

        # Get the state from checkpoint — it should exist
        state = graph.get_state(config)
        assert state is not None
        assert state.values.get("query") == "ROI по каналам"


# ---------------------------------------------------------------------------
# 7.2 Human-in-the-loop
# ---------------------------------------------------------------------------

class TestHumanInTheLoop:
    def test_interrupt_returns_plan_without_execution(self):
        """With HITL enabled, graph stops after supervisor — plan exists but no agent_outputs."""
        graph = build_graph(human_in_the_loop=True)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        # First invoke — should interrupt after supervisor
        graph.invoke({"query": "ROI по каналам"}, config)

        # Plan should be set, but agents should NOT have run yet
        state = graph.get_state(config)
        assert state.values.get("plan") == ["analytics"]
        assert state.values.get("agent_outputs", {}) == {}

    def test_resume_executes_agents(self):
        """After interrupt, resuming with None executes the planned agents."""
        graph = build_graph(human_in_the_loop=True)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        # Interrupt after supervisor
        graph.invoke({"query": "ROI по каналам"}, config)

        # Resume — execute the plan
        result = graph.invoke(None, config)

        assert "analytics" in result["agent_outputs"]
        assert result["final_answer"]
        assert "Аналитика данных" in result["final_answer"]

    def test_resume_with_modified_plan(self):
        """User can modify the plan before resuming."""
        graph = build_graph(human_in_the_loop=True)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        # Interrupt — supervisor chose both agents
        graph.invoke({"query": "Сравни ROI с бенчмарками"}, config)

        state = graph.get_state(config)
        assert "analytics" in state.values.get("plan", [])
        assert "research" in state.values.get("plan", [])

        # User overrides: only analytics
        graph.update_state(config, {"plan": ["analytics"]})

        # Resume
        result = graph.invoke(None, config)

        assert "analytics" in result["agent_outputs"]
        assert "research" not in result["agent_outputs"]


# ---------------------------------------------------------------------------
# 7.3 Streaming
# ---------------------------------------------------------------------------

class TestStreaming:
    def test_stream_yields_node_updates(self):
        """stream_mode='updates' yields dict with node names as keys."""
        graph = build_graph()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        node_names = []
        for chunk in graph.stream(
            {"query": "ROI по каналам"}, config, stream_mode="updates"
        ):
            node_names.extend(chunk.keys())

        assert "supervisor" in node_names
        assert "analytics" in node_names
        assert "synthesize" in node_names

    def test_stream_contains_all_planned_agents(self):
        """All agents from plan appear in stream for a both-agents query."""
        graph = build_graph()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        node_names = []
        for chunk in graph.stream(
            {"query": "Сравни ROI с рыночными бенчмарками"},
            config,
            stream_mode="updates",
        ):
            node_names.extend(chunk.keys())

        assert "supervisor" in node_names
        assert "analytics" in node_names
        assert "research" in node_names
        assert "synthesize" in node_names


# ---------------------------------------------------------------------------
# 7.4 Error Recovery
# ---------------------------------------------------------------------------

class TestErrorRecovery:
    def test_agent_error_does_not_crash_graph(self):
        """If an agent node raises, graph still completes with partial results."""
        graph = build_graph(inject_analytics_error=True)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        result = graph.invoke(
            {"query": "Сравни ROI с бенчмарками"}, config
        )

        # Graph completed — final_answer exists
        assert result.get("final_answer")
        # Analytics errored but research succeeded
        analytics_out = result["agent_outputs"].get("analytics", {})
        assert analytics_out.get("error") is not None
        assert "research" in result["agent_outputs"]

    def test_partial_results_in_report(self):
        """Report includes error message when one agent failed."""
        graph = build_graph(inject_analytics_error=True)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        result = graph.invoke(
            {"query": "Сравни ROI с бенчмарками"}, config
        )

        answer = result["final_answer"]
        # Research section should be present
        assert "Исследование рынка" in answer
        # Error indication should be present
        assert "ошибк" in answer.lower() or "error" in answer.lower()

    def test_single_agent_error_still_returns(self):
        """Analytics-only query with error still returns a report."""
        graph = build_graph(inject_analytics_error=True)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        result = graph.invoke({"query": "ROI по каналам"}, config)

        assert result.get("final_answer")
        assert result["agent_outputs"]["analytics"].get("error") is not None
