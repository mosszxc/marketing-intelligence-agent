"""Tool for generating marketing charts as base64 PNG images."""

import base64
import io

import matplotlib
import matplotlib.pyplot as plt
from langchain_core.tools import tool

from src.tools.data_loader import load_dataframe

matplotlib.use("Agg")  # Non-interactive backend


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert matplotlib figure to base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@tool
def create_chart(chart_type: str, metric: str, title: str = "") -> str:
    """Generate a chart from campaign data as a base64 PNG image.

    Args:
        chart_type: One of 'bar', 'line', 'pie'.
        metric: Column to visualize — 'spend', 'revenue', 'roi', 'conversions', 'clicks', 'ctr'.
        title: Optional chart title.

    Returns a base64-encoded PNG image string.
    """
    df = load_dataframe()

    # Compute derived metrics
    if metric == "roi":
        pivot_data = df.groupby("channel").agg({"spend": "sum", "revenue": "sum"})
        pivot_data["roi"] = (pivot_data["revenue"] - pivot_data["spend"]) / pivot_data["spend"] * 100
        values = pivot_data["roi"]
    elif metric == "ctr":
        pivot_data = df.groupby("channel").agg({"clicks": "sum", "impressions": "sum"})
        pivot_data["ctr"] = pivot_data["clicks"] / pivot_data["impressions"] * 100
        values = pivot_data["ctr"]
    elif metric in ("spend", "revenue", "conversions", "clicks", "impressions"):
        values = df.groupby("channel")[metric].sum()
    else:
        return f"Unknown metric: {metric}. Use: spend, revenue, roi, conversions, clicks, ctr."

    chart_title = title or f"{metric.upper()} by Channel"

    fig, ax = plt.subplots(figsize=(10, 6))

    if chart_type == "bar":
        values.plot(kind="bar", ax=ax, color=["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", "#EECA3B"])
        ax.set_ylabel(metric.upper())
        ax.set_xlabel("")
        plt.xticks(rotation=45)

    elif chart_type == "line":
        # Line chart: metric over time per channel
        for channel in df["channel"].unique():
            ch_data = df[df["channel"] == channel].sort_values("date")
            if metric == "roi":
                y = (ch_data["revenue"] - ch_data["spend"]) / ch_data["spend"] * 100
            elif metric == "ctr":
                y = ch_data["clicks"] / ch_data["impressions"] * 100
            else:
                y = ch_data[metric]
            ax.plot(ch_data["date"], y, label=channel, marker="o", markersize=4)
        ax.legend(loc="best", fontsize=8)
        ax.set_ylabel(metric.upper())
        plt.xticks(rotation=45)

    elif chart_type == "pie":
        values.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90)
        ax.set_ylabel("")

    else:
        plt.close(fig)
        return f"Unknown chart_type: {chart_type}. Use: bar, line, pie."

    ax.set_title(chart_title)
    fig.tight_layout()

    return _fig_to_base64(fig)
