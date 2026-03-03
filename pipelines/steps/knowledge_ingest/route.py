"""Route concepts to vault notes (create or update)."""

import logging
from typing import Annotated

from pydantic_ai import Agent
from zenml import ArtifactConfig, step
from zenml.config.retry_config import StepRetryConfig
from zenml.utils.metadata_utils import log_metadata

from src.shared.config import (
    AI_MODEL,
    VAULT_ARTICLES,
    VAULT_CONCEPTS,
    VAULT_DECISIONS,
    VAULT_MOC,
    VAULT_PEOPLE,
)
from src.shared.materializers import VaultNoteMaterializer
from src.shared.obsidian_io import read_note
from src.shared.schemas import CrossRefResult, NoteStatus, NoteType, VaultNote
from steps.knowledge_ingest.hooks import on_step_failure, on_step_success

logger = logging.getLogger(__name__)

# Map NoteType to vault folder
NOTE_TYPE_FOLDERS: dict[NoteType, str] = {
    NoteType.CONCEPT: VAULT_CONCEPTS,
    NoteType.FACT: VAULT_CONCEPTS,
    NoteType.DECISION: VAULT_DECISIONS,
    NoteType.PERSON: VAULT_PEOPLE,
    NoteType.ARTICLE_SUMMARY: VAULT_ARTICLES,
    NoteType.MOC: VAULT_MOC,
    NoteType.SYNTHESIS: VAULT_MOC,
}


@step(
    enable_cache=True,
    on_failure=on_step_failure,
    on_success=on_step_success,
    output_materializers={"created_note": VaultNoteMaterializer},
)
def create_note(xref: CrossRefResult, source_url: str, source_title: str) -> Annotated[
    VaultNote, ArtifactConfig(name="created_note")
]:
    """Create a new VaultNote from an extracted concept."""
    concept = xref.concept
    folder = NOTE_TYPE_FOLDERS.get(concept.note_type, VAULT_CONCEPTS)

    content = concept.body if concept.body else concept.summary

    note = VaultNote(
        title=concept.title,
        slug=concept.slug,
        note_type=concept.note_type,
        folder=folder,
        content=content,
        tags=concept.tags,
        wikilinks=[],
        status=NoteStatus.SEEDLING,
        confidence=concept.confidence,
        source_url=source_url,
        source_title=source_title,
    )
    log_metadata({"note_title": note.title, "folder": note.folder, "action": "create"})
    return note


MERGE_SYSTEM_PROMPT = """You are a knowledge note editor. You will receive an existing vault note
and new information about the same topic. Merge the new information into the existing note.

Rules:
- Preserve all existing information
- Add new information that isn't already covered
- Remove duplicates
- Keep the same overall structure and style
- Return only the updated markdown body (no frontmatter)"""


@step(
    enable_cache=False,
    retry=StepRetryConfig(max_retries=2, delay=10, backoff=2),
    on_failure=on_step_failure,
    on_success=on_step_success,
    output_materializers={"updated_note": VaultNoteMaterializer},
)
def update_note(xref: CrossRefResult) -> Annotated[
    VaultNote, ArtifactConfig(name="updated_note")
]:
    """Update an existing vault note with new information from a concept."""
    concept = xref.concept
    existing_key = xref.existing_note_key

    # Read existing note
    existing_meta: dict = {}
    existing_body: str = ""
    if existing_key:
        try:
            existing_meta, existing_body = read_note(existing_key)
        except Exception:
            logger.warning("Could not read existing note %s, creating new", existing_key)

    folder = NOTE_TYPE_FOLDERS.get(concept.note_type, VAULT_CONCEPTS)

    if existing_body:
        # Use PydanticAI to merge content
        agent = Agent(
            AI_MODEL,
            system_prompt=MERGE_SYSTEM_PROMPT,
            output_type=str,
        )

        prompt = f"""Existing note:
---
{existing_body}
---

New information to merge:
Title: {concept.title}
Summary: {concept.summary}
Body: {concept.body}
"""
        result = agent.run_sync(prompt)
        merged_content = result.output
    else:
        merged_content = concept.body if concept.body else concept.summary

    # Merge tags
    existing_tags = existing_meta.get("tags", [])
    if isinstance(existing_tags, str):
        existing_tags = [existing_tags]
    merged_tags = list(set(existing_tags + concept.tags))

    note = VaultNote(
        title=existing_meta.get("title", concept.title),
        slug=concept.slug,
        note_type=concept.note_type,
        folder=folder,
        content=merged_content,
        tags=merged_tags,
        wikilinks=existing_meta.get("wikilinks", []),
        confidence=concept.confidence,
        source_url=existing_meta.get("source_url", ""),
        source_title=existing_meta.get("source_title", ""),
    )
    log_metadata({"note_title": note.title, "folder": note.folder, "action": "update"})
    return note
