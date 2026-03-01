"""Step: Update or create people notes in the vault."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import PipelineResult, PersonRecord

logger = logging.getLogger(__name__)


@step
def update_people_notes(
    people_records: list[PersonRecord],
) -> Annotated[PipelineResult, "crm_result"]:
    """Create or update vault notes for each person."""
    from pathlib import Path

    from src.shared.config import VAULT_PEOPLE
    from src.shared.obsidian_io import generate_wikilink, read_note, write_note

    created: list[str] = []
    updated: list[str] = []
    overdue: list[str] = []

    for person in people_records:
        note_path = VAULT_PEOPLE / f"{person.name}.md"
        person.vault_note_path = str(note_path)

        try:
            if note_path.exists():
                meta, existing_body = read_note(note_path)
                # Merge new topics
                existing_tags = set(meta.get("tags", []))
                existing_tags.update(person.topics)
                meta["tags"] = sorted(existing_tags)
                meta["last_contact"] = person.last_contact or meta.get("last_contact", "")

                # Append new commitments
                commitment_lines = []
                for c in person.commitments:
                    status = "overdue" if c.status == "overdue" else "open"
                    line = f"- [ ] {c.description}"
                    if c.due_date:
                        line += f" (due: {c.due_date})"
                    commitment_lines.append(line)
                    if status == "overdue":
                        overdue.append(f"{person.name}: {c.description}")

                if commitment_lines:
                    existing_body += "\n\n## Recent Commitments\n" + "\n".join(commitment_lines)

                write_note(note_path, existing_body, meta)
                updated.append(str(note_path))
            else:
                # Create new person note
                meta = {
                    "type": "person",
                    "tags": sorted(set(["person"] + person.topics)),
                    "last_contact": person.last_contact or "",
                }
                sections = [f"# {person.name}\n"]
                if person.topics:
                    sections.append("## Topics")
                    for t in person.topics:
                        sections.append(f"- {t}")
                if person.commitments:
                    sections.append("\n## Commitments")
                    for c in person.commitments:
                        line = f"- [ ] {c.description}"
                        if c.due_date:
                            line += f" (due: {c.due_date})"
                        sections.append(line)

                write_note(note_path, "\n".join(sections), meta)
                created.append(str(note_path))
        except Exception as e:
            logger.error("Failed to update %s: %s", person.name, e)

    log_metadata({
        "people_created": len(created),
        "people_updated": len(updated),
        "overdue_commitments": len(overdue),
    })

    return PipelineResult(
        pipeline_name="personal_crm",
        items_processed=len(people_records),
        notes_created=created,
        notes_updated=updated,
        errors=overdue,  # Using errors field for overdue items
        message=f"CRM: {len(created)} created, {len(updated)} updated, {len(overdue)} overdue",
    )
