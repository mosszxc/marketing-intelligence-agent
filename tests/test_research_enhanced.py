"""Tests for Phase 16: Research Agent enhancements — FireCrawl, RSS, Sentiment."""



# ── FireCrawl ─────────────────────────────────────────────────────────────

class TestFireCrawlScraper:
    def test_firecrawl_returns_content(self):
        """FireCrawl scraper returns structured content (mock mode)."""
        from src.tools.firecrawl_scraper import firecrawl_scrape
        result = firecrawl_scrape("https://example.com")
        assert isinstance(result, str)
        assert len(result) > 20

    def test_firecrawl_fallback_to_bs4(self):
        """Without FIRECRAWL_API_KEY, falls back to BeautifulSoup."""
        import os
        os.environ.pop("FIRECRAWL_API_KEY", None)
        from src.tools.firecrawl_scraper import firecrawl_scrape
        result = firecrawl_scrape("https://example.com")
        assert isinstance(result, str)
        assert len(result) > 0


# ── RSS ───────────────────────────────────────────────────────────────────

class TestRSSFeed:
    def test_fetch_rss_returns_items(self):
        """RSS parser returns structured items from mock feed."""
        from src.tools.rss import fetch_rss
        result = fetch_rss("mock://marketing-news")
        assert isinstance(result, str)
        assert "http" in result or "title" in result.lower() or len(result) > 20

    def test_fetch_marketing_news(self):
        """Preset marketing news returns aggregated content."""
        from src.tools.rss import fetch_marketing_news
        result = fetch_marketing_news()
        assert isinstance(result, str)
        assert len(result) > 50


# ── Sentiment ─────────────────────────────────────────────────────────────

class TestSentiment:
    def test_analyze_positive(self):
        from src.tools.sentiment import analyze_sentiment
        results = analyze_sentiment(["Great results, amazing ROI!"])
        assert len(results) == 1
        assert results[0]["sentiment"] == "positive"

    def test_analyze_negative(self):
        from src.tools.sentiment import analyze_sentiment
        results = analyze_sentiment(["Terrible campaign, wasted all budget"])
        assert len(results) == 1
        assert results[0]["sentiment"] == "negative"

    def test_analyze_neutral(self):
        from src.tools.sentiment import analyze_sentiment
        results = analyze_sentiment(["The campaign ran for 30 days"])
        assert len(results) == 1
        assert results[0]["sentiment"] == "neutral"

    def test_analyze_has_score(self):
        from src.tools.sentiment import analyze_sentiment
        results = analyze_sentiment(["Good performance overall"])
        assert "score" in results[0]
        assert -1.0 <= results[0]["score"] <= 1.0

    def test_monitor_brand(self):
        from src.tools.sentiment import monitor_brand
        result = monitor_brand("TestBrand")
        assert isinstance(result, str)
        assert any(w in result.lower() for w in ["positive", "negative", "neutral", "позитив", "негатив", "нейтрал"])


# ── Integration ───────────────────────────────────────────────────────────

class TestResearchEnhancedIntegration:
    def test_research_no_llm_still_works(self):
        """Enhanced research agent doesn't break existing no_llm path."""
        from src.agents.research import run_research_no_llm
        result = run_research_no_llm("AI marketing trends")
        assert "summary" in result
        assert len(result["summary"]) > 0
