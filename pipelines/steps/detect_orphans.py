"""Step: Detect orphan notes and suggest connections."""

from __future__ import annotations

import logging
import re
from typing import Annotated, Tuple

from zenml import step

from src.shared.schemas import VaultNote

logger = logging.getLogger(__name__)

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


@step
def detect_orphans(
    changed_notes: list[VaultNote],
) -> Tuple[
    Annotated[list[str], "orphan_notes"],
    Annotated[list[str], "suggested_connections"],
]:
    """Find notes with no incoming/outgoing links and suggest connections."""
    from src.shared.config import VAULT_ROOT

    # Build link graph from all vault notes
    all_notes: dict[str, set[str]] = {}  # title -> set of outgoing link targets
    for md_file in VAULT_ROOT.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            links = set(WIKILINK_RE.findall(content))
            all_notes[md_file.stem] = links
        except Exception:
            continue

    # Find notes with no incoming links
    all_targets: set[str] = set()
    for links in all_notes.values():
        all_targets.update(links)

    orphans: list[str] = []
    for title in all_notes:
        if title not in all_targets and not all_notes[title]:
            orphans.append(title)

    # Suggest connections for changed notes based on shared tags/keywords
    suggestions: list[str] = []
    changed_titles = {n.title for n in changed_notes}
    for note in changed_notes:
        note_words = set(note.title.lower().split())
        for other_title, other_links in all_notes.items():
            if other_title == note.title or note.title in other_links:
                continue
            other_words = set(other_title.lower().split())
            common = note_words & other_words - {"the", "a", "and", "or", "in", "of", "to"}
            if common:
                suggestions.append(f"[[{note.title}]] <-> [[{other_title}]] (shared: {', '.join(common)})")

    logger.info("Found %d orphans, %d suggested connections", len(orphans), len(suggestions))
    return orphans[:50], suggestions[:50]
