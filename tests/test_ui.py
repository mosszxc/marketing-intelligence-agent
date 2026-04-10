"""Tests for the Streamlit UI module (import and logic checks, no browser)."""

import uuid


class TestUIImports:
    def test_app_module_imports(self):
        """The UI app module can be imported without errors."""
        # We can't fully import streamlit app (needs runtime), but we can
        # verify the module file is valid Python.
        import ast
        from pathlib import Path

        app_path = Path(__file__).parent.parent / "src" / "ui" / "app.py"
        source = app_path.read_text()
        tree = ast.parse(source)
        assert tree is not None

    def test_graph_build_for_ui(self):
        """Graph used by UI builds correctly."""
        from src.graph import build_graph

        graph = build_graph()
        assert graph is not None

    def test_base64_chart_decode(self):
        """Charts from analytics are valid base64 that decodes to PNG."""
        import base64

        from src.agents.analytics import run_analytics_no_llm

        result = run_analytics_no_llm("ROI по каналам")
        charts = result.get("charts", [])
        assert len(charts) > 0

        decoded = base64.b64decode(charts[0])
        # PNG magic bytes
        assert decoded[:4] == b"\x89PNG"

    def test_example_queries_produce_output(self):
        """All sidebar example queries produce non-empty results."""
        from src.graph import build_graph

        graph = build_graph()
        examples = [
            "Покажи ROI по каналам",
            "Какие аномалии в расходах?",
            "Тренды AI маркетинга 2026",
            "Сравни ROI с рыночными бенчмарками",
        ]
        for q in examples:
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            result = graph.invoke({"query": q}, config)
            assert result.get("final_answer"), f"No answer for: {q}"
            assert result.get("plan"), f"No plan for: {q}"
