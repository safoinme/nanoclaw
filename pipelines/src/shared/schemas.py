"""Pydantic models for the Knowledge Ingestion & Synthesis Pipeline.

All models use Pydantic BaseModel which has a built-in ZenML materializer.
Models suffixed with Result/Check/Summary are used as PydanticAI result_type.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class NoteType(str, Enum):
    """Types of vault notes."""

    CONCEPT = "concept"
    FACT = "fact"
    DECISION = "decision"
    PERSON = "person"
    ARTICLE_SUMMARY = "article_summary"
    MOC = "moc"
    SYNTHESIS = "synthesis"


class NoteStatus(str, Enum):
    """Maturity status of a vault note."""

    SEEDLING = "seedling"
    DEVELOPING = "developing"
    EVERGREEN = "evergreen"


class ConceptConfidence(str, Enum):
    """Confidence level for extracted concepts."""

    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    SPECULATIVE = "speculative"


class ContentChunk(BaseModel):
    """A chunk of content ready for concept extraction."""

    text: str
    chunk_index: int
    source_section: str = ""
    word_count: int = 0


class ExtractedConcept(BaseModel):
    """A concept extracted from a content chunk by PydanticAI."""

    title: str = Field(description="Human-readable concept title")
    slug: str = Field(description="URL-safe slug for the note filename")
    note_type: NoteType = Field(description="Type of note to create")
    summary: str = Field(description="1-3 sentence summary of the concept")
    body: str = Field(default="", description="Full markdown body content")
    tags: list[str] = Field(default_factory=list, description="Relevant tags")
    confidence: ConceptConfidence = Field(default=ConceptConfidence.HIGH)
    source_chunk_index: int = Field(default=0, description="Which chunk this was extracted from")


class CrossRefResult(BaseModel):
    """Result of cross-referencing a concept against the existing vault."""

    concept: ExtractedConcept
    action: str = Field(description="'create', 'update', or 'skip'")
    existing_note_key: str | None = Field(
        default=None,
        description="S3 key of existing note if action is 'update'",
    )
    similarity_score: float = Field(default=0.0)
    match_source: str = Field(default="", description="How the match was found")


class VaultNote(BaseModel):
    """A vault note ready for materialization."""

    title: str
    slug: str
    note_type: NoteType
    folder: str = Field(description="Target vault folder (e.g. '01-Knowledge/concepts')")
    content: str = Field(description="Markdown body content")
    tags: list[str] = Field(default_factory=list)
    wikilinks: list[str] = Field(default_factory=list)
    status: NoteStatus = Field(default=NoteStatus.SEEDLING)
    confidence: ConceptConfidence = Field(default=ConceptConfidence.HIGH)
    source_url: str = ""
    source_title: str = ""
    zenml_run_id: str = ""


class SynthesisCheck(BaseModel):
    """Result of checking whether a topic has enough notes for synthesis."""

    topic: str
    note_count: int
    note_titles: list[str] = Field(default_factory=list)
    should_synthesize: bool = False


class IngestionSummary(BaseModel):
    """Summary of a complete knowledge ingestion run."""

    source_title: str = ""
    source_type: str = ""
    chunks_processed: int = 0
    concepts_extracted: int = 0
    notes_created: list[str] = Field(default_factory=list)
    notes_updated: list[str] = Field(default_factory=list)
    notes_skipped: int = 0
    syntheses_created: list[str] = Field(default_factory=list)
    links_added: int = 0
    errors: list[str] = Field(default_factory=list)
