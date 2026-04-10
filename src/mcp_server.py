"""MCP Server for the Marketing Intelligence Agent.

Exposes marketing analytics as tools for Claude Desktop / Cursor / any MCP client.

Usage:
    python -m src.mcp_server          # stdio transport (default for Claude Desktop)
    mcp install src/mcp_server.py     # register in Claude Desktop
"""

import uuid

from mcp.server.fastmcp import FastMCP

from src.graph import build_graph
from src.tools.data_loader import load_dataframe, _detect_group_column
from src.tools.interpreter import classify_anomalies, interpret_metrics

mcp = FastMCP("Marketing Intelligence Agent")


@mcp.tool()
def analyze_marketing(query: str) -> str:
    """Run a full marketing analysis query through the multi-agent pipeline.

    The system routes your question to the right agents (analytics, research,
    strategy) and returns a formatted report with metrics, charts description,
    and recommendations.

    Examples:
        - "ROI по каналам"
        - "Найди аномалии"
        - "Тренды AI маркетинга 2026"
        - "Куда перераспределить бюджет?"
    """
    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = graph.invoke({"query": query}, config)
    return result.get("final_answer", "No answer generated.")


@mcp.tool()
def get_campaign_metrics(campaign: str = "", metric: str = "summary") -> str:
    """Get marketing metrics from the campaign dataset.

    Args:
        campaign: Filter by campaign name (empty = all campaigns).
        metric: One of: roi, roas, cpa, ctr, conversion_rate, summary.

    Returns a formatted table with the computed metrics.
    """
    df = load_dataframe()
    group_col = _detect_group_column(df)

    if campaign:
        if campaign not in df[group_col].values:
            available = ", ".join(sorted(df[group_col].unique()))
            return f"Campaign '{campaign}' not found. Available: {available}"
        df = df[df[group_col] == campaign]

    return interpret_metrics(df, group_by=group_col if not campaign else "")


@mcp.tool()
def detect_anomalies(threshold: float = 2.0) -> str:
    """Detect and classify anomalies in campaign data.

    Returns prioritized list of problems (bot traffic, CPC spikes,
    junk placements) with impact scores — not raw z-score tables.

    Args:
        threshold: Z-score threshold for anomaly detection (default 2.0).
    """
    df = load_dataframe()
    return classify_anomalies(df, threshold=threshold)


if __name__ == "__main__":
    mcp.run()
