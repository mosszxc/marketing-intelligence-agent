"""Tests for the LangGraph workflow — routing, synthesis, e2e."""

import uuid

from src.agents.supervisor import _classify_keywords
from src.agents.report import format_report
from src.graph import build_graph


def _config():
    """Generate a unique thread config for each test."""
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


class TestSupervisorRouting:
    def test_analytics_only(self):
        plan = _classify_keywords("Покажи ROI по каналам")
        assert plan == ["analytics"]

    def test_research_only(self):
        plan = _classify_keywords("Какие тренды в AI маркетинге?")
        assert plan == ["research"]

    def test_both_agents(self):
        plan = _classify_keywords("Сравни наш ROI с рыночными бенчмарками")
        assert "analytics" in plan
        assert "research" in plan

    def test_analytics_keywords(self):
        for q in ["расход по каналам", "CPA за месяц", "аномалии в данных", "бюджет кампании"]:
            plan = _classify_keywords(q)
            assert "analytics" in plan, f"Expected analytics for: {q}"

    def test_research_keywords(self):
        for q in ["новости рынка", "конкуренты", "прогноз индустрии", "market trends"]:
            plan = _classify_keywords(q)
            assert "research" in plan, f"Expected research for: {q}"

    def test_default_both(self):
        """Unknown queries route to both agents."""
        plan = _classify_keywords("привет")
        assert plan == ["analytics", "research"]


class TestReportAgent:
    def test_analytics_only_report(self):
        outputs = {
            "analytics": {
                "summary": "ROI: Google Ads 216%, Meta 202%",
                "data": {},
                "charts": ["base64png"],
                "sources": [],
                "error": None,
            }
        }
        report = format_report("ROI по каналам", outputs)
        assert "# Отчёт:" in report
        assert "Аналитика" in report
        assert "ROI: Google Ads" in report
        assert "рафиков: 1" in report  # "Графиков" or "графиков"
        assert "Исследование рынка" not in report

    def test_research_only_report(self):
        outputs = {
            "research": {
                "summary": "AI маркетинг растёт на 28% YoY",
                "data": {},
                "charts": [],
                "sources": [{"url": "https://example.com", "title": "Source 1"}],
                "error": None,
            }
        }
        report = format_report("тренды", outputs)
        assert "Исследование рынка" in report
        assert "28% YoY" in report
        assert "Источники" in report
        assert "example.com" in report
        assert "Аналитика данных" not in report

    def test_both_agents_report(self):
        outputs = {
            "analytics": {
                "summary": "ROI 216%",
                "data": {},
                "charts": ["chart1"],
                "sources": [],
                "error": None,
            },
            "research": {
                "summary": "Рынок растёт",
                "data": {},
                "charts": [],
                "sources": [{"url": "https://example.com"}],
                "error": None,
            },
        }
        report = format_report("ROI vs рынок", outputs)
        assert "Аналитика" in report
        assert "Исследование рынка" in report
        assert "Источники" in report


class TestGraphE2E:
    def test_analytics_only_query(self):
        graph = build_graph()
        result = graph.invoke({"query": "Покажи ROI по каналам"}, _config())
        assert result["plan"] == ["analytics"]
        assert "analytics" in result["agent_outputs"]
        assert "research" not in result["agent_outputs"]
        assert "Аналитика" in result["final_answer"]

    def test_research_only_query(self):
        graph = build_graph()
        result = graph.invoke({"query": "Какие тренды на рынке?"}, _config())
        assert result["plan"] == ["research"]
        assert "research" in result["agent_outputs"]
        assert "analytics" not in result["agent_outputs"]
        assert "Исследование рынка" in result["final_answer"]

    def test_both_agents_query(self):
        graph = build_graph()
        result = graph.invoke({"query": "Сравни наш ROI с рыночными бенчмарками"}, _config())
        assert "analytics" in result["plan"]
        assert "research" in result["plan"]
        assert "analytics" in result["agent_outputs"]
        assert "research" in result["agent_outputs"]
        assert "Аналитика" in result["final_answer"]
        assert "Исследование рынка" in result["final_answer"]

    def test_report_has_sources(self):
        graph = build_graph()
        result = graph.invoke({"query": "Что нового на рынке рекламы?"}, _config())
        assert "Источники" in result["final_answer"]
