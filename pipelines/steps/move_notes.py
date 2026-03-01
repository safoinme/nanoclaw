"""Step: Move classified notes to permanent locations and update MOCs."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.config import VAULT_ROOT
from src.shared.obsidian_io import generate_wikilink, read_note, write_note
from src.shared.schemas import ClassifiedNote, PipelineResult

logger = logging.getLogger(__name__)


@step
def move_notes(
    classified_notes: list[ClassifiedNote],
) -> Annotated[PipelineResult, "inbox_result"]:
    """Move notes from inbox to their classified destinations."""
    created: list[str] = []
    errors: list[str] = []

    for note in classified_notes:
        try:
            src = Path(note.source_path)
            if not src.exists():
                errors.append(f"Source not found: {note.source_path}")
                continue

            dest_dir = VAULT_ROOT / note.destination_folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name

            # Read original, enrich frontmatter
            meta, body = read_note(src)
            meta["tags"] = list(set(meta.get("tags", []) + note.tags))
            meta["category"] = note.category.value
            if note.summary:
                meta["summary"] = note.summary

            # Add wikilinks to body
            if note.wikilinks:
                links = " ".join(generate_wikilink(w) for w in note.wikilinks)
                body += f"\n\n## Related\n{links}\n"

            write_note(dest, body, meta)

            # Remove from inbox
            if src != dest:
                src.unlink()

            created.append(str(dest))
            logger.info("Moved %s -> %s", src.name, dest)

        except Exception as e:
            errors.append(f"{note.title}: {e}")
            logger.error("Failed to move %s: %s", note.title, e)

    log_metadata({"notes_moved": len(created), "errors": len(errors)})
    return PipelineResult(
        pipeline_name="inbox_processor",
        items_processed=len(classified_notes),
        notes_created=created,
        errors=errors,
        message=f"Processed {len(classified_notes)} inbox notes, moved {len(created)}",
    )
