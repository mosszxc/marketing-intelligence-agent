"""FireCrawl scraper — structured web scraping.

Uses FireCrawl API when FIRECRAWL_API_KEY is set.
Falls back to BeautifulSoup when no key is available.
"""

import os

from src.tools.scraper import scrape_page


def firecrawl_scrape(url: str) -> str:
    """Scrape a URL using FireCrawl (structured) or BeautifulSoup (fallback).

    Args:
        url: URL to scrape.

    Returns structured markdown content.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")

    if api_key:
        return _firecrawl_api(url, api_key)

    # Fallback to BeautifulSoup
    return scrape_page.invoke({"url": url})


def _firecrawl_api(url: str, api_key: str) -> str:
    """Call FireCrawl API for structured scraping."""
    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=api_key)
        result = app.scrape_url(url, params={"formats": ["markdown"]})
        return result.get("markdown", result.get("content", "No content extracted."))
    except ImportError:
        # firecrawl-py not installed — fall back
        return scrape_page.invoke({"url": url})
    except Exception as e:
        return f"FireCrawl error: {e}. Falling back to basic scraping.\n\n" + scrape_page.invoke({"url": url})
