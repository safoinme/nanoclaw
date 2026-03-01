"""Step: Fetch recent ZenML pipeline run statuses."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import ContentItem

logger = logging.getLogger(__name__)


@step
def fetch_zenml_status() -> Annotated[list[ContentItem], "zenml_items"]:
    """Fetch recent ZenML pipeline run statuses."""
    from datetime import datetime, timezone

    from zenml.client import Client

    items: list[ContentItem] = []
    try:
        client = Client()
        runs = client.list_pipeline_runs(sort_by="desc:created", size=10)
        for run in runs:
            items.append(
                ContentItem(
                    source="zenml",
                    title=f"{run.pipeline.name} — {run.status}",
                    body=f"Run {run.name} ({run.status})",
                    timestamp=datetime.now(tz=timezone.utc),
                    priority="high" if run.status == "failed" else "normal",
                )
            )
    except Exception as e:
        logger.warning("ZenML status fetch failed: %s", e)

    logger.info("Fetched %d ZenML status items", len(items))
    return items
