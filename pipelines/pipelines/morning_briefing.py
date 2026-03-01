"""Pipeline: Morning Briefing — fan-out/fan-in data collection and summary.

Schedule: weekdays at 7 AM.

DAG:
  fetch_github  ─┐
  fetch_gmail   ─┤
  fetch_calendar─┤
  fetch_slack   ─┼─> aggregate_briefing --> summarize_briefing --> deliver_briefing
  fetch_discord ─┤
  fetch_zenml   ─┘
"""

from __future__ import annotations

from zenml import pipeline
from zenml.config.schedule import Schedule

from steps.aggregate_briefing import aggregate_briefing
from steps.deliver_briefing import deliver_briefing
from steps.fetch_calendar import fetch_calendar
from steps.fetch_discord import fetch_discord
from steps.fetch_github import fetch_github
from steps.fetch_gmail import fetch_gmail
from steps.fetch_slack import fetch_slack
from steps.fetch_zenml_status import fetch_zenml_status
from steps.summarize_briefing import summarize_briefing

SCHEDULE = Schedule(cron_expression="0 7 * * 1-5")  # Weekdays 7 AM


@pipeline(tags=["briefing", "daily"])
def morning_briefing() -> None:
    """Fan-out data collection, fan-in aggregate, AI summary, deliver."""
    gh = fetch_github()
    gm = fetch_gmail()
    cal = fetch_calendar()
    sl = fetch_slack()
    dc = fetch_discord()
    zm = fetch_zenml_status()

    all_items = aggregate_briefing(
        github_items=gh,
        gmail_items=gm,
        calendar_items=cal,
        slack_items=sl,
        discord_items=dc,
        zenml_items=zm,
    )
    briefing = summarize_briefing(all_items=all_items)
    deliver_briefing(briefing=briefing)
