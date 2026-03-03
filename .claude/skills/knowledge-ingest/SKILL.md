---
name: knowledge-ingest
description: Save knowledge to the Obsidian vault via the knowledge_ingest ZenML pipeline. Use when the user shares URLs, PDFs, text, or conversations they want preserved. Triggers on "save this", "remember this", "ingest this", "add to vault", or when a user shares a URL/document worth keeping.
---

# Knowledge Ingestion Skill

Ingest knowledge into the Obsidian vault by triggering the `knowledge_ingest` ZenML pipeline.

## When to Use

Trigger knowledge ingestion when the user:
- Shares a URL to an article, blog post, documentation page, or any web content
- Sends a PDF document
- Shares text, notes, or ideas they want to preserve long-term
- Shares a conversation transcript worth keeping
- Explicitly asks to "save this", "remember this", "add to vault", or "ingest this"

## When NOT to Use

Do NOT ingest when:
- The user asks a simple question that doesn't need to be saved
- The content is temporary (weather, current time, quick calculations)
- The user is giving you commands or instructions
- The content is already in the vault

## How to Trigger

This is a **ZenML pipeline** named `knowledge_ingest`. Trigger it using the `trigger_zenml_pipeline` MCP tool:

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

### Content Types

| Type | `content_type` | `content` value |
|------|----------------|-----------------|
| Web URL | `url` | The full URL |
| PDF | `pdf_b64` | Base64-encoded PDF bytes |
| Plain text / notes | `text` | The raw text |
| Conversation | `conversation` | The transcript text |

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | string | required | The content to ingest (URL, base64 PDF, or raw text) |
| `content_type` | string | `"text"` | One of: `url`, `pdf_b64`, `text`, `conversation` |
| `source_title` | string | `""` | Human-readable title for the source |
| `synthesis_threshold` | int | `5` | Min notes on a topic before generating a synthesis MOC |

## Pipeline Steps

1. **Acquire** — fetch and clean content (URLs are fetched and extracted)
2. **Chunk** — split text into manageable chunks
3. **Extract** — PydanticAI extracts atomic concepts from each chunk (fan-out)
4. **Cross-reference** — each concept is matched against existing vault notes
5. **Route** — new notes are created or existing ones are updated
6. **Rebuild links** — wikilinks are rebuilt across the vault
7. **Synthesize** — if a topic has enough notes, a synthesis MOC is generated
8. **Notify** — summary notification is sent back

## Checking Status

Use `check_pipeline_status` to monitor the run:

```
check_pipeline_status(pipeline_name="knowledge_ingest")
```

## Expected Behavior

After triggering, tell the user ingestion has started and provide the run ID. They'll receive a notification when it completes with a summary of what was created/updated.
