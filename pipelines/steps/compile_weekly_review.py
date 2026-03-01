"""Step: Compile the weekly review report and save to vault."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import Commitment, PipelineResult, VaultNote, WeeklyReviewReport

logger = logging.getLogger(__name__)


@step
def compile_weekly_review(
    changed_notes: list[VaultNote],
    due_commitments: list[Commitment],
    orphan_notes: list[str],
    suggested_connections: list[str],
) -> Annotated[PipelineResult, "review_result"]:
    """Compile all review data into a report and save to vault."""
    from datetime import datetime, timedelta, timezone

    from pydantic_ai import Agent

    from src.shared.config import ANTHROPIC_MODEL
    from src.shared.obsidian_io import write_note
    from src.shared.whatsapp_notify import send_whatsapp_message

    now = datetime.now(tz=timezone.utc)
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")

    overdue = [c for c in due_commitments if c.status == "overdue"]
    upcoming = [c for c in due_commitments if c.status == "open"]

    # AI summary
    context = (
        f"Notes changed: {len(changed_notes)}\n"
        f"Commitments due: {len(upcoming)}\n"
        f"Commitments overdue: {len(overdue)}\n"
        f"Orphan notes: {len(orphan_notes)}\n"
        f"Overdue items: {', '.join(c.description for c in overdue[:5])}\n"
    )

    try:
        agent = Agent(
            f"anthropic:{ANTHROPIC_MODEL}",
            system_prompt="Write a brief weekly review summary (2-3 paragraphs).",
            result_type=str,
        )
        result = agent.run_sync(context)
        summary = result.data
    except Exception as e:
        logger.warning("Review summary failed: %s", e)
        summary = f"Weekly review {week_start} to {week_end}: {len(changed_notes)} notes changed."

    # Save to vault
    note_path = f"01-Daily/{week_end}-weekly-review.md"
    sections = [
        f"# Weekly Review — {week_start} to {week_end}\n",
        summary,
        f"\n## Stats\n- Notes created/modified: {len(changed_notes)}",
        f"- Orphan notes: {len(orphan_notes)}",
    ]

    if overdue:
        sections.append("\n## Overdue Commitments")
        for c in overdue:
            sections.append(f"- {c.person}: {c.description} (due: {c.due_date})")

    if upcoming:
        sections.append("\n## Upcoming Commitments")
        for c in upcoming:
            sections.append(f"- {c.person}: {c.description} (due: {c.due_date})")

    if suggested_connections:
        sections.append("\n## Suggested Connections")
        for s in suggested_connections[:10]:
            sections.append(f"- {s}")

    write_note(
        note_path,
        "\n".join(sections),
        metadata={
            "type": "weekly-review",
            "week_start": week_start,
            "week_end": week_end,
            "tags": ["review", "weekly"],
        },
    )

    # Notify via WhatsApp
    wa_msg = f"Weekly Review ({week_start} to {week_end}):\n{summary[:500]}"
    if overdue:
        wa_msg += f"\n\nOverdue ({len(overdue)}):"
        for c in overdue[:3]:
            wa_msg += f"\n- {c.person}: {c.description}"
    send_whatsapp_message(wa_msg)

    log_metadata({
        "notes_changed": len(changed_notes),
        "overdue": len(overdue),
        "orphans": len(orphan_notes),
    })

    return PipelineResult(
        pipeline_name="weekly_review",
        items_processed=len(changed_notes),
        notes_created=[note_path],
        message=f"Weekly review: {len(changed_notes)} notes, {len(overdue)} overdue",
    )
