"""Step: Fetch GitHub notifications and activity."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import ContentItem

logger = logging.getLogger(__name__)


@step
def fetch_github() -> Annotated[list[ContentItem], "github_items"]:
    """Fetch recent GitHub notifications via API."""
    from datetime import datetime, timezone

    import httpx
    from zenml.client import Client

    items: list[ContentItem] = []
    try:
        secret = Client().get_secret("github_token")
        token = secret.secret_values["token"]
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

        resp = httpx.get(
            "https://api.github.com/notifications",
            headers=headers,
            params={"all": "false", "participating": "true"},
            timeout=30,
        )
        resp.raise_for_status()

        for notif in resp.json()[:20]:
            items.append(
                ContentItem(
                    source="github",
                    title=notif.get("subject", {}).get("title", ""),
                    body=notif.get("reason", ""),
                    url=notif.get("subject", {}).get("url", ""),
                    timestamp=datetime.now(tz=timezone.utc),
                    priority="high" if notif.get("reason") == "review_requested" else "normal",
                )
            )
    except Exception as e:
        logger.warning("GitHub fetch failed: %s", e)

    logger.info("Fetched %d GitHub items", len(items))
    return items
