---
name: zenml-trigger
description: Trigger ZenML pipelines and check their status. Use when the user wants to run a pipeline, ingest knowledge, save/remember content, process inbox, generate a briefing, update CRM, process documents, run weekly review, or monitor content. Triggers on "run pipeline", "trigger pipeline", "process inbox", "morning briefing", "weekly review", "check pipeline", "save this", "remember this", "ingest this", "add to vault", or when a user shares a URL/document worth keeping.
---

# ZenML Pipeline Trigger Skill

Trigger ZenML pipelines via MCP tools and check their status. All automation in NanoClaw runs as ZenML pipelines — use `trigger_zenml_pipeline` to start them and `check_pipeline_status` to monitor them.

## Triggering a Pipeline

Use the `trigger_zenml_pipeline` MCP tool:

```
trigger_zenml_pipeline(
  pipeline_name: string,   # One of the pipeline names below
  parameters: object       # Pipeline-specific parameters
)
```

After triggering, report the run ID to the user. Check status with `check_pipeline_status` if asked.

## Checking Pipeline Status

```
check_pipeline_status(
  pipeline_name: string,    # Optional — omit to check all
  run_id: string            # Optional — check a specific run
)
```

Returns: run status (`running`, `completed`, `failed`), start time, duration, and output artifacts.

---

## Available Pipelines

| Pipeline | Description | When to trigger |
|---|---|---|
| `knowledge_ingest` | Ingest URLs, PDFs, text into Obsidian vault as atomic notes | User shares content to save, says "remember/save/ingest this" |
| `inbox_processor` | Process and organize Obsidian inbox captures | When inbox has unprocessed notes |
| `morning_briefing` | Generate daily briefing note | Morning, or on request |
| `personal_crm` | Update people notes and relationship tracking | When new interaction data exists |
| `document_processor` | Process and summarize documents | When new documents are added |
| `weekly_review` | Generate weekly review and planning note | End of week, or on request |
| `content_monitor` | Monitor web content for changes | Periodically, or on request |

---

## knowledge_ingest (detailed)

The most commonly triggered pipeline. Ingests any content into the Obsidian vault as atomic, cross-linked notes.

### When to Trigger

- User shares a URL to an article, blog post, docs, or any web content
- User sends a PDF document
- User shares text, notes, or ideas they want to preserve long-term
- User shares a conversation transcript worth keeping
- User says "save this", "remember this", "add to vault", or "ingest this"

### When NOT to Trigger

- Simple questions that don't need saving
- Temporary content (weather, current time, quick calculations)
- Commands or instructions directed at you
- Content already in the vault

### Parameters

```
trigger_zenml_pipeline(
  pipeline_name="knowledge_ingest",
  parameters={
    "content": "<the content or URL>",
    "content_type": "<url|pdf_b64|text|conversation>",
    "source_title": "Human-readable title",
    "synthesis_threshold": 5
  }
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | string | required | The content to ingest (URL, base64 PDF, or raw text) |
| `content_type` | string | `"text"` | One of: `url`, `pdf_b64`, `text`, `conversation` |
| `source_title` | string | `""` | Human-readable title for the source |
| `synthesis_threshold` | int | `5` | Min notes on a topic before generating a synthesis MOC |

### Content Types

| Type | `content_type` | `content` value |
|------|----------------|-----------------|
| Web URL | `url` | The full URL |
| PDF | `pdf_b64` | Base64-encoded PDF bytes |
| Plain text / notes | `text` | The raw text |
| Conversation | `conversation` | The transcript text |

### What the Pipeline Does

1. **Acquire** — fetch and clean content (URLs are fetched and extracted)
2. **Chunk** — split text into manageable chunks
3. **Extract** — PydanticAI extracts atomic concepts from each chunk (fan-out)
4. **Cross-reference** — each concept is matched against existing vault notes
5. **Route** — new notes are created or existing ones are updated
6. **Rebuild links** — wikilinks are rebuilt across the vault
7. **Synthesize** — if a topic has enough notes, a synthesis MOC is generated
8. **Notify** — summary notification is sent back

After triggering, tell the user ingestion has started and provide the run ID. They'll receive a notification when it completes with a summary of what was created/updated.

---

## Other Pipeline Parameters

**inbox_processor**
```json
{ "source_folder": "00-Inbox/captures", "dry_run": false }
```

**morning_briefing**
```json
{ "date": "2026-03-01", "include_calendar": true, "include_tasks": true }
```

**personal_crm**
```json
{ "sync_source": "all", "update_interactions": true }
```

**document_processor**
```json
{ "input_path": "path/to/document", "output_folder": "03-Resources/articles", "summarize": true }
```

**weekly_review**
```json
{ "week_start": "2026-02-23", "include_metrics": true }
```

**content_monitor**
```json
{ "urls": ["https://example.com"], "check_type": "content_change" }
```
