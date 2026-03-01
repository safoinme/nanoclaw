"""Step: Scan vault for changes made in the past week."""

from __future__ import annotations

import logging
import time
from typing import Annotated

from zenml import step

from src.shared.schemas import VaultNote

logger = logging.getLogger(__name__)

SEVEN_DAYS = 7 * 24 * 3600


@step
def scan_vault_changes() -> Annotated[list[VaultNote], "changed_notes"]:
    """Find all notes created or modified in the past week."""
    from src.shared.config import VAULT_ROOT
    from src.shared.obsidian_io import read_note

    cutoff = time.time() - SEVEN_DAYS
    notes: list[VaultNote] = []

    for md_file in VAULT_ROOT.rglob("*.md"):
        try:
            stat = md_file.stat()
            if stat.st_mtime >= cutoff:
                meta, body = read_note(md_file)
                notes.append(
                    VaultNote(
                        path=str(md_file),
                        title=md_file.stem,
                        content=body,
                        frontmatter=meta,
                        tags=meta.get("tags", []),
                    )
                )
        except Exception as e:
            logger.warning("Skipping %s: %s", md_file, e)

    logger.info("Found %d notes changed in the past week", len(notes))
    return notes
