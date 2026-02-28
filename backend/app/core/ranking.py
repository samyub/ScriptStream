import re
from datetime import datetime, timezone
from app.sources.base import ContentItem


def rank_items(items: list[ContentItem], keywords: list[str], num_results: int = 10) -> list[ContentItem]:
    """Rank content items by composite score: engagement + recency + keyword relevance."""
    if not items:
        return []

    scored = []
    for item in items:
        score = _compute_score(item, keywords)
        item.relevance_score = round(score, 4)
        scored.append(item)

    scored.sort(key=lambda x: x.relevance_score, reverse=True)
    return scored[:num_results]


def _compute_score(item: ContentItem, keywords: list[str]) -> float:
    engagement_score = _engagement_score(item)
    recency_score = _recency_score(item)
    keyword_score = _keyword_relevance(item, keywords)

    # Weighted composite: 40% engagement, 25% recency, 35% keyword relevance
    return (0.40 * engagement_score) + (0.25 * recency_score) + (0.35 * keyword_score)


def _engagement_score(item: ContentItem) -> float:
    """Normalize engagement to a 0-1 scale."""
    eng = item.engagement
    if item.source == "youtube":
        views = eng.get("views", 0)
        if views >= 1_000_000:
            return 1.0
        elif views >= 100_000:
            return 0.8
        elif views >= 10_000:
            return 0.6
        elif views >= 1_000:
            return 0.4
        elif views >= 100:
            return 0.2
        return 0.1

    elif item.source == "reddit":
        score_val = eng.get("score", 0)
        comments = eng.get("comments", 0)
        combined = score_val + (comments * 2)
        if combined >= 5000:
            return 1.0
        elif combined >= 1000:
            return 0.8
        elif combined >= 500:
            return 0.6
        elif combined >= 100:
            return 0.4
        elif combined >= 10:
            return 0.2
        return 0.1

    return 0.3  # generic


def _recency_score(item: ContentItem) -> float:
    """Score based on how recently the content was published."""
    if not item.published_at:
        return 0.3

    # Try to parse relative time strings like "2 days ago"
    published = item.published_at.lower()
    if "hour" in published or "minute" in published:
        return 1.0
    elif "day" in published:
        match = re.search(r'(\d+)', published)
        days = int(match.group(1)) if match else 1
        if days <= 1:
            return 1.0
        elif days <= 3:
            return 0.8
        elif days <= 7:
            return 0.6
        return 0.4
    elif "week" in published:
        return 0.4
    elif "month" in published:
        return 0.2
    elif "year" in published:
        return 0.05

    # Try ISO date parsing
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - dt).days
        if age_days <= 1:
            return 1.0
        elif age_days <= 7:
            return 0.7
        elif age_days <= 30:
            return 0.4
        return 0.1
    except (ValueError, TypeError):
        return 0.3


def _keyword_relevance(item: ContentItem, keywords: list[str]) -> float:
    """Score based on keyword matches in title and text."""
    if not keywords:
        return 0.5

    text = f"{item.title} {item.extracted_text}".lower()
    matches = sum(1 for kw in keywords if kw.lower() in text)
    ratio = matches / len(keywords)
    return min(ratio * 1.2, 1.0)
