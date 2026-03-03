"""Knowledge Ingestion & Synthesis — dynamic pipeline.

Acquires content (URL/PDF/text), chunks it, fans out per-chunk concept
extraction, cross-references the vault, creates/updates notes via the
VaultNoteMaterializer, rebuilds wikilinks, conditionally synthesizes MOCs,
and notifies the user.

Uses ``dynamic=True`` with ``.submit()`` for per-chunk/per-concept fan-out,
giving each step independent caching, retry, and artifact lineage.
"""

from zenml import pipeline

from steps.knowledge_ingest.acquire import acquire
from steps.knowledge_ingest.chunk import chunk
from steps.knowledge_ingest.extract import extract_concepts
from steps.knowledge_ingest.cross_reference import cross_reference
from steps.knowledge_ingest.route import create_note, update_note
from steps.knowledge_ingest.rebuild_links import rebuild_links
from steps.knowledge_ingest.synthesis import check_synthesis, synthesize_topic
from steps.knowledge_ingest.notify import notify
from src.shared.schemas import ContentChunk, IngestionSummary, SynthesisCheck


@pipeline(name="knowledge_ingest", dynamic=True, enable_cache=False)
def knowledge_ingest_pipeline(
    content: str = "",
    content_type: str = "text",
    source_title: str = "",
    synthesis_threshold: int = 5,
) -> None:
    """Ingest knowledge from any source into the Obsidian vault."""
    # Step 1: Acquire raw content
    raw = acquire(content=content, content_type=content_type, source_title=source_title)

    # Step 2: Chunk the content
    chunks_output = chunk(raw=raw)

    # Step 3: Extract concepts — fan-out per chunk
    chunks_data = chunks_output.load()
    if not chunks_data:
        return

    extract_futures = []
    for chunk_data in chunks_data:
        chunk_obj = ContentChunk.model_validate(chunk_data)
        future = extract_concepts.submit(
            chunk=chunk_obj, id=f"extract_{chunk_obj.chunk_index}"
        )
        extract_futures.append(future)

    # Step 4+5: Cross-reference + route — fan-out per concept
    raw_data = raw.load()
    source_url = raw_data.get("source_url", "")
    source_title_resolved = raw_data.get("source_title", source_title)

    created_futures = []
    updated_futures = []
    skipped = 0

    for i, extract_future in enumerate(extract_futures):
        concepts = extract_future.load()
        for j, concept in enumerate(concepts):
            xref_future = cross_reference.submit(
                concept=concept, id=f"xref_{i}_{j}"
            )
            xref_result = xref_future.load()

            if xref_result.action == "create":
                note_future = create_note.submit(
                    xref=xref_result,
                    source_url=source_url,
                    source_title=source_title_resolved,
                    id=f"create_{i}_{j}",
                )
                created_futures.append(note_future)
            elif xref_result.action == "update":
                note_future = update_note.submit(
                    xref=xref_result, id=f"update_{i}_{j}"
                )
                updated_futures.append(note_future)
            else:
                skipped += 1

    # Materialize all notes
    created_notes = [f.load() for f in created_futures]
    updated_notes = [f.load() for f in updated_futures]

    # Step 6: Rebuild links
    rebuild_links(created_notes=created_notes, updated_notes=updated_notes)

    # Step 7: Check synthesis
    checks_output = check_synthesis(created_notes=created_notes, threshold=synthesis_threshold)
    checks_data = checks_output.load()

    # Step 8: Synthesize (conditional fan-out)
    syntheses = []
    for check_data in checks_data:
        check_item = SynthesisCheck.model_validate(check_data)
        if check_item.should_synthesize:
            synth_future = synthesize_topic.submit(
                topic=check_item.topic,
                note_titles=check_item.note_titles,
                id=f"synth_{check_item.topic}",
            )
            syntheses.append(synth_future.load().title)

    # Step 9: Notify
    summary = IngestionSummary(
        source_title=source_title_resolved,
        source_type=content_type,
        chunks_processed=len(chunks_data),
        concepts_extracted=len(created_notes) + len(updated_notes) + skipped,
        notes_created=[n.title for n in created_notes],
        notes_updated=[n.title for n in updated_notes],
        notes_skipped=skipped,
        syntheses_created=syntheses,
        links_added=0,
        errors=[],
    )
    notify(summary=summary)
