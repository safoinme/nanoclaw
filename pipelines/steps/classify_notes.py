"""Step: Classify and enrich inbox notes with PydanticAI."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import ClassifiedNote, NoteCategory, VaultNote

logger = logging.getLogger(__name__)


@step
def classify_notes(
    inbox_notes: list[VaultNote],
) -> Annotated[list[ClassifiedNote], "classified_notes"]:
    """Classify each inbox note into a category using PydanticAI."""
    from pydantic_ai import Agent

    from src.shared.config import ANTHROPIC_MODEL

    agent = Agent(
        f"anthropic:{ANTHROPIC_MODEL}",
        system_prompt=(
            "You classify Obsidian notes into categories. "
            "Return a JSON object with: category (one of: reference, project, task, "
            "idea, meeting, person, resource), tags (list of strings), "
            "summary (1-2 sentences), suggested_links (list of related topic names)."
        ),
        result_type=dict,
    )

    category_to_folder = {
        NoteCategory.REFERENCE: "04-Resources",
        NoteCategory.PROJECT: "03-Projects",
        NoteCategory.TASK: "03-Projects/Tasks",
        NoteCategory.IDEA: "04-Resources/Ideas",
        NoteCategory.MEETING: "04-Resources/Meetings",
        NoteCategory.PERSON: "05-People",
        NoteCategory.RESOURCE: "04-Resources",
    }

    classified: list[ClassifiedNote] = []
    for note in inbox_notes:
        try:
            result = agent.run_sync(
                f"Title: {note.title}\n\nContent:\n{note.content[:2000]}"
            )
            data = result.data
            cat = NoteCategory(data.get("category", "reference"))
            classified.append(
                ClassifiedNote(
                    source_path=note.path,
                    title=note.title,
                    category=cat,
                    tags=data.get("tags", []),
                    destination_folder=category_to_folder.get(cat, "04-Resources"),
                    summary=data.get("summary", ""),
                    wikilinks=data.get("suggested_links", []),
                )
            )
        except Exception as e:
            logger.warning("Failed to classify %s: %s", note.title, e)
            classified.append(
                ClassifiedNote(
                    source_path=note.path,
                    title=note.title,
                    category=NoteCategory.REFERENCE,
                    destination_folder="04-Resources",
                )
            )

    log_metadata({"notes_classified": len(classified)})
    return classified
