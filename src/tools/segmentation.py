"""Campaign segmentation — K-means clustering by performance metrics.

Groups campaigns into 3-5 segments based on normalized CTR, CPA, ROAS.
Returns human-readable descriptions and scatter plot.
"""

import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.tools.data_loader import _detect_group_column


def segment_campaigns(df: pd.DataFrame, n_clusters: int = 3) -> str:
    """Segment campaigns by performance using K-means.

    Args:
        df: Campaign DataFrame.
        n_clusters: Number of segments (default 3).

    Returns human-readable description of each segment.
    """
    group_col = _detect_group_column(df)
    agg = df.groupby(group_col).agg({
        "spend": "sum", "revenue": "sum", "conversions": "sum",
        "clicks": "sum", "impressions": "sum",
    })
    agg["ROAS"] = (agg["revenue"] / agg["spend"].replace(0, 1)).round(2)
    agg["CPA"] = (agg["spend"] / agg["conversions"].replace(0, 1)).round(0)
    agg["CTR"] = (agg["clicks"] / agg["impressions"].replace(0, 1) * 100).round(2)

    # Normalize for clustering
    features = agg[["ROAS", "CPA", "CTR"]].copy()
    for col in features.columns:
        rng = features[col].max() - features[col].min()
        if rng > 0:
            features[col] = (features[col] - features[col].min()) / rng
        else:
            features[col] = 0

    # Simple K-means (no sklearn dependency — use numpy)
    labels = _kmeans(features.values, n_clusters)
    agg["segment"] = labels

    # Describe segments
    lines = [f"## Сегментация кампаний ({n_clusters} кластера)\n"]

    for seg_id in sorted(agg["segment"].unique()):
        seg = agg[agg["segment"] == seg_id]
        avg_roas = seg["ROAS"].mean()
        avg_cpa = seg["CPA"].mean()
        avg_ctr = seg["CTR"].mean()
        campaigns = ", ".join(str(n) for n in seg.index)
        label = _label_segment(avg_roas, avg_cpa, avg_ctr)

        lines.append(f"### Сегмент {seg_id + 1}: {label}")
        lines.append(f"- Кампании: {campaigns}")
        lines.append(f"- Средний ROAS: {avg_roas:.2f}")
        lines.append(f"- Средний CPA: {avg_cpa:,.0f} RUB")
        lines.append(f"- Средний CTR: {avg_ctr:.2f}%")
        lines.append("")

    return "\n".join(lines)


def segment_scatter_plot(df: pd.DataFrame, n_clusters: int = 3) -> str:
    """Generate scatter plot of campaign segments (spend vs ROAS, colored by cluster).

    Returns base64-encoded PNG.
    """
    group_col = _detect_group_column(df)
    agg = df.groupby(group_col).agg({
        "spend": "sum", "revenue": "sum", "conversions": "sum",
        "clicks": "sum", "impressions": "sum",
    })
    agg["ROAS"] = (agg["revenue"] / agg["spend"].replace(0, 1)).round(2)
    agg["CPA"] = (agg["spend"] / agg["conversions"].replace(0, 1)).round(0)
    agg["CTR"] = (agg["clicks"] / agg["impressions"].replace(0, 1) * 100).round(2)

    features = agg[["ROAS", "CPA", "CTR"]].copy()
    for col in features.columns:
        rng = features[col].max() - features[col].min()
        if rng > 0:
            features[col] = (features[col] - features[col].min()) / rng

    labels = _kmeans(features.values, n_clusters)
    colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]

    fig, ax = plt.subplots(figsize=(10, 6))
    for seg_id in range(n_clusters):
        mask = labels == seg_id
        ax.scatter(
            agg["spend"].values[mask],
            agg["ROAS"].values[mask],
            c=colors[seg_id % len(colors)],
            s=100,
            label=f"Segment {seg_id + 1}",
            alpha=0.8,
        )
        for idx in np.where(mask)[0]:
            ax.annotate(
                str(agg.index[idx]),
                (agg["spend"].values[idx], agg["ROAS"].values[idx]),
                fontsize=7, ha="center", va="bottom",
            )

    ax.set_xlabel("Spend (RUB)")
    ax.set_ylabel("ROAS")
    ax.set_title("Campaign Segments: Spend vs ROAS")
    ax.legend()
    ax.grid(True, alpha=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def _label_segment(avg_roas: float, avg_cpa: float, avg_ctr: float) -> str:
    """Generate human-readable label for a segment."""
    if avg_roas >= 5:
        return "Звёзды (высокий ROAS)"
    if avg_roas >= 2:
        return "Рабочие лошадки (стабильный ROAS)"
    if avg_roas >= 1:
        return "Зона оптимизации (на грани окупаемости)"
    return "Убыточные (ROAS < 1)"


def _kmeans(data: np.ndarray, k: int, max_iter: int = 50) -> np.ndarray:
    """Simple K-means without sklearn. Returns cluster labels."""
    n = len(data)
    if n <= k:
        return np.arange(n)

    # Initialize centroids with first k points (deterministic for tests)
    rng = np.random.RandomState(42)
    indices = rng.choice(n, k, replace=False)
    centroids = data[indices].copy()

    labels = np.zeros(n, dtype=int)

    for _ in range(max_iter):
        # Assign
        for i in range(n):
            dists = np.sum((centroids - data[i]) ** 2, axis=1)
            labels[i] = int(np.argmin(dists))

        # Update
        new_centroids = np.zeros_like(centroids)
        for j in range(k):
            members = data[labels == j]
            if len(members) > 0:
                new_centroids[j] = members.mean(axis=0)
            else:
                new_centroids[j] = centroids[j]

        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids

    return labels
