"""Report Agent — combines agent outputs into a formatted markdown response."""

from src.state import AgentOutput


def format_report(query: str, agent_outputs: dict[str, AgentOutput]) -> str:
    """Combine all agent outputs into a single markdown report.

    Sections:
    - Analytics (if present): metrics, tables, chart references
    - Research (if present): insights, sources
    - Sources list at the bottom
    """
    parts = [f"# Отчёт: {query}\n"]

    # Analytics section
    if "analytics" in agent_outputs:
        analytics = agent_outputs["analytics"]
        error = analytics.get("error")
        parts.append("## Аналитика данных\n")
        if error:
            parts.append(f"**Ошибка:** {error}")
        else:
            parts.append(analytics.get("summary", "Нет данных."))

            charts = analytics.get("charts", [])
            if charts:
                parts.append(f"\n*Сгенерировано графиков: {len(charts)}*")

    # Research section
    if "research" in agent_outputs:
        research = agent_outputs["research"]
        error = research.get("error")
        parts.append("\n## Исследование рынка\n")
        if error:
            parts.append(f"**Ошибка:** {error}")
        else:
            parts.append(research.get("summary", "Нет данных."))

    # Sources
    all_sources = []
    for output in agent_outputs.values():
        for s in output.get("sources", []):
            if s.get("url") and s not in all_sources:
                all_sources.append(s)

    if all_sources:
        parts.append("\n---\n## Источники\n")
        for i, s in enumerate(all_sources, 1):
            title = s.get("title", s["url"])
            parts.append(f"{i}. [{title}]({s['url']})")

    return "\n".join(parts)
