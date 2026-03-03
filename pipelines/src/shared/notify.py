"""ZenML metadata-based notifications.

NanoClaw host reads notification_text from pipeline run metadata after
completion and delivers via Baileys (regular WhatsApp, not Cloud API).
"""

from __future__ import annotations

import logging

from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import IngestionSummary

logger = logging.getLogger(__name__)


def log_notification(text: str) -> None:
    """Store notification text in ZenML step metadata.

    The NanoClaw host process reads this after pipeline completion
    and delivers via WhatsApp (Baileys).
    """
    log_metadata({"notification_text": text})
    logger.info("Notification logged (%d chars)", len(text))


def format_ingestion_message(summary: IngestionSummary) -> str:
    """Format a knowledge ingestion notification (plain text for WhatsApp)."""
    lines: list[str] = []

    header = f"Knowledge ingested: *{summary.source_title or 'Untitled'}*"
    if summary.source_type:
        header += f" ({summary.source_type})"
    lines.append(header)

    stats = []
    if summary.concepts_extracted:
        stats.append(f"{summary.concepts_extracted} concepts extracted")
    if summary.notes_created:
        stats.append(f"{len(summary.notes_created)} notes created")
    if summary.notes_updated:
        stats.append(f"{len(summary.notes_updated)} notes updated")
    if summary.notes_skipped:
        stats.append(f"{summary.notes_skipped} duplicates skipped")
    if stats:
        lines.append(" | ".join(stats))

    if summary.notes_created:
        lines.append("\nNew notes:")
        for title in summary.notes_created[:10]:
            lines.append(f"  - {title}")
        if len(summary.notes_created) > 10:
            lines.append(f"  ... and {len(summary.notes_created) - 10} more")

    if summary.syntheses_created:
        lines.append("\nSyntheses:")
        for title in summary.syntheses_created:
            lines.append(f"  - {title}")

    if summary.errors:
        lines.append(f"\n{len(summary.errors)} error(s) occurred:")
        for err in summary.errors[:5]:
            lines.append(f"  - {err}")

    return "\n".join(lines)
