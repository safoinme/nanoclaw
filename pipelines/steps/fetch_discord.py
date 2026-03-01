"""Step: Fetch recent Discord messages."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import ContentItem

logger = logging.getLogger(__name__)


@step
def fetch_discord() -> Annotated[list[ContentItem], "discord_items"]:
    """Fetch recent Discord messages from monitored channels."""
    from datetime import datetime, timezone

    import httpx
    from zenml.client import Client

    items: list[ContentItem] = []
    try:
        secret = Client().get_secret("discord_credentials")
        token = secret.secret_values["bot_token"]
        channels = secret.secret_values.get("channels", "").split(",")

        for channel_id in channels:
            if not channel_id.strip():
                continue
            resp = httpx.get(
                f"https://discord.com/api/v10/channels/{channel_id.strip()}/messages",
                headers={"Authorization": f"Bot {token}"},
                params={"limit": "5"},
                timeout=30,
            )
            resp.raise_for_status()
            for msg in resp.json():
                items.append(
                    ContentItem(
                        source="discord",
                        title=msg.get("content", "")[:100],
                        body=msg.get("content", ""),
                        timestamp=datetime.now(tz=timezone.utc),
                    )
                )
    except Exception as e:
        logger.warning("Discord fetch failed: %s", e)

    logger.info("Fetched %d Discord items", len(items))
    return items
