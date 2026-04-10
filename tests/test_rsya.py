"""Tests for RSY dataset integration — loader, metrics, anomalies, charts."""

import uuid
from pathlib import Path

import pandas as pd

RSYA_CSV = Path(__file__).parent.parent / "data" / "rsya_campaigns.csv"


class TestRSYALoader:
    def test_load_rsya_dataframe(self):
        from src.tools.data_loader import load_dataframe
        df = load_dataframe(str(RSYA_CSV))
        assert len(df) == 8688
        assert "campaign_id" in df.columns
        assert "ad_format" in df.columns
        assert "device" in df.columns

    def test_load_rsya_summary(self):
        from src.tools.data_loader import load_campaign_data
        summary = load_campaign_data.invoke({"path": str(RSYA_CSV)})
        assert "8688" in summary
        assert "campaign" in summary.lower()
        assert "RUB" in summary

    def test_rsya_has_all_campaigns(self):
        from src.tools.data_loader import load_dataframe
        df = load_dataframe(str(RSYA_CSV))
        campaigns = set(df["campaign_id"].unique())
        assert "retargeting_cart" in campaigns
        assert "brand_awareness" in campaigns
        assert "promo_seasonal" in campaigns
        assert len(campaigns) == 8


class TestRSYAMetrics:
    def test_metrics_by_campaign(self):
        from src.tools.data_loader import compute_metrics
        result = compute_metrics.invoke({"metric": "summary", "group_by": "campaign_id", "path": str(RSYA_CSV)})
        assert "retargeting_cart" in result
        assert "ROAS" in result
        assert "CPA" in result

    def test_metrics_by_ad_format(self):
        from src.tools.data_loader import compute_metrics
        result = compute_metrics.invoke({"metric": "ctr", "group_by": "ad_format", "path": str(RSYA_CSV)})
        assert "video" in result
        assert "text-image" in result
        assert "CTR" in result

    def test_metrics_by_device(self):
        from src.tools.data_loader import compute_metrics
        result = compute_metrics.invoke({"metric": "roi", "group_by": "device", "path": str(RSYA_CSV)})
        assert "desktop" in result
        assert "mobile" in result

    def test_roas_metric(self):
        from src.tools.data_loader import compute_metrics
        result = compute_metrics.invoke({"metric": "roas", "group_by": "campaign_id", "path": str(RSYA_CSV)})
        assert "ROAS" in result
        assert "retargeting_cart" in result


class TestRSYAAnomalies:
    def test_detects_rsya_anomalies(self):
        from src.tools.data_loader import detect_anomalies
        result = detect_anomalies.invoke({"threshold": 2.0, "path": str(RSYA_CSV)})
        assert "anomal" in result.lower() or "Found" in result

    def test_bot_traffic_detected(self):
        """Bot traffic anomaly on brand_awareness should show high clicks."""
        df = pd.read_csv(RSYA_CSV)
        bot = df[(df["campaign_id"] == "brand_awareness") & (df["ad_format"] == "video")
                 & (df["device"] == "mobile") & (df["date"].between("2026-03-15", "2026-03-20"))]
        assert len(bot) > 0
        assert bot["conversions"].sum() == 0
        assert bot["clicks"].mean() > 5000  # way above normal


class TestRSYACharts:
    def test_chart_by_campaign(self):
        from src.tools.charts import create_chart
        result = create_chart.invoke({
            "chart_type": "bar",
            "metric": "spend",
            "path": str(RSYA_CSV),
            "group_by": "campaign_id",
        })
        assert len(result) > 100  # base64 PNG

    def test_chart_by_device(self):
        from src.tools.charts import create_chart
        result = create_chart.invoke({
            "chart_type": "pie",
            "metric": "conversions",
            "path": str(RSYA_CSV),
            "group_by": "device",
        })
        assert len(result) > 100


class TestRSYAGraph:
    def test_graph_with_rsya_query(self):
        """Graph produces analytics output for RSY-related query."""
        from src.graph import build_graph
        graph = build_graph()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = graph.invoke({"query": "ROI по кампаниям"}, config)
        assert result.get("final_answer")
        assert "analytics" in result.get("agent_outputs", {})
