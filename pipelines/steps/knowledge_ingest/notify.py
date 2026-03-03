"""Notify the user of ingestion results."""

import logging

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.notify import format_ingestion_message, log_notification
from src.shared.schemas import IngestionSummary
from steps.knowledge_ingest.hooks import on_step_failure, on_step_success

logger = logging.getLogger(__name__)


@step(enable_cache=False, on_failure=on_step_failure, on_success=on_step_success)
def notify(summary: IngestionSummary) -> None:
    """Format and log the ingestion summary as a notification."""
    text = format_ingestion_message(summary)
    log_notification(text)
    log_metadata({
        "notification_sent": True,
        "concepts_extracted": summary.concepts_extracted,
        "notes_created": len(summary.notes_created),
        "notes_updated": len(summary.notes_updated),
    })
    logger.info("Ingestion notification sent: %s", text[:100])
