"""Tool for loading and validating marketing campaign CSV data."""

from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

REQUIRED_COLUMNS = {"date", "channel", "impressions", "clicks", "conversions", "spend", "revenue"}
DEFAULT_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "demo_campaigns.csv"


def load_dataframe(path: str | None = None) -> pd.DataFrame:
    """Load CSV into DataFrame and validate columns.

    Returns the DataFrame directly — used by other tools and tests.
    """
    csv_path = Path(path) if path else DEFAULT_CSV

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["date"])
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    return df


@tool
def load_campaign_data(path: str = "") -> str:
    """Load marketing campaign data from a CSV file.

    Returns a summary of the dataset: shape, columns, date range, channels.
    If path is empty, loads the built-in demo dataset.
    """
    df = load_dataframe(path or None)

    summary = (
        f"Loaded {len(df)} rows, {len(df.columns)} columns.\n"
        f"Columns: {', '.join(df.columns)}\n"
        f"Date range: {df['date'].min().date()} to {df['date'].max().date()}\n"
        f"Channels: {', '.join(sorted(df['channel'].unique()))}\n"
        f"Total spend: {df['spend'].sum():,.0f} RUB\n"
        f"Total revenue: {df['revenue'].sum():,.0f} RUB"
    )
    return summary


@tool
def compute_metrics(metric: str, group_by: str = "channel") -> str:
    """Compute marketing metrics from campaign data.

    Args:
        metric: One of 'roi', 'cpa', 'ctr', 'conversion_rate', 'summary'.
        group_by: Group results by 'channel', 'date', or 'channel_date'.

    Returns a formatted table with the computed metric.
    """
    df = load_dataframe()

    if group_by == "channel_date":
        grouped = df.groupby(["channel", pd.Grouper(key="date", freq="ME")])
    elif group_by == "date":
        grouped = df.groupby(pd.Grouper(key="date", freq="ME"))
    else:
        grouped = df.groupby("channel")

    agg = grouped.agg({
        "impressions": "sum",
        "clicks": "sum",
        "conversions": "sum",
        "spend": "sum",
        "revenue": "sum",
    })

    if metric == "roi":
        agg["ROI"] = ((agg["revenue"] - agg["spend"]) / agg["spend"] * 100).round(1)
        result = agg[["spend", "revenue", "ROI"]].to_string()
    elif metric == "cpa":
        agg["CPA"] = (agg["spend"] / agg["conversions"]).round(0)
        result = agg[["conversions", "spend", "CPA"]].to_string()
    elif metric == "ctr":
        agg["CTR%"] = (agg["clicks"] / agg["impressions"] * 100).round(2)
        result = agg[["impressions", "clicks", "CTR%"]].to_string()
    elif metric == "conversion_rate":
        agg["CR%"] = (agg["conversions"] / agg["clicks"] * 100).round(2)
        result = agg[["clicks", "conversions", "CR%"]].to_string()
    elif metric == "summary":
        agg["ROI"] = ((agg["revenue"] - agg["spend"]) / agg["spend"] * 100).round(1)
        agg["CPA"] = (agg["spend"] / agg["conversions"]).round(0)
        agg["CTR%"] = (agg["clicks"] / agg["impressions"] * 100).round(2)
        result = agg[["spend", "revenue", "ROI", "CPA", "CTR%"]].to_string()
    else:
        result = f"Unknown metric: {metric}. Use one of: roi, cpa, ctr, conversion_rate, summary."

    return f"Metric: {metric} | Grouped by: {group_by}\n\n{result}"


@tool
def detect_anomalies(threshold: float = 2.0) -> str:
    """Detect anomalies in campaign data using z-score method.

    Args:
        threshold: Z-score threshold for anomaly detection (default 2.0).

    Returns rows where any numeric metric deviates more than threshold
    standard deviations from the channel mean.
    """
    df = load_dataframe()
    anomalies = []

    for channel in df["channel"].unique():
        ch_data = df[df["channel"] == channel]
        for col in ["spend", "revenue", "conversions", "clicks"]:
            mean = ch_data[col].mean()
            std = ch_data[col].std()
            if std == 0:
                continue
            for _, row in ch_data.iterrows():
                z = abs(row[col] - mean) / std
                if z > threshold:
                    anomalies.append({
                        "date": str(row["date"].date()),
                        "channel": channel,
                        "metric": col,
                        "value": row[col],
                        "mean": round(mean, 0),
                        "z_score": round(z, 2),
                    })

    if not anomalies:
        return "No anomalies detected."

    lines = [f"Found {len(anomalies)} anomalies (z-score > {threshold}):\n"]
    for a in anomalies:
        lines.append(
            f"  {a['date']} | {a['channel']} | {a['metric']}: "
            f"{a['value']:,.0f} (mean: {a['mean']:,.0f}, z={a['z_score']})"
        )
    return "\n".join(lines)
