"""CLI entry point for NanoClaw pipelines."""

from __future__ import annotations

import argparse
import sys

from pipelines.content_monitor import SCHEDULE as CONTENT_SCHEDULE
from pipelines.content_monitor import content_monitor
from pipelines.document_processor import document_processor
from pipelines.inbox_processor import SCHEDULE as INBOX_SCHEDULE
from pipelines.inbox_processor import inbox_processor
from pipelines.morning_briefing import SCHEDULE as BRIEFING_SCHEDULE
from pipelines.morning_briefing import morning_briefing
from pipelines.personal_crm import SCHEDULE as CRM_SCHEDULE
from pipelines.personal_crm import personal_crm
from pipelines.weekly_review import SCHEDULE as REVIEW_SCHEDULE
from pipelines.weekly_review import weekly_review

PIPELINES = {
    "inbox_processor": (inbox_processor, INBOX_SCHEDULE),
    "morning_briefing": (morning_briefing, BRIEFING_SCHEDULE),
    "personal_crm": (personal_crm, CRM_SCHEDULE),
    "document_processor": (document_processor, None),
    "weekly_review": (weekly_review, REVIEW_SCHEDULE),
    "content_monitor": (content_monitor, CONTENT_SCHEDULE),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NanoClaw ZenML pipelines")
    parser.add_argument(
        "--pipeline",
        choices=list(PIPELINES.keys()),
        required=True,
        help="Which pipeline to run",
    )
    parser.add_argument(
        "--config",
        default="configs/dev.yaml",
        help="Path to YAML config (default: configs/dev.yaml)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable step caching",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Deploy with the pipeline's default schedule",
    )
    parser.add_argument(
        "--file-path",
        default="",
        help="File path for document_processor pipeline",
    )
    args = parser.parse_args()

    pipeline_fn, schedule = PIPELINES[args.pipeline]

    options: dict = {
        "config_path": args.config,
        "enable_cache": not args.no_cache,
    }

    if args.schedule and schedule is not None:
        options["schedule"] = schedule
    elif args.schedule and schedule is None:
        print(f"Pipeline '{args.pipeline}' does not support scheduling (on-demand only).")
        sys.exit(1)

    instance = pipeline_fn.with_options(**options)

    # Pass pipeline-specific parameters
    if args.pipeline == "document_processor" and args.file_path:
        instance(file_path=args.file_path)
    else:
        instance()


if __name__ == "__main__":
    main()
