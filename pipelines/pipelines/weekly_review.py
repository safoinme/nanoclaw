"""Pipeline: Weekly Review — scan vault, check commitments, find connections.

Schedule: Sundays at 10 AM.

DAG:
  scan_vault_changes ─┐
  check_commitments  ─┼─> compile_weekly_review
  detect_orphans     ─┘
"""

from __future__ import annotations

from zenml import pipeline
from zenml.config.schedule import Schedule

from steps.check_commitments import check_commitments
from steps.compile_weekly_review import compile_weekly_review
from steps.detect_orphans import detect_orphans
from steps.scan_vault_changes import scan_vault_changes

SCHEDULE = Schedule(cron_expression="0 10 * * 0")  # Sunday 10 AM


@pipeline(tags=["review", "weekly"])
def weekly_review() -> None:
    """Scan changes, check commitments, detect orphans, compile review."""
    changed = scan_vault_changes()
    commitments = check_commitments()
    orphans, connections = detect_orphans(changed_notes=changed)
    compile_weekly_review(
        changed_notes=changed,
        due_commitments=commitments,
        orphan_notes=orphans,
        suggested_connections=connections,
    )
