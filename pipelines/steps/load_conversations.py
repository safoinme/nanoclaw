"""Step: Load recent conversations from vault for CRM extraction."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import VaultNote

logger = logging.getLogger(__name__)


@step
def load_conversations() -> Annotated[list[VaultNote], "conversation_notes"]:
    """Load recent notes that may contain people references and commitments."""
    from src.shared.config import VAULT_DAILY, VAULT_ROOT
    from src.shared.obsidian_io import read_note

    notes: list[VaultNote] = []

    # Scan daily notes and meeting notes
    search_dirs = [VAULT_DAILY, VAULT_ROOT / "04-Resources" / "Meetings"]
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for md_file in sorted(search_dir.glob("*.md"), reverse=True)[:30]:
            try:
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

    logger.info("Loaded %d conversation notes for CRM", len(notes))
    return notes
