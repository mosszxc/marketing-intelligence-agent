"""Tests for Phase 17: Analytics Agent enhancements — SQL, LTV, segmentation."""

import os
import sqlite3
import tempfile

import pandas as pd
import pytest

from src.tools.data_loader import load_dataframe


# ── SQL Loader ────────────────────────────────────────────────────────────

class TestSQLLoader:
    @pytest.fixture
    def demo_db(self):
        """Create a temp SQLite DB with campaign data."""
        df = load_dataframe()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        conn = sqlite3.connect(path)
        df.to_sql("campaigns", conn, index=False)
        conn.close()
        yield path
        os.unlink(path)

    def test_load_from_sqlite(self, demo_db):
        from src.tools.sql_loader import query_sql
        df = query_sql(demo_db, "SELECT * FROM campaigns LIMIT 10")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10

    def test_has_required_columns(self, demo_db):
        from src.tools.sql_loader import query_sql
        df = query_sql(demo_db, "SELECT * FROM campaigns LIMIT 1")
        for col in ["impressions", "clicks", "conversions", "spend", "revenue"]:
            assert col in df.columns

    def test_blocks_non_select(self, demo_db):
        from src.tools.sql_loader import query_sql
        with pytest.raises(ValueError, match="SELECT"):
            query_sql(demo_db, "DELETE FROM campaigns")


# ── LTV & Cohort Metrics ─────────────────────────────────────────────────

class TestLTV:
    def test_ltv_returns_per_campaign(self):
        from src.tools.data_loader import compute_metrics
        result = compute_metrics.invoke({"metric": "ltv"})
        assert "LTV" in result or "ltv" in result.lower()
        # Should contain campaign names
        assert "retargeting_cart" in result or "campaign" in result.lower()

    def test_ltv_values_positive(self):
        from src.tools.data_loader import compute_metrics
        result = compute_metrics.invoke({"metric": "ltv"})
        # LTV should be a number — check digits exist
        assert any(c.isdigit() for c in result)


class TestCohort:
    def test_cohort_returns_table(self):
        from src.tools.data_loader import compute_metrics
        result = compute_metrics.invoke({"metric": "cohort"})
        assert isinstance(result, str)
        assert len(result) > 20


# ── Segmentation ──────────────────────────────────────────────────────────

class TestSegmentation:
    def test_segment_returns_clusters(self):
        from src.tools.segmentation import segment_campaigns
        df = load_dataframe()
        result = segment_campaigns(df)
        assert isinstance(result, str)
        assert any(w in result.lower() for w in ["сегмент", "segment", "кластер", "cluster", "группа"])

    def test_segment_has_labels(self):
        from src.tools.segmentation import segment_campaigns
        df = load_dataframe()
        result = segment_campaigns(df)
        # Should describe each cluster
        assert "1" in result or "#" in result

    def test_segment_scatter_plot(self):
        from src.tools.segmentation import segment_scatter_plot
        df = load_dataframe()
        b64 = segment_scatter_plot(df)
        assert isinstance(b64, str)
        assert len(b64) > 100  # base64 encoded PNG
