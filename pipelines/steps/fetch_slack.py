"""Step: Fetch recent Slack messages."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import ContentItem

logger = logging.getLogger(__name__)


@step
def fetch_slack() -> Annotated[list[ContentItem], "slack_items"]:
    """Fetch recent Slack messages from important channels."""
    from datetime import datetime, timezone

    import httpx
    from zenml.client import Client

    items: list[ContentItem] = []
    try:
        secret = Client().get_secret("slack_credentials")
        token = secret.secret_values["bot_token"]
        channels = secret.secret_values.get("channels", "").split(",")

        for channel_id in channels:
            if not channel_id.strip():
                continue
            resp = httpx.get(
                "https://slack.com/api/conversations.history",
                headers={"Authorization": f"Bearer {token}"},
                params={"channel": channel_id.strip(), "limit": "5"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for msg in data.get("messages", []):
                items.append(
                    ContentItem(
                        source="slack",
                        title=msg.get("text", "")[:100],
                        body=msg.get("text", ""),
                        timestamp=datetime.now(tz=timezone.utc),
                    )
                )
    except Exception as e:
        logger.warning("Slack fetch failed: %s", e)

    logger.info("Fetched %d Slack items", len(items))
    return items
