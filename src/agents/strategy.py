"""Strategy Agent — budget reallocation, what-if projections, action items.

Rule-based engine: no LLM required. Uses metrics from data_loader + interpreter.
"""

import re

import pandas as pd

from src.state import AgentOutput
from src.tools.data_loader import load_dataframe, _detect_group_column


def budget_reallocation(df: pd.DataFrame) -> str:
    """Generate budget reallocation recommendations.

    Returns a table: campaign → current % → recommended % → reason.
    Logic: shift budget from low-ROAS to high-ROAS campaigns.
    """
    group_col = _detect_group_column(df)
    agg = df.groupby(group_col).agg({"spend": "sum", "revenue": "sum"}).copy()
    agg["ROAS"] = (agg["revenue"] / agg["spend"].replace(0, 1)).round(2)

    total_spend = agg["spend"].sum()
    agg["текущий %"] = (agg["spend"] / max(total_spend, 1) * 100).round(1)

    # Reallocation rules
    recommended = []
    for name, row in agg.iterrows():
        cur = row["текущий %"]
        roas = row["ROAS"]
        if roas == 0:
            rec = 0.0
            reason = "ROAS 0 — отключить, бюджет сливается"
        elif roas < 0.5:
            rec = max(0, cur * 0.3)
            reason = f"ROAS {roas} — сократить на 70%"
        elif roas < 1.0:
            rec = cur * 0.7
            reason = f"ROAS {roas} — сократить на 30%, оптимизировать"
        elif roas < 3.0:
            rec = cur
            reason = f"ROAS {roas} — сохранить текущий уровень"
        else:
            rec = cur * 1.5
            reason = f"ROAS {roas} — увеличить на 50%, масштабировать"
        recommended.append({"name": name, "рекомендуемый %": round(rec, 1), "reason": reason})

    # Normalize recommended to 100%
    total_rec = sum(r["рекомендуемый %"] for r in recommended)
    if total_rec > 0:
        for r in recommended:
            r["рекомендуемый %"] = round(r["рекомендуемый %"] / total_rec * 100, 1)

    lines = ["## Перераспределение бюджета\n"]
    lines.append("| Кампания | Текущий % | Рекомендуемый % | Причина |")
    lines.append("|----------|-----------|-----------------|---------|")
    for r, (name, row) in zip(recommended, agg.iterrows()):
        lines.append(
            f"| {name} | {row['текущий %']}% | {r['рекомендуемый %']}% | {r['reason']} |"
        )

    # Summary
    freed = sum(
        agg.loc[r["name"], "spend"] * (1 - r["рекомендуемый %"] / max(agg.loc[r["name"], "текущий %"], 0.1))
        for r in recommended if r["рекомендуемый %"] < agg.loc[r["name"], "текущий %"]
    )
    if freed > 0:
        lines.append(f"\n**Высвобождаемый бюджет:** ~{freed:,.0f} RUB для перераспределения на эффективные кампании.")

    return "\n".join(lines)


def what_if(df: pd.DataFrame, scenario: str) -> str:
    """Model a what-if scenario.

    Parses: "увеличить бюджет <campaign> +N%"
    Returns projected metrics based on linear extrapolation.
    """
    group_col = _detect_group_column(df)
    agg = df.groupby(group_col).agg({
        "spend": "sum", "revenue": "sum", "conversions": "sum",
        "clicks": "sum", "impressions": "sum",
    })
    agg["ROAS"] = (agg["revenue"] / agg["spend"].replace(0, 1)).round(2)
    agg["CPA"] = (agg["spend"] / agg["conversions"].replace(0, 1)).round(0)

    # Parse scenario
    scenario_lower = scenario.lower()
    target_campaign = None
    pct_change = 20  # default

    for name in agg.index:
        if str(name).lower() in scenario_lower:
            target_campaign = name
            break

    # Extract percentage
    pct_match = re.search(r'[+\-]?\s*(\d+)\s*%', scenario)
    if pct_match:
        pct_change = int(pct_match.group(1))
    if "-" in scenario or "сократ" in scenario_lower or "уменьш" in scenario_lower:
        pct_change = -pct_change

    if target_campaign is None:
        return "Кампания не найдена. Укажите название кампании из данных."

    row = agg.loc[target_campaign]
    multiplier = 1 + pct_change / 100

    new_spend = row["spend"] * multiplier
    new_revenue = row["revenue"] * multiplier  # linear projection
    new_conversions = row["conversions"] * multiplier
    new_roas = row["ROAS"]  # ROAS stays same in linear model

    lines = [f"## What-if: {target_campaign} бюджет {'+' if pct_change > 0 else ''}{pct_change}%\n"]
    lines.append("| Метрика | Текущее | Прогноз | Изменение |")
    lines.append("|---------|---------|---------|-----------|")
    lines.append(f"| Расход | {row['spend']:,.0f} RUB | {new_spend:,.0f} RUB | {'+' if pct_change > 0 else ''}{pct_change}% |")
    lines.append(f"| Выручка | {row['revenue']:,.0f} RUB | {new_revenue:,.0f} RUB | {'+' if pct_change > 0 else ''}{pct_change}% |")
    lines.append(f"| Конверсии | {row['conversions']:,.0f} | {new_conversions:,.0f} | {'+' if pct_change > 0 else ''}{pct_change}% |")
    lines.append(f"| ROAS | {new_roas} | {new_roas} | без изменений (линейная модель) |")
    lines.append("\n*Прогноз на основе линейной экстраполяции текущих данных. Реальные результаты могут отличаться.*")

    return "\n".join(lines)


def run_strategy(query: str) -> AgentOutput:
    """Run strategy agent — budget reallocation + what-if."""
    df = load_dataframe()
    query_lower = query.lower()

    parts = []

    if any(w in query_lower for w in ["что если", "what if", "увелич", "сократ", "уменьш"]):
        parts.append(what_if(df, query))
    else:
        parts.append(budget_reallocation(df))

    # Always add action items
    parts.append("\n## Action items\n")
    parts.append("1. Пересмотреть бюджет кампаний с ROAS < 1")
    parts.append("2. Масштабировать кампании с ROAS > 3")
    parts.append("3. Запустить A/B тесты для кампаний в зоне оптимизации (ROAS 0.5-1.0)")

    return AgentOutput(
        summary="\n".join(parts),
        data={},
        charts=[],
        sources=[],
        error=None,
    )
