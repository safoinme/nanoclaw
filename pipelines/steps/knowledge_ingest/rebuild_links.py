"""Rebuild wikilinks across the vault after new notes are added."""

import logging
import re
from typing import Annotated

from zenml import ArtifactConfig, step
from zenml.utils.metadata_utils import log_metadata

from src.shared.config import VAULT_MOC
from src.shared.obsidian_io import (
    generate_wikilink,
    list_vault_notes,
    read_note,
    write_note,
)
from src.shared.schemas import VaultNote
from steps.knowledge_ingest.hooks import on_step_failure, on_step_success

logger = logging.getLogger(__name__)


@step(enable_cache=False, on_failure=on_step_failure, on_success=on_step_success)
def rebuild_links(
    created_notes: list[VaultNote],
    updated_notes: list[VaultNote],
) -> Annotated[dict, ArtifactConfig(name="link_rebuild_report")]:
    """Rebuild wikilinks and update MOC pages.

    1. Back-linking: scan vault for mentions of new note titles
    2. MOC update: group notes by tag, update MOC pages

    Returns:
        Dict with 'links_added' count and 'mocs_updated' list.
    """
    all_notes = created_notes + updated_notes
    if not all_notes:
        return {"links_added": 0, "mocs_updated": []}

    # Build title->wikilink mapping
    new_titles = {note.title: note.slug for note in all_notes}
    links_added = 0

    # Back-linking: scan existing vault notes
    vault_keys = list_vault_notes()
    for key in vault_keys:
        try:
            meta, body = read_note(key)
        except Exception:
            continue

        modified = False
        for title in new_titles:
            # Look for the title mentioned in the body but not already wikilinked
            pattern = re.compile(
                rf"(?<!\[\[){re.escape(title)}(?!\]\])",
                re.IGNORECASE,
            )
            if pattern.search(body):
                wikilink = generate_wikilink(title)
                body = pattern.sub(wikilink, body, count=1)
                modified = True
                links_added += 1

        if modified:
            try:
                write_note(key, body, meta)
            except Exception:
                logger.warning("Failed to update links in %s", key)

    # MOC update: group notes by tag
    tag_groups: dict[str, list[VaultNote]] = {}
    for note in all_notes:
        for tag in note.tags:
            tag_groups.setdefault(tag, []).append(note)

    mocs_updated: list[str] = []
    for tag, notes in tag_groups.items():
        if len(notes) < 2:
            continue

        moc_key = f"vault/{VAULT_MOC}/{tag}.md"
        try:
            existing_meta, existing_body = read_note(moc_key)
        except Exception:
            existing_meta = {"title": f"MOC: {tag}", "type": "moc", "tags": [tag]}
            existing_body = f"# {tag}\n\nMap of Content for *{tag}*.\n\n## Notes\n"

        # Add new wikilinks
        for note in notes:
            wikilink = generate_wikilink(note.title)
            if wikilink not in existing_body:
                existing_body += f"\n- {wikilink}"

        write_note(moc_key, existing_body, existing_meta)
        mocs_updated.append(tag)

    log_metadata({"links_added": links_added, "mocs_updated": len(mocs_updated)})
    logger.info("Links added: %d, MOCs updated: %d", links_added, len(mocs_updated))
    return {"links_added": links_added, "mocs_updated": mocs_updated}
