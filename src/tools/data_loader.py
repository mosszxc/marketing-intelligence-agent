"""Tool for loading and validating marketing campaign CSV data.

Supports two dataset formats:
- demo_campaigns.csv: channel-level (date, channel, impressions, clicks, conversions, spend, revenue)
- rsya_campaigns.csv: campaign-level (date, campaign_id, campaign_name, ad_format, device, + metrics)

Auto-detects format by column presence. All tools accept optional `path` parameter.
"""

from pathlib import Path

import pandas as pd
from langchain_core.tools import tool

REQUIRED_BASE = {"date", "impressions", "clicks", "conversions", "spend", "revenue"}
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_CSV = DATA_DIR / "rsya_campaigns.csv"


def load_dataframe(path: str | None = None) -> pd.DataFrame:
    """Load CSV into DataFrame and validate columns."""
    csv_path = Path(path) if path else DEFAULT_CSV

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["date"])
    missing = REQUIRED_BASE - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    return df


def _detect_group_column(df: pd.DataFrame) -> str:
    """Auto-detect the primary grouping column."""
    if "campaign_id" in df.columns:
        return "campaign_id"
    return "channel"


def _valid_group_columns(df: pd.DataFrame) -> list[str]:
    """Return valid grouping columns for this dataset."""
    candidates = ["channel", "campaign_id", "ad_format", "device"]
    return [c for c in candidates if c in df.columns]


@tool
def load_campaign_data(path: str = "") -> str:
    """Load marketing campaign data from a CSV file.

    Returns a summary of the dataset: shape, columns, date range, groups, totals.
    If path is empty, loads the default dataset.
    """
    df = load_dataframe(path or None)
    group_col = _detect_group_column(df)

    lines = [
        f"Loaded {len(df)} rows, {len(df.columns)} columns.",
        f"Columns: {', '.join(df.columns)}",
        f"Date range: {df['date'].min().date()} to {df['date'].max().date()}",
    ]

    if "campaign_id" in df.columns:
        campaigns = df.groupby("campaign_id")["campaign_name"].first()
        lines.append(f"Campaigns ({len(campaigns)}):")
        for cid, name in campaigns.items():
            lines.append(f"  - {cid}: {name}")
        if "ad_format" in df.columns:
            lines.append(f"Ad formats: {', '.join(sorted(df['ad_format'].unique()))}")
        if "device" in df.columns:
            lines.append(f"Devices: {', '.join(sorted(df['device'].unique()))}")
    else:
        lines.append(f"Channels: {', '.join(sorted(df[group_col].unique()))}")

    lines.append(f"Total spend: {df['spend'].sum():,.0f} RUB")
    lines.append(f"Total revenue: {df['revenue'].sum():,.0f} RUB")
    lines.append(f"Total conversions: {df['conversions'].sum():,}")

    if df["spend"].sum() > 0:
        roas = df["revenue"].sum() / df["spend"].sum()
        lines.append(f"Overall ROAS: {roas:.2f}")

    return "\n".join(lines)


