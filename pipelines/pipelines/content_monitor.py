"""Pipeline: Content Monitor — fetch RSS feeds, summarize, archive.

Schedule: every 6 hours.

DAG:
  load_feeds --> summarize_feeds
"""

from __future__ import annotations

from zenml import pipeline
from zenml.config.schedule import Schedule

from steps.load_feeds import load_feeds
from steps.summarize_feeds import summarize_feeds

SCHEDULE = Schedule(cron_expression="0 */6 * * *")  # Every 6 hours


@pipeline(tags=["content", "rss"])
def content_monitor(feeds_config: str = "") -> None:
    """Load RSS feeds, fetch updates, summarize, archive to vault."""
    items = load_feeds(feeds_config=feeds_config)
    summarize_feeds(feed_items=items)
