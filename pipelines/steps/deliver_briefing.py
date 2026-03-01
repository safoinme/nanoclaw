"""Step: Deliver briefing via WhatsApp and archive to vault."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import MorningBriefing, PipelineResult

logger = logging.getLogger(__name__)


@step
def deliver_briefing(
    briefing: MorningBriefing,
) -> Annotated[PipelineResult, "briefing_result"]:
    """Send briefing to WhatsApp and save to vault."""
    from src.shared.obsidian_io import write_note
    from src.shared.whatsapp_notify import format_briefing_message, send_whatsapp_message

    # Format and send WhatsApp message
    wa_message = format_briefing_message(
        summary=briefing.summary,
        action_items=briefing.analysis.action_items,
        highlights=briefing.analysis.key_highlights,
    )
    sent = send_whatsapp_message(wa_message)

    # Archive to vault as daily note
    note_path = f"01-Daily/{briefing.date}-briefing.md"
    sections = [f"# Morning Briefing — {briefing.date}\n", briefing.summary]

    if briefing.analysis.key_highlights:
        sections.append("\n## Highlights")
        for h in briefing.analysis.key_highlights:
            sections.append(f"- {h}")

    if briefing.analysis.action_items:
        sections.append("\n## Action Items")
        for i, a in enumerate(briefing.analysis.action_items, 1):
            sections.append(f"{i}. {a}")

    for source, items in briefing.items_by_source.items():
        sections.append(f"\n## {source.title()}")
        for item in items:
            sections.append(f"- {item.title}")

    write_note(
        note_path,
        "\n".join(sections),
        metadata={"type": "briefing", "date": briefing.date, "tags": ["briefing", "daily"]},
    )

    log_metadata({"whatsapp_sent": sent, "vault_note": note_path})
    return PipelineResult(
        pipeline_name="morning_briefing",
        items_processed=sum(len(v) for v in briefing.items_by_source.values()),
        notes_created=[note_path],
        message=f"Briefing delivered (WhatsApp: {'sent' if sent else 'skipped'})",
    )
