"""Step: Load and fetch RSS feed items."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import FeedItem

logger = logging.getLogger(__name__)

DEFAULT_FEEDS = [
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
    {"name": "ArXiv CS.AI", "url": "http://arxiv.org/rss/cs.AI"},
]


@step
def load_feeds(
    feeds_config: str = "",
) -> Annotated[list[FeedItem], "feed_items"]:
    """Fetch items from configured RSS feeds."""
    import json

    import feedparser

    feeds = json.loads(feeds_config) if feeds_config else DEFAULT_FEEDS
    items: list[FeedItem] = []

    for feed_conf in feeds:
        try:
            parsed = feedparser.parse(feed_conf["url"])
            for entry in parsed.entries[:10]:
                items.append(
                    FeedItem(
                        feed_name=feed_conf["name"],
                        title=entry.get("title", ""),
                        url=entry.get("link", ""),
                        published=entry.get("published", ""),
                        summary=entry.get("summary", "")[:500],
                    )
                )
        except Exception as e:
            logger.warning("Feed %s failed: %s", feed_conf.get("name", "?"), e)

    logger.info("Fetched %d items from %d feeds", len(items), len(feeds))
    return items
