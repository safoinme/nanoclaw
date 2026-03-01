"""Pipeline: Inbox Processor — classify and organize inbox notes.

Schedule: daily at midnight.

DAG:
  scan_inbox --> classify_notes --> move_notes
"""

from __future__ import annotations

from zenml import pipeline
from zenml.config.schedule import Schedule

from steps.classify_notes import classify_notes
from steps.move_notes import move_notes
from steps.scan_inbox import scan_inbox

SCHEDULE = Schedule(cron_expression="0 0 * * *")  # Daily midnight


@pipeline(tags=["obsidian", "inbox"])
def inbox_processor(inbox_path: str = "") -> None:
    """Scan inbox, classify with AI, move to permanent locations, update MOCs."""
    notes = scan_inbox(inbox_path=inbox_path)
    classified = classify_notes(inbox_notes=notes)
    move_notes(classified_notes=classified)
