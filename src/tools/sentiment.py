"""Sentiment analysis — brand mention monitoring.

Uses TextBlob for sentiment classification. Lightweight — no heavy ML models.
Falls back to keyword-based analysis if TextBlob is unavailable.
"""

from src.tools.search import web_search


def analyze_sentiment(texts: list[str]) -> list[dict]:
    """Analyze sentiment of a list of texts.

    Args:
        texts: List of text strings to analyze.

    Returns list of dicts: {text, sentiment, score}.
        sentiment: "positive", "negative", or "neutral"
        score: float from -1.0 (negative) to 1.0 (positive)
    """
    results = []
    for text in texts:
        score = _get_score(text)
        if score > 0.1:
            sentiment = "positive"
        elif score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        results.append({"text": text, "sentiment": sentiment, "score": round(score, 3)})
    return results


def monitor_brand(brand_name: str) -> str:
    """Monitor brand mentions: search web → analyze sentiment.

    Args:
        brand_name: Brand name to search for.

    Returns summary: "X positive, Y negative, Z neutral mentions"
    """
    search_results = web_search.invoke({"query": f"{brand_name} reviews opinions", "max_results": 5})

    # Extract text chunks from search results
    texts = []
    for line in search_results.split("\n"):
        line = line.strip()
        if line and not line.startswith(("URL:", "Title:", "Score:", "---")):
            texts.append(line)

    if not texts:
        texts = [search_results]

    sentiments = analyze_sentiment(texts)

    pos = sum(1 for s in sentiments if s["sentiment"] == "positive")
    neg = sum(1 for s in sentiments if s["sentiment"] == "negative")
    neu = sum(1 for s in sentiments if s["sentiment"] == "neutral")
    avg_score = sum(s["score"] for s in sentiments) / max(len(sentiments), 1)

    lines = [
        f"### Brand Monitoring: {brand_name}\n",
        f"Проанализировано **{len(sentiments)}** упоминаний:\n",
        f"- Позитивных: **{pos}**",
        f"- Негативных: **{neg}**",
        f"- Нейтральных: **{neu}**",
        f"- Средний score: **{avg_score:.2f}** (-1.0 = негативный, +1.0 = позитивный)",
    ]

    if avg_score > 0.2:
        lines.append("\n**Вывод:** преимущественно позитивное восприятие бренда.")
    elif avg_score < -0.2:
        lines.append("\n**Вывод:** преимущественно негативное восприятие. Требуется внимание.")
    else:
        lines.append("\n**Вывод:** смешанное или нейтральное восприятие бренда.")

    return "\n".join(lines)


def _get_score(text: str) -> float:
    """Get sentiment score for a single text. Uses TextBlob if available."""
    try:
        from textblob import TextBlob
        return TextBlob(text).sentiment.polarity
    except ImportError:
        return _keyword_score(text)


# Keyword fallback when TextBlob is not installed
_POSITIVE = {
    "great", "amazing", "excellent", "good", "best", "fantastic", "wonderful",
    "outstanding", "impressive", "love", "perfect", "brilliant", "superb",
    "отлично", "хорошо", "прекрасно", "замечательно", "лучший", "рост",
}
_NEGATIVE = {
    "terrible", "awful", "bad", "worst", "horrible", "poor", "disappointing",
    "waste", "failed", "broken", "useless", "pathetic", "disaster",
    "ужасно", "плохо", "провал", "потеря", "убыток", "падение",
}


def _keyword_score(text: str) -> float:
    """Simple keyword-based sentiment scoring."""
    words = set(text.lower().split())
    pos = len(words & _POSITIVE)
    neg = len(words & _NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total
