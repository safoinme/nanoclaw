"""Pipeline: Personal CRM — extract people and commitments from notes.

Schedule: nightly at 11 PM.

DAG:
  load_conversations --> extract_people --> update_people_notes
"""

from __future__ import annotations

from zenml import pipeline
from zenml.config.schedule import Schedule

from steps.extract_people import extract_people
from steps.load_conversations import load_conversations
from steps.update_people_notes import update_people_notes

SCHEDULE = Schedule(cron_expression="0 23 * * *")  # Nightly 11 PM


@pipeline(tags=["crm", "people"])
def personal_crm() -> None:
    """Load conversations, extract people/commitments, update vault notes."""
    notes = load_conversations()
    records = extract_people(conversation_notes=notes)
    update_people_notes(people_records=records)
