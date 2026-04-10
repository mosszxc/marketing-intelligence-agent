"""RSS feed parser — marketing news aggregation.

Uses feedparser when available, falls back to mock data for demos/tests.
"""

MARKETING_FEEDS = [
    "https://feeds.feedburner.com/SearchEngineLand",
    "https://blog.hubspot.com/marketing/rss.xml",
    "https://contentmarketinginstitute.com/feed/",
]

# Mock data for demos without network
_MOCK_ITEMS = [
    {"title": "AI-Powered Ad Optimization Reaches 40% of Digital Budgets", "link": "https://example.com/ai-ad-optimization", "summary": "Brands are shifting to AI-driven bidding and creative generation. Google and Meta report 40% of ad spend now uses AI optimization."},
    {"title": "Marketing Attribution Models Evolve with Privacy Changes", "link": "https://example.com/attribution-privacy", "summary": "With cookie deprecation, first-party data and media mix modeling are replacing last-click attribution across the industry."},
    {"title": "Short-Form Video Dominates 2026 Content Strategy", "link": "https://example.com/short-form-video", "summary": "TikTok, Reels, and Shorts account for 60% of content marketing engagement. Average watch time increased 35% YoY."},
    {"title": "Email Marketing ROI Remains Highest Among Digital Channels", "link": "https://example.com/email-roi-2026", "summary": "Email delivers $42 per $1 spent. Personalization and AI-generated subject lines boost open rates by 22%."},
    {"title": "B2B Marketing Shifts to Account-Based AI Agents", "link": "https://example.com/b2b-ai-agents", "summary": "AI agents now handle prospect research, content personalization, and outreach sequencing for enterprise sales teams."},
]


def fetch_rss(url: str, max_items: int = 10) -> str:
    """Fetch and parse an RSS/Atom feed.

    Args:
        url: RSS feed URL (or "mock://" for demo data).
        max_items: Maximum items to return.

    Returns formatted string with title + summary + link per item.
    """
    if url.startswith("mock://"):
        return _format_items(_MOCK_ITEMS[:max_items])

    try:
        import feedparser
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", "No title"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:200],
            })
        if items:
            return _format_items(items)
        return "No items found in feed."
    except ImportError:
        return _format_items(_MOCK_ITEMS[:max_items])
    except Exception as e:
        return f"RSS error: {e}"


def fetch_marketing_news(max_items: int = 5) -> str:
    """Fetch aggregated marketing news from preset feeds.

    Returns combined digest from multiple marketing RSS sources.
    Uses mock data when feedparser is unavailable or feeds are unreachable.
    """
    all_items = []

    for feed_url in MARKETING_FEEDS:
        result = fetch_rss(feed_url, max_items=3)
        if not result.startswith("RSS error"):
            all_items.append(result)

    if all_items:
        return "### Marketing News Digest\n\n" + "\n---\n".join(all_items[:max_items])

    # Fallback to mock
    return "### Marketing News Digest\n\n" + _format_items(_MOCK_ITEMS[:max_items])


def _format_items(items: list[dict]) -> str:
    """Format RSS items into readable text."""
    lines = []
    for item in items:
        lines.append(f"**{item['title']}**")
        if item.get("summary"):
            lines.append(f"  {item['summary']}")
        if item.get("link"):
            lines.append(f"  URL: {item['link']}")
        lines.append("")
    return "\n".join(lines)
