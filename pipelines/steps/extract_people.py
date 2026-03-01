"""Step: Extract people and commitments from conversation notes."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import Commitment, PersonRecord, VaultNote

logger = logging.getLogger(__name__)


@step
def extract_people(
    conversation_notes: list[VaultNote],
) -> Annotated[list[PersonRecord], "people_records"]:
    """Use PydanticAI to extract people and commitments from notes."""
    from pydantic_ai import Agent

    from src.shared.config import ANTHROPIC_MODEL

    agent = Agent(
        f"anthropic:{ANTHROPIC_MODEL}",
        system_prompt=(
            "Extract people mentioned and any commitments/follow-ups from the text. "
            "Return a JSON object with: people (list of {name, topics (list), "
            "commitments (list of {description, due_date or null})}). "
            "Only include real people, not generic references."
        ),
        result_type=dict,
    )

    people_map: dict[str, PersonRecord] = {}

    for note in conversation_notes:
        try:
            result = agent.run_sync(
                f"Source: {note.title}\n\n{note.content[:3000]}"
            )
            data = result.data
            for person_data in data.get("people", []):
                name = person_data.get("name", "").strip()
                if not name:
                    continue

                if name not in people_map:
                    people_map[name] = PersonRecord(name=name)

                record = people_map[name]
                record.last_contact = note.title  # Use note title as date reference
                record.topics.extend(person_data.get("topics", []))

                for c in person_data.get("commitments", []):
                    record.commitments.append(
                        Commitment(
                            person=name,
                            description=c.get("description", ""),
                            due_date=c.get("due_date"),
                            source=note.title,
                        )
                    )
        except Exception as e:
            logger.warning("Extraction failed for %s: %s", note.title, e)

    records = list(people_map.values())
    # Deduplicate topics
    for r in records:
        r.topics = list(set(r.topics))

    log_metadata({"people_found": len(records)})
    return records
