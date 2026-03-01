"""Step: Check vault for due and overdue commitments."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step

from src.shared.schemas import Commitment

logger = logging.getLogger(__name__)


@step
def check_commitments() -> Annotated[list[Commitment], "due_commitments"]:
    """Scan people notes for commitments that are due or overdue."""
    from datetime import datetime, timezone

    from src.shared.config import VAULT_PEOPLE
    from src.shared.obsidian_io import read_note

    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    commitments: list[Commitment] = []

    if not VAULT_PEOPLE.exists():
        return commitments

    for md_file in VAULT_PEOPLE.glob("*.md"):
        try:
            meta, body = read_note(md_file)
            person_name = md_file.stem

            for line in body.splitlines():
                line = line.strip()
                if not line.startswith("- [ ]"):
                    continue

                # Parse commitment lines like: - [ ] Do thing (due: 2026-03-01)
                text = line[5:].strip()
                due_date = None
                if "(due:" in text:
                    due_part = text.split("(due:")[1].split(")")[0].strip()
                    due_date = due_part
                    text = text.split("(due:")[0].strip()

                status = "open"
                if due_date and due_date <= today:
                    status = "overdue"

                if due_date:
                    commitments.append(
                        Commitment(
                            person=person_name,
                            description=text,
                            due_date=due_date,
                            source=str(md_file),
                            status=status,
                        )
                    )
        except Exception as e:
            logger.warning("Error reading %s: %s", md_file, e)

    logger.info("Found %d commitments with dates", len(commitments))
    return commitments
