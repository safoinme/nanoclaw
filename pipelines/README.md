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
export WHATSAPP_PHONE_ID="..."
export WHATSAPP_TOKEN="..."
export WHATSAPP_RECIPIENT="..."
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

## Pipelines

### 1. Inbox Processor

Scan inbox, classify notes with AI, move to permanent vault locations, update MOCs.

**Schedule:** Daily at midnight (`0 0 * * *`)

```
scan_inbox --> classify_notes --> move_notes
```

### 2. Morning Briefing

Fan-out data collection from GitHub, Gmail, Calendar, Slack, Discord, and ZenML. Fan-in aggregation, AI summary, WhatsApp notification, vault archive.

**Schedule:** Weekdays at 7 AM (`0 7 * * 1-5`)

```
fetch_github  ─┐
fetch_gmail   ─┤
fetch_calendar─┤
fetch_slack   ─┼─> aggregate_briefing --> summarize_briefing --> deliver_briefing
fetch_discord ─┤
fetch_zenml   ─┘
```

### 3. Personal CRM

Load conversations, extract people and commitments with AI, create/update people notes, flag overdue follow-ups.

**Schedule:** Nightly at 11 PM (`0 23 * * *`)

```
load_conversations --> extract_people --> update_people_notes
```

### 4. Document Processor

Receive a file, process it in an E2B sandbox (PDF, CSV, XLSX, text), summarize with AI, save to vault.

**Trigger:** On-demand via snapshot

```
receive_document --> process_in_sandbox --> summarize_document
```

### 5. Weekly Review

Scan vault changes for the past week, check commitments, detect orphan notes, find connections, compile review with AI.

**Schedule:** Sundays at 10 AM (`0 10 * * 0`)

```
scan_vault_changes ─┐
check_commitments  ─┼─> compile_weekly_review
detect_orphans     ─┘
```

### 6. Content Monitor

Load RSS feeds, fetch latest items, summarize with AI, archive digests to vault.

**Schedule:** Every 6 hours (`0 */6 * * *`)

```
load_feeds --> summarize_feeds
```

## Project Structure

```
pipelines/
├── pyproject.toml          # Dependencies
├── run.py                  # CLI entry point (argparse)
├── configs/
│   └── dev.yaml            # Development config
├── src/
│   └── shared/
│       ├── config.py       # ZenML Cloud settings, vault paths
│       ├── schemas.py      # Pydantic models (built-in materializer)
│       ├── obsidian_io.py  # Vault read/write utilities
│       └── whatsapp_notify.py  # WhatsApp Cloud API sender
├── steps/                  # One step per file
│   ├── scan_inbox.py
│   ├── classify_notes.py
│   ├── move_notes.py
│   ├── fetch_github.py
│   ├── fetch_gmail.py
│   ├── fetch_calendar.py
│   ├── fetch_slack.py
│   ├── fetch_discord.py
│   ├── fetch_zenml_status.py
│   ├── aggregate_briefing.py
│   ├── summarize_briefing.py
│   ├── deliver_briefing.py
│   ├── load_conversations.py
│   ├── extract_people.py
│   ├── update_people_notes.py
│   ├── receive_document.py
│   ├── process_in_sandbox.py
│   ├── summarize_document.py
│   ├── scan_vault_changes.py
│   ├── check_commitments.py
│   ├── detect_orphans.py
│   ├── compile_weekly_review.py
│   ├── load_feeds.py
│   └── summarize_feeds.py
└── pipelines/              # Pipeline definitions
    ├── inbox_processor.py
    ├── morning_briefing.py
    ├── personal_crm.py
    ├── document_processor.py
    ├── weekly_review.py
    └── content_monitor.py
```
