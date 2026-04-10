"""Research Agent — searches the web for marketing intelligence."""

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.state import AgentOutput
from src.tools.scraper import scrape_page
from src.tools.search import web_search

TOOLS = [web_search, scrape_page]

SYSTEM_PROMPT = """You are a marketing research agent. You search the web for industry trends, competitor analysis, and market intelligence.

When asked a question:
1. Search the web for relevant information.
2. If a specific URL is mentioned, scrape it for detailed content.
3. Synthesize findings into a structured summary with key insights.
4. Always cite your sources with URLs.

Focus on actionable insights, not generic advice.
Respond in Russian."""


def run_research(query: str) -> AgentOutput:
    """Run the research agent with LLM. Requires OPENAI_API_KEY."""
    llm = ChatOpenAI(
        model=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(TOOLS)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]

    sources: list[dict] = []
    max_iterations = 6

    for _ in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tc in response.tool_calls:
            tool_fn = {t.name: t for t in TOOLS}[tc["name"]]
            result = tool_fn.invoke(tc["args"])

            # Track sources from search results
            if tc["name"] == "web_search":
                for line in result.split("\n"):
                    if line.strip().startswith("URL:"):
                        url = line.strip().replace("URL:", "").strip()
                        sources.append({"url": url})

            from langchain_core.messages import ToolMessage
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    summary = response.content if response.content else "Research complete."

    return AgentOutput(
        summary=summary,
        data={},
        charts=[],
        sources=sources,
        error=None,
    )


def run_research_no_llm(query: str) -> AgentOutput:
    """Fallback research without LLM — returns search results directly."""
    search_results = web_search.invoke({"query": query, "max_results": 4})

    # Extract sources
    sources = []
    for line in search_results.split("\n"):
        line = line.strip()
        if line.startswith("URL:"):
            url = line.replace("URL:", "").strip()
            sources.append({"url": url, "title": ""})

    # Add scraped context
    page_content = scrape_page.invoke({"url": "demo"})

    summary = f"### Результаты поиска: {query}\n\n{search_results}\n\n### Дополнительный контекст\n\n{page_content}"

    return AgentOutput(
        summary=summary,
        data={},
        charts=[],
        sources=sources,
        error=None,
    )
