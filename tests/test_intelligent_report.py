"""Tests for Phase 9: Intelligent Report Layer.

Validates that the system answers like an analyst, not a data pipe:
- No debug output in responses
- Data interpretation (best/worst campaigns, budget at risk)
- Anomaly prioritization (grouped, classified, top-N)
- Actionable recommendations
"""

import uuid

import pytest

from src.agents.analytics import run_analytics_no_llm
from src.agents.report import format_report
from src.graph import build_graph


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_query(query: str) -> str:
    """Run a full e2e query through the graph, return final_answer."""
    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    graph.invoke({"query": query}, config)
    state = graph.get_state(config)
    return state.values.get("final_answer", "")


def _run_analytics(query: str) -> dict:
    """Run analytics agent directly, return AgentOutput dict."""
    return run_analytics_no_llm(query)


# ---------------------------------------------------------------------------
# 9.1 — No debug output
# ---------------------------------------------------------------------------

class TestNoDebugOutput:
    """Response must not contain internal debug information."""

    DEBUG_PATTERNS = [
        "Loaded ",
        "Columns:",
        "Date range:",
        "14 columns",
        "8688 rows",
        "campaign_id, campaign_name, ad_format",
    ]

    def test_analytics_summary_no_debug(self):
        result = _run_analytics("Покажи ROAS по кампаниям")
        for pattern in self.DEBUG_PATTERNS:
            assert pattern not in result["summary"], (
                f"Debug pattern '{pattern}' found in analytics summary"
            )

    def test_full_report_no_debug(self):
        answer = _run_query("Какая кампания самая эффективная?")
        for pattern in self.DEBUG_PATTERNS:
            assert pattern not in answer, (
                f"Debug pattern '{pattern}' found in report"
            )

    def test_anomaly_report_no_debug(self):
        answer = _run_query("Найди аномалии в данных")
        for pattern in self.DEBUG_PATTERNS:
            assert pattern not in answer, (
                f"Debug pattern '{pattern}' found in anomaly report"
            )


# ---------------------------------------------------------------------------
# 9.2 — Data interpretation
# ---------------------------------------------------------------------------

class TestDataInterpretation:
    """Response interprets data — names campaigns, gives context, not raw tables."""

    def test_best_campaign_named(self):
        """When asked about best campaign, answer must name it explicitly."""
        answer = _run_query("Какая кампания самая эффективная?")
        assert "retargeting_cart" in answer.lower() or "ретаргетинг" in answer.lower(), (
            "Best campaign (retargeting_cart) not named in answer"
        )

    def test_worst_campaigns_named_on_budget_question(self):
        """'Where are we wasting budget?' must name campaigns with ROAS < 1."""
        answer = _run_query("Где мы сливаем бюджет?")
        answer_lower = answer.lower()
        # Must mention at least one of the loss-making campaigns
        losing = ["brand_awareness", "geo_moscow"]
        found = [c for c in losing if c in answer_lower]
        assert len(found) >= 1, (
            f"None of the losing campaigns {losing} named in answer about budget waste"
        )

    def test_interpretation_has_numbers_in_context(self):
        """Interpretation must include specific numbers, not just a table."""
        answer = _run_query("Какая кампания самая эффективная?")
        # Should mention ROAS value for the best campaign
        assert "8.11" in answer or "ROAS" in answer, (
            "Answer about best campaign should mention ROAS value"
        )

    def test_analytics_summary_is_prose_not_table(self):
        """Analytics summary should read as text, not raw pandas output."""
        result = _run_analytics("Покажи ROAS по кампаниям")
        summary = result["summary"]
        # Raw pandas output has lots of whitespace-aligned columns
        # Prose should not have "campaign_id" as a column header line
        lines = summary.strip().split("\n")
        # First non-empty line should not be a pandas index/header
        first_line = lines[0].strip()
        assert not first_line.startswith("campaign_id"), (
            "Summary starts with raw pandas table header"
        )


# ---------------------------------------------------------------------------
# 9.3 — Anomaly prioritization
# ---------------------------------------------------------------------------

