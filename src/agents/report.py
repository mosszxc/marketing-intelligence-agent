"""Report Agent — combines agent outputs into a formatted markdown response.

Filters debug output, preserves interpreted analytics and recommendations.
"""

import re

from src.state import AgentOutput

# Patterns that indicate debug/internal output — must not reach the user
_DEBUG_PATTERNS = [
    re.compile(r"^Loaded \d+ rows.*$", re.MULTILINE),
    re.compile(r"^Columns:.*$", re.MULTILINE),
    re.compile(r"^Date range:.*$", re.MULTILINE),
    re.compile(r"^Campaigns \(\d+\):.*$", re.MULTILINE),
    re.compile(r"^  - \w+:.*(?:Охват|Гео|Интерес|Look-alike|Промо|Ретаргетинг|Тематик).*$", re.MULTILINE),
    re.compile(r"^Ad formats:.*$", re.MULTILINE),
    re.compile(r"^Devices:.*$", re.MULTILINE),
    re.compile(r"^Total spend:.*$", re.MULTILINE),
    re.compile(r"^Total revenue:.*$", re.MULTILINE),
    re.compile(r"^Total conversions:.*$", re.MULTILINE),
    re.compile(r"^Overall ROAS:.*$", re.MULTILINE),
    re.compile(r"^Metric: \w+ \| Grouped by:.*$", re.MULTILINE),
]


def _strip_debug(text: str) -> str:
    """Remove debug/internal lines from text."""
    for pattern in _DEBUG_PATTERNS:
        text = pattern.sub("", text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_report(query: str, agent_outputs: dict[str, AgentOutput]) -> str:
    """Combine all agent outputs into a single markdown report.

    Sections:
    - Analytics (if present): interpreted metrics, recommendations
    - Research (if present): insights, sources
    - Sources list at the bottom
    """
    parts = [f"# Отчёт: {query}\n"]

    # Analytics section
    if "analytics" in agent_outputs:
        analytics = agent_outputs["analytics"]
        error = analytics.get("error")
        parts.append("## Аналитика\n")
        if error:
            parts.append(f"**Ошибка:** {error}")
        else:
            summary = analytics.get("summary", "Нет данных.")
            summary = _strip_debug(summary)
            if summary:
                parts.append(summary)

            charts = analytics.get("charts", [])
            if charts:
                parts.append(f"\n*Графиков: {len(charts)}*")

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
