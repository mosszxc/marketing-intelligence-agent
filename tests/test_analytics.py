"""Tests for analytics tools and agent (no LLM required).

Uses demo_campaigns.csv for explicit-path tests and default (RSY) for agent tests.
"""

import base64
from pathlib import Path

import pandas as pd

from src.tools.data_loader import load_dataframe, load_campaign_data, compute_metrics, detect_anomalies
from src.tools.charts import create_chart
from src.agents.analytics import run_analytics_no_llm


DEMO_PATH = str(Path(__file__).resolve().parent.parent / "data" / "demo_campaigns.csv")


class TestDataLoader:
    def test_load_dataframe(self):
        df = load_dataframe(DEMO_PATH)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 72
        assert set(df.columns) >= {"date", "channel", "spend", "revenue"}

    def test_load_dataframe_default(self):
        """Default dataset is RSY (8688 rows)."""
        df = load_dataframe()
        assert len(df) == 8688

    def test_load_campaign_data_tool(self):
        result = load_campaign_data.invoke({"path": DEMO_PATH})
        assert "72 rows" in result
        assert "google_ads" in result

    def test_load_invalid_path(self):
        try:
            load_dataframe("/nonexistent/file.csv")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass


class TestComputeMetrics:
    def test_roi_by_channel(self):
        result = compute_metrics.invoke({"metric": "roi", "group_by": "channel", "path": DEMO_PATH})
        assert "ROI" in result
        assert "google_ads" in result

    def test_cpa_by_channel(self):
        result = compute_metrics.invoke({"metric": "cpa", "group_by": "channel", "path": DEMO_PATH})
        assert "CPA" in result

    def test_summary(self):
        result = compute_metrics.invoke({"metric": "summary", "group_by": "channel", "path": DEMO_PATH})
        assert "ROAS" in result
        assert "CPA" in result
        assert "CTR" in result

    def test_roi_values_are_positive(self):
        """All channels should have positive ROI in the demo dataset."""
        df = load_dataframe(DEMO_PATH)
        by_channel = df.groupby("channel").agg({"spend": "sum", "revenue": "sum"})
        by_channel["roi"] = (by_channel["revenue"] - by_channel["spend"]) / by_channel["spend"]
        assert (by_channel["roi"] > 0).all()

    def test_unknown_metric(self):
        result = compute_metrics.invoke({"metric": "xyz"})
        assert "Unknown metric" in result


class TestAnomalyDetection:
    def test_detects_anomalies_demo(self):
        result = detect_anomalies.invoke({"threshold": 2.0, "path": DEMO_PATH})
        assert "anomal" in result.lower() or "Found" in result
        assert "tiktok_ads" in result or "email" in result

    def test_detects_anomalies_default(self):
        """Default (RSY) dataset should also detect anomalies."""
        result = detect_anomalies.invoke({"threshold": 2.0})
        assert "Found" in result


class TestCharts:
    def test_bar_chart_revenue(self):
        result = create_chart.invoke({"chart_type": "bar", "metric": "revenue"})
        decoded = base64.b64decode(result)
        assert decoded[:4] == b"\x89PNG"

    def test_line_chart_spend(self):
        result = create_chart.invoke({"chart_type": "line", "metric": "spend"})
        decoded = base64.b64decode(result)
        assert decoded[:4] == b"\x89PNG"

    def test_pie_chart_conversions(self):
        result = create_chart.invoke({"chart_type": "pie", "metric": "conversions"})
        decoded = base64.b64decode(result)
        assert decoded[:4] == b"\x89PNG"

    def test_unknown_chart_type(self):
        result = create_chart.invoke({"chart_type": "scatter", "metric": "spend"})
        assert "Unknown chart_type" in result

    def test_unknown_metric(self):
        result = create_chart.invoke({"chart_type": "bar", "metric": "xyz"})
        assert "Unknown metric" in result


class TestAnalyticsAgentNoLLM:
    def test_roi_query(self):
        result = run_analytics_no_llm("Покажи ROI по каналам")
        assert result["summary"]
        assert "ROAS" in result["summary"]
        assert len(result["charts"]) >= 1

    def test_anomaly_query(self):
        result = run_analytics_no_llm("Найди аномалии в данных")
        assert result["summary"]
        assert len(result["charts"]) >= 1

    def test_generic_query(self):
        result = run_analytics_no_llm("Общая сводка по кампаниям")
        assert result["summary"]
        assert "8688 rows" in result["summary"]
