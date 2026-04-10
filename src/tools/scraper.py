"""Web scraping tool with timeout and error handling."""

import os

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

MOCK_PAGES = {
    "default": (
        "AI Marketing Trends 2026\n\n"
        "The global AI marketing market reached $36 billion in 2026, growing 28% YoY. "
        "Key developments:\n"
        "- Meta launched AI agents inside Ads Manager for automated campaign optimization\n"
        "- Google integrated Gemini into Google Ads for real-time bid adjustments\n"
        "- OpenAI hired Growth Paid Marketing Platform Engineers\n"
        "- Omneky's AI creative generation delivered +200% sales and 3.5x ROI\n"
        "- 43% salary premium for marketers with AI skills (JobsPikr 2026)\n\n"
        "The trend is clear: AI agents are becoming standard tools in MarTech."
    )
}


@tool
def scrape_page(url: str) -> str:
    """Scrape a web page and extract its main text content.

    Args:
        url: The URL to scrape.

    Returns the extracted text content from the page.
    Timeout: 10 seconds. Returns mock data if no network or in demo mode.
    """
    if os.getenv("DEMO_MODE") or not url.startswith("http"):
        return MOCK_PAGES["default"]

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "MarketingIntelligenceBot/0.1"})
        resp.raise_for_status()
    except (requests.RequestException, Exception) as e:
        return f"Error fetching {url}: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove scripts, styles, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Truncate to avoid overwhelming the LLM
    max_chars = 3000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[...truncated]"

    return text
