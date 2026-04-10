"""Tavily web search tool with mock fallback."""

import os

from langchain_core.tools import tool

MOCK_RESULTS = [
    {
        "title": "AI в маркетинге 2026: ключевые тренды",
        "url": "https://example.com/ai-marketing-trends-2026",
        "content": "Рынок AI в маркетинге достиг $36B в 2026 году. Ключевые тренды: "
        "персонализация в реальном времени, AI-генерация креативов, предиктивная аналитика, "
        "мультиканальная атрибуция через LLM-агентов. Meta и Google интегрировали AI-агентов "
        "в рекламные кабинеты. Маркетологи с AI-навыками получают на 43% больше.",
        "score": 0.95,
    },
    {
        "title": "Performance Marketing Benchmarks Q1 2026",
        "url": "https://example.com/perf-marketing-benchmarks-q1-2026",
        "content": "Средний ROI по каналам: Google Ads 250-400%, Meta Ads 180-320%, "
        "TikTok Ads 120-280%, Email 3500-4200%, SEO 1500-2500%. "
        "CPA вырос на 12% YoY из-за конкуренции. Лучшая стратегия — "
        "мультиканальная атрибуция и перераспределение бюджета в реальном времени.",
        "score": 0.88,
    },
    {
        "title": "Как бренды используют AI-агентов для рекламы",
        "url": "https://example.com/brands-ai-agents-advertising",
        "content": "Omneky: AI-генерация креативов дала +200% продаж и 3.5x ROI. "
        "Klarna: AI-агент заменил 700 сотрудников саппорта. "
        "Coca-Cola: мультиагентная система для A/B тестирования креативов на 15 рынках. "
        "Тренд 2026: AI-агенты как стандартный инструмент в MarTech стеке.",
        "score": 0.82,
    },
    {
        "title": "Yandex Direct: обновления алгоритмов 2026",
        "url": "https://example.com/yandex-direct-2026-updates",
        "content": "Yandex запустил AI-оптимизатор ставок на базе YandexGPT. "
        "Автостратегии теперь учитывают LTV и вероятность повторной покупки. "
        "Новый формат: динамические объявления с генерацией текста через LLM. "
        "Средний CTR вырос на 18% у рекламодателей, использующих новые инструменты.",
        "score": 0.75,
    },
]


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for marketing intelligence and industry trends.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (default 5).

    Returns formatted search results with titles, URLs, and content snippets.
    Uses Tavily API if TAVILY_API_KEY is set, otherwise returns mock data for demo.
    """
    if os.getenv("TAVILY_API_KEY"):
        return _tavily_search(query, max_results)

    return _format_results(MOCK_RESULTS[:max_results])


def _tavily_search(query: str, max_results: int) -> str:
    """Real Tavily search."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query, max_results=max_results, search_depth="basic")

    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0),
        }
        for r in response.get("results", [])
    ]
    return _format_results(results)


def _format_results(results: list[dict]) -> str:
    """Format search results into readable text."""
    if not results:
        return "No results found."

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"[{i}] {r['title']}\n"
            f"    URL: {r['url']}\n"
            f"    {r['content'][:300]}\n"
            f"    Relevance: {r['score']}"
        )
    return "\n\n".join(parts)
