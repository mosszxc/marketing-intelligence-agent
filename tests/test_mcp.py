"""Tests for Phase 12: MCP Server."""

from mcp.server.fastmcp import FastMCP


class TestMCPServerImport:
    def test_server_creates(self):
        from src.mcp_server import mcp
        assert isinstance(mcp, FastMCP)

    def test_server_has_tools(self):
        # FastMCP registers tools internally; verify our functions exist
        from src import mcp_server
        assert hasattr(mcp_server, 'analyze_marketing')
        assert hasattr(mcp_server, 'get_campaign_metrics')
        assert hasattr(mcp_server, 'detect_anomalies')


class TestAnalyzeMarketing:
    def test_returns_string_with_analytics(self):
        from src.mcp_server import analyze_marketing
        result = analyze_marketing("ROI по каналам")
        assert isinstance(result, str)
        assert len(result) > 50
        assert "аналитика" in result.lower() or "roas" in result.lower() or "roi" in result.lower()

    def test_handles_research_query(self):
        from src.mcp_server import analyze_marketing
        result = analyze_marketing("Тренды AI маркетинга")
        assert isinstance(result, str)
        assert len(result) > 50

    def test_handles_strategy_query(self):
        from src.mcp_server import analyze_marketing
        result = analyze_marketing("Куда перераспределить бюджет?")
        assert isinstance(result, str)
        assert "стратег" in result.lower() or "бюджет" in result.lower() or "%" in result


class TestGetCampaignMetrics:
    def test_returns_all_campaigns(self):
        from src.mcp_server import get_campaign_metrics
        result = get_campaign_metrics()
        assert isinstance(result, str)
        assert "ROAS" in result or "roas" in result.lower()

    def test_returns_specific_campaign(self):
        from src.mcp_server import get_campaign_metrics
        result = get_campaign_metrics(campaign="retargeting_cart")
        assert "retargeting_cart" in result


class TestDetectAnomalies:
    def test_returns_anomalies(self):
        from src.mcp_server import detect_anomalies
        result = detect_anomalies()
        assert isinstance(result, str)
        assert len(result) > 20
        # Should have classified anomalies or "no anomalies"
        assert "аномал" in result.lower() or "проблем" in result.lower() or "не обнаружено" in result.lower()


class TestMCPConfig:
    def test_config_file_exists(self):
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "mcp-config.json",
        )
        assert os.path.isfile(config_path), "mcp-config.json should exist"

    def test_config_is_valid_json(self):
        import json
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "mcp-config.json",
        )
        with open(config_path) as f:
            config = json.load(f)
        assert "mcpServers" in config
