"""Step: Summarize feed items and archive to vault."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import FeedItem, PipelineResult

logger = logging.getLogger(__name__)


@step
def summarize_feeds(
    feed_items: list[FeedItem],
) -> Annotated[PipelineResult, "content_result"]:
    """Summarize feed items and save to vault."""
    from datetime import datetime, timezone

    from pydantic_ai import Agent

    from src.shared.config import ANTHROPIC_MODEL
    from src.shared.obsidian_io import write_note

    if not feed_items:
        return PipelineResult(
            pipeline_name="content_monitor",
            message="No new feed items to process",
        )

    # Group items by feed
    by_feed: dict[str, list[FeedItem]] = {}
    for item in feed_items:
        by_feed.setdefault(item.feed_name, []).append(item)

    agent = Agent(
        f"anthropic:{ANTHROPIC_MODEL}",
        system_prompt=(
            "Summarize these RSS feed items into a brief digest. "
            "Return a concise summary highlighting the most important items."
        ),
        result_type=str,
    )

    # Build digest
    digest_lines: list[str] = []
    for feed_name, items in by_feed.items():
        feed_text = "\n".join(f"- {i.title}: {i.summary[:200]}" for i in items)
        try:
            result = agent.run_sync(f"Feed: {feed_name}\n\n{feed_text}")
            digest_lines.append(f"## {feed_name}\n{result.data}")
        except Exception as e:
            logger.warning("Summarization failed for %s: %s", feed_name, e)
            digest_lines.append(f"## {feed_name}")
            for item in items:
                digest_lines.append(f"- [{item.title}]({item.url})")

    # Save to vault
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    hour = datetime.now(tz=timezone.utc).strftime("%H")
    note_path = f"09-Archive/Content/{today}-{hour}h-digest.md"

    write_note(
        note_path,
        "\n\n".join(digest_lines),
        metadata={
            "type": "content-digest",
            "date": today,
            "tags": ["content", "digest", "rss"],
            "feeds": list(by_feed.keys()),
        },
    )

    log_metadata({"items_processed": len(feed_items), "feeds_covered": len(by_feed)})
    return PipelineResult(
        pipeline_name="content_monitor",
        items_processed=len(feed_items),
        notes_created=[note_path],
        message=f"Content digest: {len(feed_items)} items from {len(by_feed)} feeds",
    )
