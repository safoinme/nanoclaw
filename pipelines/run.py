"""CLI entry point for NanoClaw pipelines."""

import argparse
import sys

from pipelines.knowledge_ingest import knowledge_ingest_pipeline

PIPELINES = {
    "knowledge_ingest": knowledge_ingest_pipeline,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NanoClaw ZenML pipelines")
    parser.add_argument(
        "--pipeline",
        choices=list(PIPELINES.keys()),
        default="knowledge_ingest",
        help="Which pipeline to run (default: knowledge_ingest)",
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
        "--content",
        required=True,
        help="Content to ingest: URL, base64 PDF, or raw text",
    )
    parser.add_argument(
        "--content-type",
        choices=["url", "pdf_b64", "text", "conversation"],
        default="text",
        help="Type of content (default: text)",
    )
    parser.add_argument(
        "--source-title",
        default="",
        help="Optional human-readable source title",
    )
    parser.add_argument(
        "--synthesis-threshold",
        type=int,
        default=5,
        help="Minimum notes per tag to trigger synthesis (default: 5)",
    )
    args = parser.parse_args()

    pipeline_fn = PIPELINES[args.pipeline]

    options: dict = {
        "config_path": args.config,
        "enable_cache": not args.no_cache,
    }

    instance = pipeline_fn.with_options(**options)
    instance.configure(secrets=["nanoclaw_api_keys"])

    instance(
        content=args.content,
        content_type=args.content_type,
        source_title=args.source_title,
        synthesis_threshold=args.synthesis_threshold,
    )
    snapshot = instance.create_snapshot(name="knowledge_ingest", replace=True)
    print(f"Snapshot created: {snapshot.name}")

if __name__ == "__main__":
    main()