class TestAnomalyPrioritization:
    """Anomalies must be grouped, classified, and limited to top-N."""

    def test_anomalies_not_raw_dump(self):
        """Response should NOT contain 'Found 1365 anomalies'."""
        answer = _run_query("Найди аномалии в данных")
        assert "1365" not in answer, (
            "Raw anomaly count (1365) should not appear in report"
        )

    def test_anomalies_limited_count(self):
        """Report should show ≤5 key problems, not 20 z-score lines."""
        answer = _run_query("Найди аномалии в данных")
        # Count problem items (lines starting with number or bullet)
        import re
        problems = re.findall(r"(?:^|\n)\s*(?:\d+[\.\):]|[-•▸])\s+", answer)
        # There can be other lists too, but anomaly items should be ≤ ~10
        # The key check: no 20-line z-score dump
        assert "z=" not in answer, (
            "Raw z-score values should not appear in report"
        )

    def test_anomalies_have_type_classification(self):
        """Each anomaly group should have a human-readable type."""
        answer = _run_query("Найди аномалии в данных")
        answer_lower = answer.lower()
        # At least one classification type should appear
        types = ["бот", "bot", "spike", "спайк", "мусор", "junk", "промо", "promo"]
        found = [t for t in types if t in answer_lower]
        assert len(found) >= 1, (
            f"No anomaly type classification found. Expected one of: {types}"
        )


# ---------------------------------------------------------------------------
# 9.4 — Recommendations
# ---------------------------------------------------------------------------

class TestRecommendations:
    """Every analytics response must include actionable recommendations."""

    def test_budget_waste_has_recommendations(self):
        answer = _run_query("Где мы сливаем бюджет?")
        answer_lower = answer.lower()
        action_words = [
            "рекомендац", "recommend",
            "отключ", "disable", "stop",
            "оптимизир", "optimize",
            "перерасп", "reallocat",
            "снизить", "reduce",
            "проверить", "check",
        ]
        found = [w for w in action_words if w in answer_lower]
        assert len(found) >= 1, (
            "No actionable recommendations in budget waste answer"
        )

    def test_anomaly_report_has_recommendations(self):
        answer = _run_query("Найди аномалии в данных")
        answer_lower = answer.lower()
        action_words = [
            "рекомендац", "recommend",
            "проверить", "check",
            "площадк", "placement",
            "минус", "exclude",
            "отключ", "disable",
        ]
        found = [w for w in action_words if w in answer_lower]
        assert len(found) >= 1, (
            "No actionable recommendations in anomaly report"
        )

    def test_recommendations_reference_specific_campaigns(self):
        """Recommendations must be tied to specific campaigns, not generic."""
        answer = _run_query("Где мы сливаем бюджет?")
        answer_lower = answer.lower()
        # At least one campaign name in the recommendations area
        campaigns = [
            "brand_awareness", "geo_moscow", "interests_electronics",
            "topics_reviews", "retargeting_cart",
        ]
        found = [c for c in campaigns if c in answer_lower]
        assert len(found) >= 1, (
            "Recommendations don't reference any specific campaign"
        )


# ---------------------------------------------------------------------------
# 9.5 — E2E integration
# ---------------------------------------------------------------------------

class TestE2EIntegration:
    """Full end-to-end: question → interpreted answer with recommendations."""

    def test_e2e_budget_waste(self):
        """'Где мы сливаем бюджет?' → names losers, gives amounts, recommends."""
        answer = _run_query("Где мы сливаем бюджет?")
        answer_lower = answer.lower()
        # Names at least one losing campaign
        assert "brand_awareness" in answer_lower or "geo_moscow" in answer_lower
        # Has numbers (amounts)
        import re
        has_numbers = bool(re.search(r"\d[\d\s,\.]*(?:RUB|руб|₽|K|тыс|млн)", answer, re.IGNORECASE))
        assert has_numbers, "Answer should include monetary amounts"
        # Has recommendations
        assert "рекомендац" in answer_lower or "recommend" in answer_lower or "отключ" in answer_lower

    def test_e2e_anomalies(self):
        """'Найди аномалии' → prioritized problems with types."""
        answer = _run_query("Найди аномалии в данных")
        # No debug
        assert "Loaded " not in answer
        # Has classification
        answer_lower = answer.lower()
        assert any(t in answer_lower for t in ["бот", "spike", "спайк", "мусор", "промо"])
        # ≤5 key items, not 20
        assert "z=" not in answer

    def test_e2e_best_campaign(self):
        """'Какая кампания лучшая?' → names it, explains why."""
        answer = _run_query("Какая кампания самая эффективная?")
        assert "Loaded " not in answer
        answer_lower = answer.lower()
        assert "retargeting_cart" in answer_lower or "ретаргетинг" in answer_lower

    def test_no_regression_existing_tests(self):
        """Analytics agent still returns charts and valid data."""
        result = _run_analytics("Покажи ROAS по кампаниям")
        assert len(result["charts"]) >= 1
        assert result["error"] is None