@tool
def compute_metrics(metric: str, group_by: str = "", path: str = "") -> str:
    """Compute marketing metrics from campaign data.

    Args:
        metric: One of 'roi', 'roas', 'cpa', 'ctr', 'conversion_rate', 'summary'.
        group_by: Group results by column name (campaign_id, channel, ad_format, device, date).
                  Empty = auto-detect primary group.
        path: Optional CSV path. Empty = default dataset.

    Returns a formatted table with the computed metric.
    """
    df = load_dataframe(path or None)

    if not group_by:
        group_by = _detect_group_column(df)

    if group_by not in df.columns and group_by != "date":
        valid = _valid_group_columns(df)
        return f"Column '{group_by}' not found. Available: {', '.join(valid)}, date"

    if group_by == "date":
        grouped = df.groupby(pd.Grouper(key="date", freq="ME"))
    else:
        grouped = df.groupby(group_by)

    agg = grouped.agg({
        "impressions": "sum",
        "clicks": "sum",
        "conversions": "sum",
        "spend": "sum",
        "revenue": "sum",
    })

    if metric == "roi":
        agg["ROI"] = ((agg["revenue"] - agg["spend"]) / agg["spend"].replace(0, 1) * 100).round(1)
        result = agg[["spend", "revenue", "ROI"]].to_string()
    elif metric == "roas":
        agg["ROAS"] = (agg["revenue"] / agg["spend"].replace(0, 1)).round(2)
        result = agg[["spend", "revenue", "ROAS"]].to_string()
    elif metric == "cpa":
        agg["CPA"] = (agg["spend"] / agg["conversions"].replace(0, 1)).round(0)
        result = agg[["conversions", "spend", "CPA"]].to_string()
    elif metric == "ctr":
        agg["CTR%"] = (agg["clicks"] / agg["impressions"].replace(0, 1) * 100).round(2)
        result = agg[["impressions", "clicks", "CTR%"]].to_string()
    elif metric == "conversion_rate":
        agg["CR%"] = (agg["conversions"] / agg["clicks"].replace(0, 1) * 100).round(2)
        result = agg[["clicks", "conversions", "CR%"]].to_string()
    elif metric == "summary":
        agg["ROI"] = ((agg["revenue"] - agg["spend"]) / agg["spend"].replace(0, 1) * 100).round(1)
        agg["ROAS"] = (agg["revenue"] / agg["spend"].replace(0, 1)).round(2)
        agg["CPA"] = (agg["spend"] / agg["conversions"].replace(0, 1)).round(0)
        agg["CTR%"] = (agg["clicks"] / agg["impressions"].replace(0, 1) * 100).round(2)
        result = agg[["spend", "revenue", "ROAS", "CPA", "CTR%"]].to_string()
    elif metric == "ltv":
        agg["LTV"] = (agg["revenue"] / agg["conversions"].replace(0, 1)).round(0)
        result = agg[["conversions", "revenue", "LTV"]].to_string()
    elif metric == "cohort":
        # Group by month as cohort
        df_copy = df.copy()
        df_copy["month"] = df_copy["date"].dt.to_period("M")
        cohort = df_copy.groupby("month").agg({
            "spend": "sum", "revenue": "sum", "conversions": "sum",
        })
        cohort["ROAS"] = (cohort["revenue"] / cohort["spend"].replace(0, 1)).round(2)
        cohort["CPA"] = (cohort["spend"] / cohort["conversions"].replace(0, 1)).round(0)
        result = cohort.to_string()
    else:
        return f"Unknown metric: {metric}. Use: roi, roas, cpa, ctr, conversion_rate, summary, ltv, cohort."

    return f"Metric: {metric} | Grouped by: {group_by}\n\n{result}"


@tool
def detect_anomalies(threshold: float = 2.0, path: str = "") -> str:
    """Detect anomalies in campaign data using z-score method.

    Args:
        threshold: Z-score threshold for anomaly detection (default 2.0).
        path: Optional CSV path. Empty = default dataset.

    Returns rows where any numeric metric deviates more than threshold
    standard deviations from the group mean.
    """
    df = load_dataframe(path or None)
    group_col = _detect_group_column(df)

    # For RSY data, group by campaign_id + ad_format + device for finer detection
    if "campaign_id" in df.columns and "ad_format" in df.columns:
        group_keys = ["campaign_id", "ad_format", "device"]
    else:
        group_keys = [group_col]

    anomalies = []
    metrics_to_check = ["spend", "revenue", "conversions", "clicks"]

    for keys, group_data in df.groupby(group_keys):
        if not isinstance(keys, tuple):
            keys = (keys,)
        label = " / ".join(str(k) for k in keys)

        for col in metrics_to_check:
            if col not in group_data.columns:
                continue
            mean = group_data[col].mean()
            std = group_data[col].std()
            if std == 0 or pd.isna(std):
                continue
            for _, row in group_data.iterrows():
                z = abs(row[col] - mean) / std
                if z > threshold:
                    anomalies.append({
                        "date": str(row["date"].date()),
                        "group": label,
                        "metric": col,
                        "value": row[col],
                        "mean": round(mean, 0),
                        "z_score": round(z, 2),
                    })

    if not anomalies:
        return "No anomalies detected."

    # Sort by z-score descending, top 20
    anomalies.sort(key=lambda a: a["z_score"], reverse=True)
    shown = anomalies[:20]

    lines = [f"Found {len(anomalies)} anomalies (z-score > {threshold}), showing top {len(shown)}:\n"]
    for a in shown:
        lines.append(
            f"  {a['date']} | {a['group']} | {a['metric']}: "
            f"{a['value']:,.0f} (mean: {a['mean']:,.0f}, z={a['z_score']})"
        )

    return "\n".join(lines)
