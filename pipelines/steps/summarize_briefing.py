"""Step: Summarize aggregated items into a morning briefing using PydanticAI."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import AnalysisSummary, ContentItem, MorningBriefing

logger = logging.getLogger(__name__)


@step
def summarize_briefing(
    all_items: dict[str, list[ContentItem]],
) -> Annotated[MorningBriefing, "briefing"]:
    """Use PydanticAI to generate a morning briefing summary."""
    from pydantic_ai import Agent

    from src.shared.config import ANTHROPIC_MODEL

    # Flatten items into a text block for the LLM
    lines: list[str] = []
    for source, items in all_items.items():
        if items:
            lines.append(f"\n## {source.upper()}")
            for item in items:
                prio = f" [!{item.priority}]" if item.priority != "normal" else ""
                lines.append(f"- {item.title}{prio}")
                if item.body:
                    lines.append(f"  {item.body[:200]}")

    context = "\n".join(lines) if lines else "No items found from any source."

    agent = Agent(
        f"anthropic:{ANTHROPIC_MODEL}",
        system_prompt=(
            "You are a personal assistant creating a morning briefing. "
            "Analyze the collected data and produce a JSON object with: "
            "summary (2-3 paragraph overview), key_highlights (list of strings), "
            "action_items (list of strings), people_mentions (list of {name, context, source}), "
            "calendar_conflicts (list of strings if any scheduling issues)."
        ),
        result_type=dict,
    )

    try:
        result = agent.run_sync(context)
        data = result.data
        analysis = AnalysisSummary(
            key_highlights=data.get("key_highlights", []),
            action_items=data.get("action_items", []),
            people_mentions=[],
            calendar_conflicts=data.get("calendar_conflicts", []),
        )
    except Exception as e:
        logger.error("Briefing summarization failed: %s", e)
        analysis = AnalysisSummary(
            key_highlights=["Summarization failed — check logs"],
        )

    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    briefing = MorningBriefing(
        date=today,
        summary=data.get("summary", "Briefing generation incomplete.") if "data" in dir() else "",
        analysis=analysis,
        items_by_source={k: v for k, v in all_items.items() if v},
    )

    total_items = sum(len(v) for v in all_items.values())
    log_metadata({"total_items": total_items, "sources_with_data": len(briefing.items_by_source)})
    return briefing
