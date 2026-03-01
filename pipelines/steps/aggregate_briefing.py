"""Step: Aggregate all source items into a single collection."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import ContentItem

logger = logging.getLogger(__name__)


@step
def aggregate_briefing(
    github_items: list[ContentItem],
    gmail_items: list[ContentItem],
    calendar_items: list[ContentItem],
    slack_items: list[ContentItem],
    discord_items: list[ContentItem],
    zenml_items: list[ContentItem],
) -> Annotated[dict[str, list[ContentItem]], "all_items"]:
    """Fan-in: aggregate items from all sources into a single dict."""
    all_items: dict[str, list[ContentItem]] = {
        "github": github_items,
        "gmail": gmail_items,
        "calendar": calendar_items,
        "slack": slack_items,
        "discord": discord_items,
        "zenml": zenml_items,
    }
    total = sum(len(v) for v in all_items.values())
    logger.info("Aggregated %d total items from %d sources", total, len(all_items))
    return all_items
