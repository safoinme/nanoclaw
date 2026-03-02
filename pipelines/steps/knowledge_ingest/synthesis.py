"""Synthesis steps: check if topics need synthesis, generate MOCs."""

import logging
from typing import Annotated

from pydantic_ai import Agent
from zenml import ArtifactConfig, step
from zenml.config.retry_config import StepRetryConfig
from zenml.utils.metadata_utils import log_metadata

from src.shared.config import AI_MODEL, VAULT_MOC
from src.shared.materializers import VaultNoteMaterializer
from src.shared.obsidian_io import read_note, search_vault_by_tags
from src.shared.schemas import NoteType, NoteStatus, ConceptConfidence, SynthesisCheck, VaultNote
from steps.knowledge_ingest.hooks import on_step_failure, on_step_success

logger = logging.getLogger(__name__)


@step(enable_cache=False, on_failure=on_step_failure, on_success=on_step_success)
def check_synthesis(
    created_notes: list[VaultNote],
    threshold: int,
) -> Annotated[list[SynthesisCheck], ArtifactConfig(name="synthesis_checks")]:
    """Check which topics have enough notes to warrant synthesis.

    Groups notes by tag, counts vault notes with each tag,
    and flags topics that exceed the threshold.
    """
    # Collect all tags from new notes
    tag_counts: dict[str, list[str]] = {}
    for note in created_notes:
        for tag in note.tags:
            tag_counts.setdefault(tag, []).append(note.title)

    checks: list[SynthesisCheck] = []
    for tag, new_titles in tag_counts.items():
        # Count existing vault notes with this tag
        existing = search_vault_by_tags([tag])
        total_count = len(existing) + len(new_titles)

        all_titles = new_titles.copy()
        for key in existing:
            try:
                meta, _ = read_note(key)
                all_titles.append(meta.get("title", key.rsplit("/", 1)[-1]))
            except Exception:
                continue

        should_synth = total_count >= threshold
        checks.append(
            SynthesisCheck(
                topic=tag,
                note_count=total_count,
                note_titles=all_titles,
                should_synthesize=should_synth,
            )
        )
        if should_synth:
            logger.info("Topic '%s' has %d notes, synthesis triggered", tag, total_count)

    log_metadata({
        "topics_checked": len(checks),
        "topics_to_synthesize": sum(1 for c in checks if c.should_synthesize),
    })
    return checks


SYNTHESIS_PROMPT = """You are a knowledge synthesizer. Given a topic and a set of related notes,
create a comprehensive Map of Content (MOC) that:

1. Provides a high-level overview of the topic
2. Identifies key themes and relationships between notes
3. Groups related notes together
4. Highlights gaps or areas for further exploration
5. Uses [[wikilinks]] to reference the notes

Format as clean markdown. Use ## for sections. Include a brief introduction."""


@step(
    enable_cache=True,
    retry=StepRetryConfig(max_retries=2, delay=15, backoff=2),
    on_failure=on_step_failure,
    on_success=on_step_success,
    output_materializers={"synthesis_note": VaultNoteMaterializer},
)
def synthesize_topic(topic: str, note_titles: list[str]) -> Annotated[
    VaultNote, ArtifactConfig(name="synthesis_note")
]:
    """Generate a comprehensive MOC for a topic from its related notes.

    Reads the actual note content from the vault, then uses PydanticAI
    to generate a synthesis.
    """
    # Gather note content
    notes_content: list[str] = []
    for title in note_titles:
        # Try to find the note in the vault
        from src.shared.obsidian_io import list_vault_notes

        for key in list_vault_notes():
            try:
                meta, body = read_note(key)
                if meta.get("title") == title:
                    notes_content.append(f"## {title}\n\n{body}")
                    break
            except Exception:
                continue

    agent = Agent(
        AI_MODEL,
        system_prompt=SYNTHESIS_PROMPT,
        output_type=str,
    )

    prompt = f"""Topic: {topic}
Number of related notes: {len(note_titles)}

Notes:
{"---".join(notes_content) if notes_content else chr(10).join(f"- [[{t}]]" for t in note_titles)}
"""

    result = agent.run_sync(prompt)

    from slugify import slugify

    return VaultNote(
        title=f"MOC: {topic}",
        slug=slugify(f"moc-{topic}"),
        note_type=NoteType.SYNTHESIS,
        folder=VAULT_MOC,
        content=result.output,
        tags=[topic],
        wikilinks=[f"[[{t}]]" for t in note_titles],
        status=NoteStatus.DEVELOPING,
        confidence=ConceptConfidence.HIGH,
    )
