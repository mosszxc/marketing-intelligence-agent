"""Tool for generating marketing charts as base64 PNG images.

Supports both demo (channel-level) and RSY (campaign-level) datasets.
Auto-detects grouping column when group_by is not specified.
"""

import base64
import io

import matplotlib
import matplotlib.pyplot as plt
from langchain_core.tools import tool

from src.tools.data_loader import load_dataframe, _detect_group_column

matplotlib.use("Agg")

# Design system: blue data + amber highlights
CHART_COLORS = [
    "#1E40AF", "#3B82F6", "#60A5FA", "#F59E0B",
    "#10B981", "#8B5CF6", "#EF4444", "#06B6D4",
]
CHART_BG = "#F8FAFC"
CHART_TEXT = "#1E3A8A"
CHART_GRID = "#E2E8F0"


def _apply_style(fig, ax):
    """Apply design system styling to matplotlib chart."""
    fig.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)
    ax.tick_params(colors=CHART_TEXT, labelsize=9)
    ax.xaxis.label.set_color(CHART_TEXT)
    ax.yaxis.label.set_color(CHART_TEXT)
    ax.title.set_color(CHART_TEXT)
    ax.title.set_fontsize(14)
    ax.title.set_fontweight("bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(CHART_GRID)
    ax.spines["bottom"].set_color(CHART_GRID)
    ax.grid(axis="y", color=CHART_GRID, linewidth=0.5, alpha=0.7)


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert matplotlib figure to base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@tool
def create_chart(
    chart_type: str,
    metric: str,
    title: str = "",
    group_by: str = "",
    path: str = "",
) -> str:
    """Generate a chart from campaign data as a base64 PNG image.

    Args:
        chart_type: One of 'bar', 'line', 'pie'.
        metric: Column or derived metric — 'spend', 'revenue', 'roi', 'roas',
                'conversions', 'clicks', 'ctr', 'impressions'.
        title: Optional chart title.
        group_by: Group data by column (campaign_id, channel, ad_format, device).
                  Empty = auto-detect.
        path: Optional CSV path. Empty = default dataset.

    Returns a base64-encoded PNG image string.
    """
    df = load_dataframe(path or None)

    if not group_by:
        group_by = _detect_group_column(df)

    if group_by not in df.columns:
        return f"Column '{group_by}' not found. Available: {', '.join(df.columns)}"

    # Compute values
    if metric == "roi":
        pivot = df.groupby(group_by).agg({"spend": "sum", "revenue": "sum"})
        pivot["roi"] = (pivot["revenue"] - pivot["spend"]) / pivot["spend"].replace(0, 1) * 100
        values = pivot["roi"]
    elif metric == "roas":
        pivot = df.groupby(group_by).agg({"spend": "sum", "revenue": "sum"})
        pivot["roas"] = pivot["revenue"] / pivot["spend"].replace(0, 1)
        values = pivot["roas"]
    elif metric == "ctr":
        pivot = df.groupby(group_by).agg({"clicks": "sum", "impressions": "sum"})
        pivot["ctr"] = pivot["clicks"] / pivot["impressions"].replace(0, 1) * 100
        values = pivot["ctr"]
    elif metric in ("spend", "revenue", "conversions", "clicks", "impressions"):
        values = df.groupby(group_by)[metric].sum()
    else:
        return f"Unknown metric: {metric}. Use: spend, revenue, roi, roas, conversions, clicks, ctr."

    chart_title = title or f"{metric.upper()} by {group_by.replace('_', ' ').title()}"

    fig, ax = plt.subplots(figsize=(10, 5.5))

    if chart_type == "bar":
        colors = CHART_COLORS[:len(values)]
        values.plot(kind="bar", ax=ax, color=colors, edgecolor="none", width=0.7)
        ax.set_ylabel(metric.upper(), fontsize=10, fontweight="600")
        ax.set_xlabel("")
        plt.xticks(rotation=45, ha="right")

    elif chart_type == "line":
        groups = df[group_by].unique()
        for i, grp in enumerate(groups):
            grp_data = df[df[group_by] == grp].groupby("date").agg({
                "spend": "sum", "revenue": "sum",
                "clicks": "sum", "impressions": "sum",
                "conversions": "sum",
            }).sort_index()
            if metric == "roi":
                y = (grp_data["revenue"] - grp_data["spend"]) / grp_data["spend"].replace(0, 1) * 100
            elif metric == "roas":
                y = grp_data["revenue"] / grp_data["spend"].replace(0, 1)
            elif metric == "ctr":
                y = grp_data["clicks"] / grp_data["impressions"].replace(0, 1) * 100
            else:
                y = grp_data[metric]
            color = CHART_COLORS[i % len(CHART_COLORS)]
            label = str(grp)[:25]
            ax.plot(y.index, y.values, label=label, marker="o", markersize=3,
                    color=color, linewidth=1.5, alpha=0.85)
        ax.legend(loc="best", fontsize=7, framealpha=0.9, edgecolor=CHART_GRID, ncol=2)
        ax.set_ylabel(metric.upper(), fontsize=10, fontweight="600")
        plt.xticks(rotation=45, ha="right")

    elif chart_type == "pie":
        values_positive = values.clip(lower=0)
        if values_positive.sum() == 0:
            plt.close(fig)
            return "No positive values to chart."
        colors = CHART_COLORS[:len(values_positive)]
        values_positive.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90,
                             colors=colors, textprops={"fontsize": 8, "color": CHART_TEXT})
        ax.set_ylabel("")

    else:
        plt.close(fig)
        return f"Unknown chart_type: {chart_type}. Use: bar, line, pie."

    ax.set_title(chart_title, pad=16)
    _apply_style(fig, ax)
    fig.tight_layout()

    return _fig_to_base64(fig)
