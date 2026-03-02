"""Cross-reference extracted concepts against the existing vault."""

import logging
import re
from typing import Annotated

from zenml import ArtifactConfig, step
from zenml.utils.metadata_utils import log_metadata

from src.shared.obsidian_io import list_vault_notes, read_note
from src.shared.schemas import CrossRefResult, ExtractedConcept
from steps.knowledge_ingest.hooks import on_step_failure, on_step_success

logger = logging.getLogger(__name__)


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Compute Jaccard similarity between two sets of words."""
    if not a or not b:
        return 0.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union)


def _normalize_words(text: str) -> set[str]:
    """Normalize text to a set of lowercase words."""
    return set(re.sub(r"[^a-z0-9\s]", "", text.lower()).split())


@step(enable_cache=False, on_failure=on_step_failure, on_success=on_step_success)
def cross_reference(concept: ExtractedConcept) -> Annotated[
    CrossRefResult, ArtifactConfig(name="cross_ref_result")
]:
    """Cross-reference a concept against the existing vault.

    Layer 1: Scan vault notes for filename/title similarity (Jaccard).
    Layer 2: Check ZenML artifact store for previous extractions.

    Decision thresholds:
    - similarity < 0.5 -> create
    - similarity >= 0.5 -> update
    - exact title match in artifact store -> skip
    """
    concept_words = _normalize_words(concept.title)
    best_score = 0.0
    best_key: str | None = None
    best_source = ""

    # Layer 1: Vault scan (filename + title similarity)
    vault_keys = list_vault_notes()
    for key in vault_keys:
        # Check filename similarity
        filename = key.rsplit("/", 1)[-1].removesuffix(".md")
        filename_words = _normalize_words(filename.replace("-", " "))
        score = _jaccard_similarity(concept_words, filename_words)

        if score > best_score:
            best_score = score
            best_key = key
            best_source = "filename"

        # Check title in frontmatter
        if score < 0.5:
            try:
                meta, _ = read_note(key)
                title = meta.get("title", "")
                if title:
                    title_words = _normalize_words(title)
                    title_score = _jaccard_similarity(concept_words, title_words)
                    if title_score > best_score:
                        best_score = title_score
                        best_key = key
                        best_source = "title"
            except Exception:
                continue

    # Layer 2: Check artifact store for exact duplicates
    try:
        from zenml.client import Client

        client = Client()
        existing = client.list_artifact_versions(
            name=concept.slug,
            sort_by="desc:created",
            size=1,
        )
        if existing.items:
            logger.info("Exact match in artifact store for '%s', skipping", concept.slug)
            return CrossRefResult(
                concept=concept,
                action="skip",
                similarity_score=1.0,
                match_source="artifact_store",
            )
    except Exception:
        pass

    # Decision
    if best_score >= 0.5:
        action = "update"
        logger.info(
            "Concept '%s' matches existing note (%.2f via %s): %s",
            concept.title,
            best_score,
            best_source,
            best_key,
        )
    else:
        action = "create"
        best_key = None

    result = CrossRefResult(
        concept=concept,
        action=action,
        existing_note_key=best_key,
        similarity_score=best_score,
        match_source=best_source,
    )
    log_metadata({"action": result.action, "similarity": result.similarity_score})
    return result
