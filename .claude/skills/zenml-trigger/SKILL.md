---
name: zenml-trigger
description: Trigger ZenML pipelines and check their status. Use when the user wants to run a pipeline, process inbox, generate a briefing, update CRM, process documents, run weekly review, or monitor content. Triggers on "run pipeline", "trigger pipeline", "process inbox", "morning briefing", "weekly review", "check pipeline".
---

# ZenML Pipeline Trigger Skill

Trigger ZenML pipelines via MCP tools and check their status.

## Available Pipelines

| Pipeline | Description | When to trigger |
|---|---|---|
| `inbox_processor` | Process and organize Obsidian inbox captures | When inbox has unprocessed notes |
| `morning_briefing` | Generate daily briefing note | Morning, or on request |
| `personal_crm` | Update people notes and relationship tracking | When new interaction data exists |
| `document_processor` | Process and summarize documents | When new documents are added |
| `weekly_review` | Generate weekly review and planning note | End of week, or on request |
| `content_monitor` | Monitor web content for changes | Periodically, or on request |

## Triggering a Pipeline

Use the `trigger_zenml_pipeline` MCP tool:

```
trigger_zenml_pipeline(
  pipeline_name: string,   # One of the pipeline names above
  parameters: object       # Pipeline-specific parameters (see below)
)
```

### Parameter Schemas

**inbox_processor**
```json
{
  "source_folder": "00-Inbox/captures",
  "dry_run": false
}
```

**morning_briefing**
```json
{
  "date": "2026-03-01",
  "include_calendar": true,
  "include_tasks": true
}
```

**personal_crm**
```json
{
  "sync_source": "all",
  "update_interactions": true
}
```

**document_processor**
```json
{
  "input_path": "path/to/document",
  "output_folder": "03-Resources/articles",
  "summarize": true
}
```

**weekly_review**
```json
{
  "week_start": "2026-02-23",
  "include_metrics": true
}
```

**content_monitor**
```json
{
  "urls": ["https://example.com"],
  "check_type": "content_change"
}
```

## Checking Pipeline Status

Use the `check_pipeline_status` MCP tool:

```
check_pipeline_status(
  pipeline_name: string,    # Optional — omit to check all
  run_id: string            # Optional — check a specific run
)
```

Returns: run status (`running`, `completed`, `failed`), start time, duration, and output artifacts.

## Workflow

1. Identify which pipeline to run based on user request or scheduled trigger
2. Call `trigger_zenml_pipeline` with the correct name and parameters
3. Report the run ID to the user
4. If the user asks, check status with `check_pipeline_status`
5. On completion, summarize results and any output artifacts
