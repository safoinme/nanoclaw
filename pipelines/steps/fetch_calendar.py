"""Step: Fetch today's calendar events."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import ContentItem

logger = logging.getLogger(__name__)


@step
def fetch_calendar() -> Annotated[list[ContentItem], "calendar_items"]:
    """Fetch today's calendar events via Google Calendar API."""
    from datetime import datetime, timezone

    import httpx
    from zenml.client import Client

    items: list[ContentItem] = []
    try:
        secret = Client().get_secret("google_calendar_credentials")
        token = secret.secret_values["access_token"]

        now = datetime.now(tz=timezone.utc)
        time_min = now.replace(hour=0, minute=0, second=0).isoformat()
        time_max = now.replace(hour=23, minute=59, second=59).isoformat()

        resp = httpx.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": "true",
                "orderBy": "startTime",
            },
            timeout=30,
        )
        resp.raise_for_status()

        for event in resp.json().get("items", []):
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
            items.append(
                ContentItem(
                    source="calendar",
                    title=event.get("summary", "Untitled event"),
                    body=f"Time: {start}",
                    url=event.get("htmlLink", ""),
                    timestamp=now,
                )
            )
    except Exception as e:
        logger.warning("Calendar fetch failed: %s", e)

    logger.info("Fetched %d calendar events", len(items))
    return items
