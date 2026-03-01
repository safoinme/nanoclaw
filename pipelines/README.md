# NanoClaw Pipelines

ZenML pipelines for Obsidian vault automation, personal CRM, and content monitoring. Connects to [ZenML Cloud](https://cloud.zenml.io) for orchestration and tracking.

## Install

```bash
cd pipelines
uv pip install -e ".[dev]"
zenml init
```

If `uv` is unavailable: `pip install -e ".[dev]"`

## Configuration

Set required environment variables:

```bash
export ZENML_STORE_URL="https://11870fb5-zenml.cloudinfra.zenml.io"
export ZENML_STORE_API_KEY="your-api-key"
export VAULT_ROOT="$HOME/obsidian-vault"
export ANTHROPIC_API_KEY="your-key"

# Optional (for specific pipelines):
export E2B_API_KEY="..."
```

Store sensitive credentials in the ZenML secret store:

```bash
zenml secret create github_token --token=ghp_...
zenml secret create gmail_credentials --access_token=...
zenml secret create google_calendar_credentials --access_token=...
zenml secret create slack_credentials --bot_token=xoxb-... --channels=C01,C02
zenml secret create discord_credentials --bot_token=... --channels=123,456
```

## Run

```bash
python run.py --pipeline <name> --config configs/dev.yaml
python run.py --pipeline <name> --no-cache
python run.py --pipeline <name> --schedule     # Deploy with recurring schedule
python run.py --pipeline document_processor --file-path /path/to/file.pdf
```

Assumes a configured ZenML stack. See [ZenML docs](https://docs.zenml.io) for stack setup.

## Quick Start: Minimal Test

You only need **two secrets** to run a useful subset of pipelines. Sources without configured secrets (Gmail, Slack, Discord) gracefully return empty results — the pipeline still completes.

### 1. GitHub token

Create a [personal access token](https://github.com/settings/tokens) with `repo` and `notifications` scopes:

```bash
zenml secret create github_token --token=ghp_yourTokenHere
```

### 2. Google Calendar credentials

Create OAuth credentials in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials), enable the Calendar API, and complete the OAuth flow to get an access token:

```bash
zenml secret create google_calendar_credentials \
  --access_token=ya29.yourAccessToken \
  --refresh_token=1//yourRefreshToken \
  --client_id=yourClientId.apps.googleusercontent.com \
  --client_secret=yourClientSecret
```

### 3. Run the morning briefing

```bash
python run.py --pipeline morning_briefing --config configs/dev.yaml
```

The briefing will include GitHub notifications and calendar events. Gmail, Slack, and Discord sections will be empty but the pipeline succeeds. Content Monitor and Inbox Processor work with no secrets at all.

### What each pipeline needs

| Pipeline | Required secrets | Works without secrets? |
|----------|-----------------|----------------------|
| Content Monitor | None | Yes (RSS feeds only) |
| Inbox Processor | None | Yes (scans local vault) |
| Morning Briefing | `github_token`, `google_calendar_credentials` | Partially (other sources return empty) |
| Personal CRM | None | Yes (reads vault conversations) |
| Weekly Review | None | Yes (reads vault data) |
| Document Processor | `E2B_API_KEY` env var | No |

## Pipelines

All pipelines use `@pipeline(dynamic=True)` for runtime branching, `.map()` fan-out, and `.submit()` parallelism.

### 1. Inbox Processor

Scan inbox, classify notes with AI, move to permanent vault locations.

**Schedule:** Daily at midnight (`0 0 * * *`)

```
scan_inbox --> [if notes] --> classify_notes --> move_notes
```

### 2. Morning Briefing

Parameterized fan-out data collection via `.map()`, AI summary, vault archive + notification.

**Schedule:** Weekdays at 7 AM (`0 7 * * 1-5`)

```
get_source_configs --> fetch_source.map(sources) --> summarize --> deliver
```

### 3. Personal CRM

Load conversations, extract people and commitments with AI, create/update people notes, flag overdue follow-ups.

**Schedule:** Nightly at 11 PM (`0 23 * * *`)

```
load_conversations --> extract_people --> update_notes
```

### 4. Document Processor

Receive a file, process it in an E2B sandbox (PDF, CSV, XLSX, text), summarize with AI, save to vault.

**Trigger:** On-demand via snapshot

```
process --> summarize
```

### 5. Weekly Review

Gather vault changes, commitments, and orphans in one step; compile review with AI.

**Schedule:** Sundays at 10 AM (`0 10 * * 0`)

```
gather_data --> compile_review
```

### 6. Content Monitor

Load RSS feeds, fetch latest items, summarize with AI, archive digests to vault.

**Schedule:** Every 6 hours (`0 */6 * * *`)

```
load_feeds --> [if feeds] --> summarize_feeds
```

## Notifications

Pipelines store notification text in ZenML step metadata via `log_notification()`. The NanoClaw host process reads this after pipeline completion and delivers via WhatsApp (Baileys).

## Project Structure

```
pipelines/
├── pyproject.toml
├── run.py
├── configs/
│   └── dev.yaml
├── src/
│   └── shared/
│       ├── config.py           # Vault paths, ZenML Cloud settings
│       ├── schemas.py          # Pydantic models (data + PydanticAI results)
│       ├── obsidian_io.py      # Vault read/write utilities
│       └── notify.py           # ZenML metadata-based notifications
├── steps/
│   ├── inbox_processor/
│   │   ├── scan_inbox.py
│   │   ├── classify_notes.py
│   │   └── move_notes.py
│   ├── morning_briefing/
│   │   ├── fetch_source.py     # Single parameterized step (replaces 6 fetch files)
│   │   ├── summarize.py
│   │   └── deliver.py
│   ├── personal_crm/
│   │   ├── load_conversations.py
│   │   ├── extract_people.py
│   │   └── update_notes.py
│   ├── document_processor/
│   │   ├── process.py          # E2B sandbox (absorbs receive_document)
│   │   └── summarize.py
│   ├── weekly_review/
│   │   ├── gather_data.py      # Combined: scan + commitments + orphans
│   │   └── compile_review.py
│   └── content_monitor/
│       ├── load_feeds.py
│       └── summarize_feeds.py
└── pipelines/
    ├── inbox_processor.py
    ├── morning_briefing.py
    ├── personal_crm.py
    ├── document_processor.py
    ├── weekly_review.py
    └── content_monitor.py
```
