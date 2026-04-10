"""Supervisor Agent — classifies queries and routes to the right agents."""

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = """You are a query classifier for a marketing intelligence system.

Given a user query, decide which agents should handle it. Available agents:
- analytics: questions about campaign data, metrics, ROI, CPA, CTR, spend, revenue, anomalies, trends in OUR data
- research: questions about market trends, competitors, industry news, benchmarks, external information

Respond with ONLY a JSON list of agent names. Examples:
- "Покажи ROI по каналам" → ["analytics"]
- "Что нового в AI маркетинге?" → ["research"]
- "Сравни наш ROI с рыночными бенчмарками" → ["analytics", "research"]
- "Найди аномалии и покажи что делают конкуренты" → ["analytics", "research"]

Always respond with a valid JSON list, nothing else."""

# Keywords for no-LLM classification
ANALYTICS_KEYWORDS = {
    "roi", "рои", "cpa", "ctr", "spend", "revenue", "расход", "доход", "выручка",
    "бюджет", "конверси", "клик", "показ", "канал", "аномал", "метрик",
    "график", "данные", "кампани", "эффективн", "окупаем", "стоимость",
}
RESEARCH_KEYWORDS = {
    "тренд", "рынок", "рыноч", "рынке", "рынка", "конкурент", "индустри", "новост", "бенчмарк",
    "benchmark", "отрасл", "trend", "competitor", "market", "news", "исследован",
}
STRATEGY_KEYWORDS = {
    "перераспредел", "оптимизир", "что если", "what if", "стратег", "strategy",
    "перенаправ", "куда направ", "куда перевест",
    "масштабир", "scale", "реаллок", "realloc",
}
RAG_KEYWORDS = {
    "документ", "document", "pdf", "файл", "file", "загружен",
    "в нашем плане", "наша стратег", "в документе", "в файле",
    "kpi цел", "kpi target", "написано в", "нашей стратеги",
    "наш план", "нашем плане",
}


def classify_query(query: str) -> list[str]:
    """Classify query and return list of agent names to invoke."""
    if os.getenv("OPENAI_API_KEY"):
        return _classify_with_llm(query)
    return _classify_keywords(query)


def _classify_with_llm(query: str) -> list[str]:
    """Use LLM to classify the query."""
    import json

    llm = ChatOpenAI(
        model=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        temperature=0,
    )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query),
    ])

    try:
        plan = json.loads(response.content.strip())
        if isinstance(plan, list) and all(a in ("analytics", "research") for a in plan):
            return plan
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback if LLM response is malformed
    return _classify_keywords(query)


def _classify_keywords(query: str) -> list[str]:
    """Keyword-based classification fallback."""
    query_lower = query.lower()

    has_analytics = any(kw in query_lower for kw in ANALYTICS_KEYWORDS)
    has_research = any(kw in query_lower for kw in RESEARCH_KEYWORDS)
    has_strategy = any(kw in query_lower for kw in STRATEGY_KEYWORDS)
    has_rag = any(kw in query_lower for kw in RAG_KEYWORDS)

    # RAG takes priority for document-specific queries
    if has_rag:
        return ["rag"]

    # Strategy takes priority when detected
    if has_strategy:
        agents = ["strategy"]
        if has_analytics:
            agents.insert(0, "analytics")
        return agents

    if has_analytics and has_research:
        return ["analytics", "research"]
    if has_analytics:
        return ["analytics"]
    if has_research:
        return ["research"]

    # Default: both
    return ["analytics", "research"]
