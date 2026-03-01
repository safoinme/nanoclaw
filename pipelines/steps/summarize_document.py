"""Step: Summarize extracted document content and save to vault."""

from __future__ import annotations

import logging
from typing import Annotated

from zenml import step
from zenml.utils.metadata_utils import log_metadata

from src.shared.schemas import PipelineResult, ProcessedDocument

logger = logging.getLogger(__name__)


@step
def summarize_document(
    processed_doc: ProcessedDocument,
) -> Annotated[PipelineResult, "doc_result"]:
    """Summarize the processed document with PydanticAI and save to vault."""
    from pathlib import Path

    from pydantic_ai import Agent

    from src.shared.config import ANTHROPIC_MODEL
    from src.shared.obsidian_io import write_note

    agent = Agent(
        f"anthropic:{ANTHROPIC_MODEL}",
        system_prompt=(
            "Summarize this document content. Return JSON with: "
            "summary (2-3 paragraphs), key_points (list of strings)."
        ),
        result_type=dict,
    )

    try:
        result = agent.run_sync(processed_doc.summary)
        data = result.data
        summary = data.get("summary", processed_doc.summary)
        key_points = data.get("key_points", [])
    except Exception as e:
        logger.warning("Summarization failed: %s", e)
        summary = processed_doc.summary
        key_points = []

    # Save to vault
    original_name = Path(processed_doc.original_path).stem
    note_path = f"04-Resources/Documents/{original_name}.md"
    sections = [f"# {original_name}\n", summary]
    if key_points:
        sections.append("\n## Key Points")
        for kp in key_points:
            sections.append(f"- {kp}")

    write_note(
        note_path,
        "\n".join(sections),
        metadata={
            "type": "document",
            "source_file": processed_doc.original_path,
            "file_type": processed_doc.file_type,
            "tags": ["document", processed_doc.file_type],
        },
    )

    processed_doc.vault_note_path = note_path
    processed_doc.key_points = key_points

    log_metadata({"note_path": note_path, "key_points_count": len(key_points)})
    return PipelineResult(
        pipeline_name="document_processor",
        items_processed=1,
        notes_created=[note_path],
        message=f"Document processed: {original_name}",
    )
