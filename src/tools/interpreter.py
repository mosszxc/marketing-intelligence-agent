"""Intelligent interpretation layer — turns raw metrics into analyst-grade insights.

No LLM required. Pure logic:
- interpret_metrics(): best/worst campaigns, budget at risk, key numbers
- classify_anomalies(): group raw anomalies by campaign, assign human-readable type
- generate_recommendations(): actionable items based on metrics and anomalies
"""

import pandas as pd

from src.tools.data_loader import _detect_group_column


# ---------------------------------------------------------------------------
# Metrics interpretation
# ---------------------------------------------------------------------------

def interpret_metrics(df: pd.DataFrame, group_by: str = "") -> str:
    """Interpret campaign metrics — prose summary, not raw table.

    Returns a human-readable analysis naming best/worst campaigns,
    budget at risk, and key performance numbers.
    """
    if not group_by:
        group_by = _detect_group_column(df)

    agg = df.groupby(group_by).agg({
        "impressions": "sum",
        "clicks": "sum",
        "conversions": "sum",
        "spend": "sum",
        "revenue": "sum",
    })

    agg["ROAS"] = (agg["revenue"] / agg["spend"].replace(0, 1)).round(2)
    agg["CPA"] = (agg["spend"] / agg["conversions"].replace(0, 1)).round(0)
    agg["CTR%"] = (agg["clicks"] / agg["impressions"].replace(0, 1) * 100).round(2)

    total_spend = agg["spend"].sum()
    total_revenue = agg["revenue"].sum()
    overall_roas = round(total_revenue / max(total_spend, 1), 2)

    # Best and worst by ROAS
    best = agg["ROAS"].idxmax()
    worst = agg["ROAS"].idxmin()
    best_roas = agg.loc[best, "ROAS"]
    worst_roas = agg.loc[worst, "ROAS"]

    # Campaigns losing money (ROAS < 1)
    losers = agg[agg["ROAS"] < 1.0].sort_values("ROAS")
    loss_spend = losers["spend"].sum()
    loss_pct = round(loss_spend / max(total_spend, 1) * 100, 1)

    # Profitable campaigns
    winners = agg[agg["ROAS"] >= 1.0].sort_values("ROAS", ascending=False)

    lines = []

    # Summary headline
    lines.append(
        f"Общий ROAS: {overall_roas} | "
        f"Бюджет: {total_spend:,.0f} RUB | "
        f"Выручка: {total_revenue:,.0f} RUB"
    )
    lines.append("")

    # Best campaign
    best_spend = agg.loc[best, "spend"]
    best_rev = agg.loc[best, "revenue"]
    lines.append(
        f"**Лучшая кампания:** {best} — ROAS {best_roas}, "
        f"потрачено {best_spend:,.0f} RUB, выручка {best_rev:,.0f} RUB"
    )

    # Worst campaign
    worst_spend = agg.loc[worst, "spend"]
    worst_rev = agg.loc[worst, "revenue"]
    lines.append(
        f"**Худшая кампания:** {worst} — ROAS {worst_roas}, "
        f"потрачено {worst_spend:,.0f} RUB, выручка {worst_rev:,.0f} RUB"
    )
    lines.append("")

    # Losers detail
    if not losers.empty:
        lines.append(
            f"**Бюджет в убыток:** {loss_spend:,.0f} RUB ({loss_pct}% от общего бюджета)"
        )
        for name, row in losers.iterrows():
            lines.append(
                f"  - {name}: ROAS {row['ROAS']}, "
                f"потрачено {row['spend']:,.0f} RUB, "
                f"выручка {row['revenue']:,.0f} RUB"
            )
        lines.append("")

    # Winners summary (top 3)
    if not winners.empty:
        lines.append("**Прибыльные кампании (топ-3):**")
        for name, row in winners.head(3).iterrows():
            lines.append(
                f"  - {name}: ROAS {row['ROAS']}, "
                f"CPA {row['CPA']:,.0f} RUB, CTR {row['CTR%']}%"
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Anomaly classification
# ---------------------------------------------------------------------------

def classify_anomalies(df: pd.DataFrame, threshold: float = 2.0) -> str:
    """Detect, group, classify, and prioritize anomalies.

    Returns ≤5 critical problems with human-readable type and impact,
    not 1365 raw z-score lines.
    """
    group_col = _detect_group_column(df)

    if "campaign_id" in df.columns and "ad_format" in df.columns:
        group_keys = ["campaign_id", "ad_format", "device"]
    else:
        group_keys = [group_col]

    raw_anomalies = []

    for keys, group_data in df.groupby(group_keys):
        if not isinstance(keys, tuple):
            keys = (keys,)

        for col in ["spend", "revenue", "conversions", "clicks"]:
            if col not in group_data.columns:
                continue
            mean = group_data[col].mean()
            std = group_data[col].std()
            if std == 0 or pd.isna(std):
                continue
            for _, row in group_data.iterrows():
                z = abs(row[col] - mean) / std
                if z > threshold:
                    raw_anomalies.append({
                        "date": row["date"],
                        "campaign": keys[0] if len(keys) > 0 else "unknown",
                        "group_label": " / ".join(str(k) for k in keys),
                        "metric": col,
                        "value": row[col],
                        "mean": mean,
                        "z_score": z,
                        "spend": row.get("spend", 0),
                        "clicks": row.get("clicks", 0),
                        "conversions": row.get("conversions", 0),
                        "impressions": row.get("impressions", 0),
                        "revenue": row.get("revenue", 0),
                    })

    if not raw_anomalies:
        return "Аномалий не обнаружено."

    # Group by campaign and classify
    campaign_issues: dict[str, dict] = {}

    for a in raw_anomalies:
        camp = a["campaign"]
        if camp not in campaign_issues:
            campaign_issues[camp] = {
                "anomalies": [],
                "total_impact": 0.0,
                "types": set(),
            }
        campaign_issues[camp]["anomalies"].append(a)

        # Impact = spend involved × z-score deviation
        campaign_issues[camp]["total_impact"] += a["spend"] * a["z_score"]

    # Classify each campaign's anomalies
    classified = []
    for camp, info in campaign_issues.items():
        anomalies = info["anomalies"]
        atype = _classify_type(anomalies, df, camp)
        impact = info["total_impact"]
        count = len(anomalies)

        # Date range of anomalies
        dates = sorted(set(a["date"] for a in anomalies))
        if len(dates) == 1:
            period = str(dates[0].date())
        else:
            period = f"{dates[0].date()} — {dates[-1].date()}"

        classified.append({
            "campaign": camp,
            "type": atype,
            "impact": impact,
            "count": count,
            "period": period,
            "details": _type_details(atype, anomalies, camp),
        })

    # Sort by impact, take top 5
    classified.sort(key=lambda x: x["impact"], reverse=True)
    top = classified[:5]

    lines = [f"**Обнаружено {len(classified)} проблемных кампаний, топ-{len(top)} по impact:**\n"]

    for i, item in enumerate(top, 1):
        lines.append(
            f"{i}. **{item['campaign']}** — {item['type']}\n"
            f"   Период: {item['period']} | "
            f"Аномальных событий: {item['count']}\n"
            f"   {item['details']}"
        )
        lines.append("")

    return "\n".join(lines)


def _classify_type(anomalies: list[dict], df: pd.DataFrame, campaign: str) -> str:
    """Classify anomaly type based on patterns."""
    has_click_spike = any(
        a["metric"] == "clicks" and a["z_score"] > 3 for a in anomalies
    )
    has_zero_conversions = any(
        a["conversions"] == 0 and a["clicks"] > 100 for a in anomalies
    )
    has_spend_spike = any(
        a["metric"] == "spend" and a["z_score"] > 3 for a in anomalies
    )
    has_revenue_spike = any(
        a["metric"] == "revenue" and a["value"] > a["mean"] * 2 for a in anomalies
    )
    has_very_low_ctr = any(
        a["impressions"] > 0 and (a["clicks"] / max(a["impressions"], 1)) < 0.001
        for a in anomalies
    )

    # Bot traffic: high clicks + zero conversions
    if has_click_spike and has_zero_conversions:
        return "Бот-трафик (spike кликов, 0 конверсий)"

    # CPC/spend spike
    if has_spend_spike and not has_revenue_spike:
        return "CPC spike (аномальный рост расходов)"

    # Promo effect: revenue and conversion spike
    if has_revenue_spike:
        return "Промо-эффект (всплеск выручки/конверсий)"

    # Junk placement: very low CTR + zero conversions
    if has_very_low_ctr and has_zero_conversions:
        return "Мусорная площадка (CTR < 0.1%, 0 конверсий)"

    # Generic
    if has_spend_spike:
        return "Spike расходов"

    return "Аномальное отклонение метрик"


def _type_details(atype: str, anomalies: list[dict], campaign: str) -> str:
    """Generate a one-line detail string for the anomaly type."""
    if "Бот" in atype or "bot" in atype.lower():
        max_clicks = max((a for a in anomalies if a["metric"] == "clicks"),
                         key=lambda a: a["value"], default=None)
        if max_clicks:
            return (
                f"Макс. клики: {max_clicks['value']:,.0f} "
                f"(среднее: {max_clicks['mean']:,.0f}), конверсии: 0"
            )

    if "CPC" in atype or "spike" in atype.lower():
        max_spend = max((a for a in anomalies if a["metric"] == "spend"),
                        key=lambda a: a["z_score"], default=None)
        if max_spend:
            return (
                f"Расход: {max_spend['value']:,.0f} RUB "
                f"(среднее: {max_spend['mean']:,.0f} RUB, x{max_spend['value']/max(max_spend['mean'],1):.1f})"
            )

    if "Промо" in atype:
        max_rev = max((a for a in anomalies if a["metric"] == "revenue"),
                      key=lambda a: a["value"], default=None)
        if max_rev:
            return (
                f"Выручка: {max_rev['value']:,.0f} RUB "
                f"(среднее: {max_rev['mean']:,.0f} RUB)"
            )

    total_spend = sum(a["spend"] for a in anomalies)
    return f"Затронутый бюджет: {total_spend:,.0f} RUB"


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def generate_recommendations(df: pd.DataFrame, anomaly_text: str = "") -> str:
    """Generate actionable recommendations based on metrics and anomalies.

    Rules-based engine:
    - ROAS < 0.5 → recommend disabling
    - ROAS 0.5-1.0 → recommend optimization
    - Bot traffic detected → check placements
    - CPC spike → check bids
    - High ROAS → recommend scaling
    """
    group_col = _detect_group_column(df)
    agg = df.groupby(group_col).agg({
        "spend": "sum",
        "revenue": "sum",
        "conversions": "sum",
        "clicks": "sum",
        "impressions": "sum",
    })
    agg["ROAS"] = (agg["revenue"] / agg["spend"].replace(0, 1)).round(2)

    recs = []

    # Rule: ROAS = 0 — disable
    zero_roas = agg[agg["ROAS"] == 0]
    for name, row in zero_roas.iterrows():
        recs.append(
            f"**Отключить {name}** — ROAS 0, потрачено {row['spend']:,.0f} RUB "
            f"при нулевой выручке. Бюджет сливается впустую."
        )

    # Rule: ROAS < 0.5 — strong recommendation to disable
    low_roas = agg[(agg["ROAS"] > 0) & (agg["ROAS"] < 0.5)]
    for name, row in low_roas.iterrows():
        loss = row["spend"] - row["revenue"]
        recs.append(
            f"**Рассмотреть отключение {name}** — ROAS {row['ROAS']}, "
            f"убыток {loss:,.0f} RUB. Оптимизация таргетинга или отключение."
        )

    # Rule: ROAS 0.5-1.0 — optimize
    mid_roas = agg[(agg["ROAS"] >= 0.5) & (agg["ROAS"] < 1.0)]
    for name, row in mid_roas.iterrows():
        recs.append(
            f"**Оптимизировать {name}** — ROAS {row['ROAS']}. "
            f"Проверить креативы, таргетинг, площадки. Потенциал выхода в плюс."
        )

    # Anomaly-based recommendations
    anomaly_lower = anomaly_text.lower()
    if "бот" in anomaly_lower or "bot" in anomaly_lower:
        recs.append(
            "**Проверить площадки на бот-трафик** — добавить минус-площадки, "
            "включить фильтр недействительных кликов."
        )
    if "spike" in anomaly_lower or "спайк" in anomaly_lower or "cpc" in anomaly_lower:
        recs.append(
            "**Проверить ставки** — CPC spike может быть вызван конкурентами "
            "или изменением аукциона. Рассмотреть ручное управление ставками."
        )

    # Rule: top ROAS — scale up
    high_roas = agg[agg["ROAS"] >= 3.0].sort_values("ROAS", ascending=False)
    if not high_roas.empty:
        top = high_roas.index[0]
        recs.append(
            f"**Масштабировать {top}** — ROAS {high_roas.loc[top, 'ROAS']}, "
            f"перераспределить бюджет с убыточных кампаний."
        )

    if not recs:
        return ""

    lines = ["## Рекомендации\n"]
    for i, rec in enumerate(recs, 1):
        lines.append(f"{i}. {rec}")

    return "\n".join(lines)
