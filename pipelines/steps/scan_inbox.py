"""Step: Scan inbox folder for unprocessed notes."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.obsidian_io import list_inbox_notes, read_note
from src.shared.schemas import VaultNote

logger = logging.getLogger(__name__)


@step
def scan_inbox(inbox_path: str = "") -> Annotated[list[VaultNote], "inbox_notes"]:
    """Scan the Obsidian inbox folder and return all notes."""
    from pathlib import Path

    from src.shared.config import VAULT_INBOX

    path = Path(inbox_path) if inbox_path else VAULT_INBOX
    files = list_inbox_notes(path)
    logger.info("Found %d notes in inbox", len(files))

    notes: list[VaultNote] = []
    for f in files:
        try:
            meta, body = read_note(f)
            notes.append(
                VaultNote(
                    path=str(f),
                    title=f.stem,
                    content=body,
                    frontmatter=meta,
                    tags=meta.get("tags", []),
                )
            )
        except Exception as e:
            logger.warning("Skipping %s: %s", f, e)

    return notes
