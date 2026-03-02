"""Extract atomic concepts from content chunks using PydanticAI."""

import logging
from typing import Annotated

from pydantic_ai import Agent
from slugify import slugify
from zenml import ArtifactConfig, step
from zenml.config.retry_config import StepRetryConfig
from zenml.utils.metadata_utils import log_metadata

from src.shared.config import AI_MODEL
from src.shared.schemas import ContentChunk, ConceptConfidence, ExtractedConcept, NoteType
from steps.knowledge_ingest.hooks import on_step_failure, on_step_success

logger = logging.getLogger(__name__)

EXTRACT_SYSTEM_PROMPT = """You are a knowledge extraction agent. Given a chunk of text, extract
distinct atomic concepts, facts, decisions, or notable people mentioned.

For each concept:
- Give it a clear, concise title
- Classify its type: concept, fact, decision, person, or article_summary
- Write a 1-3 sentence summary
- Write a fuller body with the key details in markdown
- Assign relevant tags (lowercase, no #)
- Rate your confidence: verified (cited/sourced), high (clearly stated), medium (implied), speculative (inferred)

Keep concepts atomic — one idea per concept. Prefer more granular concepts over fewer broad ones.
If the text is a conversation, extract the key topics discussed and any decisions/commitments made."""


def _create_extraction_agent() -> Agent[None, list[ExtractedConcept]]:
    return Agent(
        AI_MODEL,
        system_prompt=EXTRACT_SYSTEM_PROMPT,
        output_type=list[ExtractedConcept],
    )


@step(
    enable_cache=True,
    retry=StepRetryConfig(max_retries=2, delay=10, backoff=2),
    on_failure=on_step_failure,
    on_success=on_step_success,
)
def extract_concepts(chunk: ContentChunk) -> Annotated[
    list[ExtractedConcept], ArtifactConfig(name="extracted_concepts")
]:
    """Extract atomic concepts from a content chunk."""
    agent = _create_extraction_agent()

    prompt = f"Extract concepts from this text (chunk {chunk.chunk_index}, section: '{chunk.source_section}'):\n\n{chunk.text}"

    result = agent.run_sync(prompt)
    concepts = result.output

    # Ensure slugs are properly generated
    for concept in concepts:
        if not concept.slug:
            concept.slug = slugify(concept.title)
        else:
            concept.slug = slugify(concept.slug)
        concept.source_chunk_index = chunk.chunk_index

    log_metadata({
        "chunk_index": chunk.chunk_index,
        "concepts_extracted": len(concepts),
    })
    logger.info(
        "Extracted %d concepts from chunk %d",
        len(concepts),
        chunk.chunk_index,
    )
    return concepts
