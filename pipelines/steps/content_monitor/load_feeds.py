"""Step: Load and fetch RSS feed items."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Annotated

import feedparser
from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import FeedItem

logger = logging.getLogger(__name__)

DEFAULT_FEEDS = [
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
    {"name": "ArXiv CS.AI", "url": "http://arxiv.org/rss/cs.AI"},
    {"name": "LangChain Blog", "url": "https://blog.langchain.dev/rss/"},
    {"name": "Pydantic Blog", "url": "https://blog.pydantic.dev/feed"},
    {"name": "LangGraph Blog", "url": "https://blog.langchain.dev/tag/langgraph/rss/"},
    {"name": "Anthropic Research", "url": "https://www.anthropic.com/feed"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Simon Willison", "url": "https://simonwillison.net/atom/everything/"},
    {"name": "The Batch", "url": "https://www.deeplearning.ai/the-batch/feed/"},
    {"name": "Ahead of AI", "url": "https://magazine.sebastianraschka.com/feed"},
    {"name": "ZenML Blog", "url": "https://www.zenml.io/blog/rss.xml"},
]


@step
def load_feeds(
    feeds_config: str = "",
) -> Annotated[list[FeedItem], "feed_items"]:
    """Fetch items from configured RSS feeds."""
    feeds = json.loads(feeds_config) if feeds_config else DEFAULT_FEEDS
    items: list[FeedItem] = []

    def _fetch_one(conf: dict) -> list[FeedItem]:
        parsed = feedparser.parse(conf["url"])
        return [
            FeedItem(
                feed_name=conf["name"],
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                published=entry.get("published", ""),
                summary=entry.get("summary", "")[:500],
            )
            for entry in parsed.entries[:10]
        ]

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_fetch_one, f): f for f in feeds}
        for future in as_completed(futures):
            feed_conf = futures[future]
            try:
                items.extend(future.result())
            except Exception as e:
                logger.warning("Feed %s failed: %s", feed_conf.get("name", "?"), e)

    logger.info("Fetched %d items from %d feeds", len(items), len(feeds))
    log_metadata({"items_fetched": len(items), "feeds_count": len(feeds)})
    return items
