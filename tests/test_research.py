"""Tests for research tools and agent (no API keys required)."""

from src.tools.search import web_search, MOCK_RESULTS
from src.tools.scraper import scrape_page
from src.agents.research import run_research_no_llm


class TestWebSearch:
    def test_mock_search_returns_results(self):
        result = web_search.invoke({"query": "AI маркетинг тренды 2026"})
        assert "[1]" in result
        assert "URL:" in result
        assert "AI" in result

    def test_mock_search_respects_max_results(self):
        result = web_search.invoke({"query": "test", "max_results": 2})
        assert "[2]" in result
        assert "[3]" not in result

    def test_mock_results_have_required_fields(self):
        for r in MOCK_RESULTS:
            assert "title" in r
            assert "url" in r
            assert "content" in r
            assert "score" in r
            assert isinstance(r["score"], float)


class TestScraper:
    def test_demo_mode_returns_content(self):
        result = scrape_page.invoke({"url": "demo"})
        assert "AI Marketing" in result
        assert len(result) > 100

    def test_invalid_url_returns_mock(self):
        result = scrape_page.invoke({"url": "not-a-url"})
        assert len(result) > 0


class TestResearchAgentNoLLM:
    def test_returns_search_results(self):
        result = run_research_no_llm("тренды AI в маркетинге")
        assert result["summary"]
        assert "Результаты поиска" in result["summary"]
        assert "AI" in result["summary"]

    def test_returns_sources(self):
        result = run_research_no_llm("конкуренты в рекламе")
        assert isinstance(result["sources"], list)
        assert len(result["sources"]) > 0
        assert "url" in result["sources"][0]

    def test_includes_scraped_context(self):
        result = run_research_no_llm("что нового в маркетинге")
        assert "Дополнительный контекст" in result["summary"]

    def test_output_structure(self):
        result = run_research_no_llm("test")
        assert "summary" in result
        assert "data" in result
        assert "charts" in result
        assert "sources" in result
        assert "error" in result
        assert result["error"] is None
        assert result["charts"] == []
