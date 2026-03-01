"""Step: Fetch recent Gmail messages."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import ContentItem

logger = logging.getLogger(__name__)


@step
def fetch_gmail() -> Annotated[list[ContentItem], "gmail_items"]:
    """Fetch recent unread Gmail messages via API."""
    from datetime import datetime, timezone

    import httpx
    from zenml.client import Client

    items: list[ContentItem] = []
    try:
        secret = Client().get_secret("gmail_credentials")
        token = secret.secret_values["access_token"]

        resp = httpx.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": "is:unread", "maxResults": "10"},
            timeout=30,
        )
        resp.raise_for_status()

        for msg_ref in resp.json().get("messages", []):
            msg_resp = httpx.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_ref['id']}",
                headers={"Authorization": f"Bearer {token}"},
                params={"format": "metadata", "metadataHeaders": ["Subject", "From"]},
                timeout=30,
            )
            msg_resp.raise_for_status()
            msg = msg_resp.json()
            headers_list = msg.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "")
            sender = next((h["value"] for h in headers_list if h["name"] == "From"), "")

            items.append(
                ContentItem(
                    source="gmail",
                    title=subject,
                    body=f"From: {sender}",
                    url=f"https://mail.google.com/mail/u/0/#inbox/{msg_ref['id']}",
                    timestamp=datetime.now(tz=timezone.utc),
                )
            )
    except Exception as e:
        logger.warning("Gmail fetch failed: %s", e)

    logger.info("Fetched %d Gmail items", len(items))
    return items
