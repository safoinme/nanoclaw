"""Pydantic models for pipeline data.

All models use Pydantic BaseModel which has a built-in ZenML materializer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# --- Inbox Processor ---


class NoteCategory(str, Enum):
    """Categories for inbox note classification."""

    REFERENCE = "reference"
    PROJECT = "project"
    TASK = "task"
    IDEA = "idea"
    MEETING = "meeting"
    PERSON = "person"
    RESOURCE = "resource"


class ClassifiedNote(BaseModel):
    """A note that has been classified and enriched."""

    source_path: str
    title: str
    category: NoteCategory
    tags: list[str] = Field(default_factory=list)
    destination_folder: str
    summary: str = ""
    wikilinks: list[str] = Field(default_factory=list)


# --- Morning Briefing ---


class ContentItem(BaseModel):
    """A single item from any data source (GitHub, Gmail, etc.)."""

    source: str
    title: str
    body: str = ""
    url: str = ""
    timestamp: datetime | None = None
    priority: str = "normal"


class PersonMention(BaseModel):
    """A person mentioned in the briefing context."""

    name: str
    context: str
    source: str


class AnalysisSummary(BaseModel):
    """AI-generated analysis of collected data."""

    key_highlights: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    people_mentions: list[PersonMention] = Field(default_factory=list)
    calendar_conflicts: list[str] = Field(default_factory=list)


class MorningBriefing(BaseModel):
    """Complete morning briefing ready for delivery."""

    date: str
    summary: str
    analysis: AnalysisSummary
    items_by_source: dict[str, list[ContentItem]] = Field(default_factory=dict)
    whatsapp_message: str = ""
    vault_note_path: str = ""


# --- Personal CRM ---


class Commitment(BaseModel):
    """A commitment or follow-up extracted from conversations."""

    person: str
    description: str
    due_date: str | None = None
    source: str = ""
    status: str = "open"


class PersonRecord(BaseModel):
    """CRM record for a person."""

    name: str
    last_contact: str | None = None
    commitments: list[Commitment] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    vault_note_path: str = ""


# --- Document Processor ---


class ProcessedDocument(BaseModel):
    """Result of processing a document in E2B sandbox."""

    original_path: str
    file_type: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    vault_note_path: str = ""


# --- Weekly Review ---


class WeeklyReviewReport(BaseModel):
    """Compiled weekly review."""

    week_start: str
    week_end: str
    notes_created: int = 0
    notes_modified: int = 0
    commitments_due: list[Commitment] = Field(default_factory=list)
    commitments_overdue: list[Commitment] = Field(default_factory=list)
    orphan_notes: list[str] = Field(default_factory=list)
    suggested_connections: list[str] = Field(default_factory=list)
    summary: str = ""


# --- Content Monitor ---


class FeedItem(BaseModel):
    """A single RSS feed item."""

    feed_name: str
    title: str
    url: str
    published: str = ""
    summary: str = ""


class VaultNote(BaseModel):
    """Generic vault note representation."""

    path: str
    title: str
    content: str
    frontmatter: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """Generic result wrapper for any pipeline run."""

    pipeline_name: str
    success: bool = True
    items_processed: int = 0
    notes_created: list[str] = Field(default_factory=list)
    notes_updated: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    message: str = ""
