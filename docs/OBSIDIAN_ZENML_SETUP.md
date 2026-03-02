# Obsidian + Knowledge Ingestion Setup Guide

End-to-end setup for the Obsidian vault integration and Knowledge Ingestion pipeline in NanoClaw.

## Prerequisites

- NanoClaw already running (WhatsApp connected, main group registered)
- Docker or Apple Container runtime
- Python 3.12+ (for pipelines)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [ZenML Cloud](https://cloud.zenml.io) account with a service account API key
- Obsidian app (desktop or mobile) — optional but recommended for browsing the vault

---

## 1. Environment Variables

Add these to your `.env` file in the NanoClaw project root:

```bash
# --- ZenML Cloud (required) ---
ZENML_STORE_URL=https://your-tenant.cloudinfra.zenml.io
ZENML_STORE_API_KEY=your-zenml-service-account-api-key

# --- Anthropic (required for PydanticAI concept extraction) ---
ANTHROPIC_API_KEY=your-anthropic-api-key

# --- E2B (required for PDF processing) ---
E2B_API_KEY=your-e2b-api-key

# --- Vault configuration ---
VAULT_ROOT=~/obsidian-vault      # Local fallback for dev/testing
VAULT_PREFIX=vault               # Prefix within artifact store for vault files
```

The TypeScript host reads `ZENML_STORE_URL` and `ZENML_STORE_API_KEY` from `process.env`. The Python pipelines read all of the above.

**No AWS credentials needed** — ZenML handles S3 auth through its service connectors.

---

## 2. Vault Storage

### 2.1 Where notes live

The pipeline writes vault notes as markdown files to a `vault/` prefix inside the ZenML artifact store (typically an S3 bucket). No local vault or Obsidian installation is required for the pipeline to work.

```
S3 bucket (e.g., s3://nanoclaw-data/)
├── vault/                          ← Vault markdown files
│   ├── 00-Inbox/captures/
│   ├── 01-Knowledge/concepts/      ← Extracted concepts, facts
│   ├── 01-Knowledge/decisions/     ← Decision records
│   ├── 01-Knowledge/people/        ← People notes
│   ├── 02-Projects/
│   ├── 03-Resources/articles/      ← Article summaries
│   ├── 04-MOCs/                    ← Maps of Content, syntheses
│   └── 05-Templates/
└── <zenml-managed>/                ← ZenML artifacts, logs, metadata
```

### 2.2 Local-only mode (dev/testing)

When no S3 artifact store is configured, the pipeline falls back to writing directly to `VAULT_ROOT` on the local filesystem:

```bash
VAULT_ROOT=~/obsidian-vault
```

### 2.3 Optional: Browse notes in Obsidian

This is entirely optional. If you want to read/edit vault notes locally in Obsidian:

**Option A — Local-only mode:** Point Obsidian at your `VAULT_ROOT` directory. Notes appear immediately.

**Option B — S3 mode with local sync:** Use the [Remotely Save](https://github.com/remotely-save/remotely-save) Obsidian community plugin to sync the S3 `vault/` prefix to a local folder:

1. Install Remotely Save in Obsidian
2. Configure it with your S3 bucket and `vault/` prefix
3. Set a sync interval (e.g., every 5 minutes)
4. Point Obsidian at the synced local folder

The pipeline doesn't depend on Obsidian or local sync in either mode — it reads and writes through ZenML's artifact store abstraction.

### 2.4 How the pipeline uses the vault

The Knowledge Ingestion pipeline interacts with the vault through `obsidian_io.py`:
- **Writes** go through ZenML's artifact store filesystem abstraction (`store.open()`)
- **Reads** for cross-referencing use the same abstraction
- Every note has YAML frontmatter: `title`, `type`, `status`, `confidence`, `tags`, `wikilinks`, `zenml_run_id`
- Notes are written atomically (locally) or via S3 PutObject (remote)

---

## 3. Knowledge Ingestion Pipeline

### 3.1 Install Python dependencies

```bash
cd pipelines
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"
```

Key dependencies:
- `zenml` — pipeline orchestration
- `pydantic-ai[anthropic]` — structured AI output for concept extraction
- `python-frontmatter` — markdown frontmatter parsing
- `readability-lxml` — article text extraction from HTML
- `python-slugify` — URL-safe slug generation
- `e2b-code-interpreter` — PDF processing in sandbox
- `httpx` — HTTP requests

### 3.2 Connect to ZenML Cloud

```bash
zenml login --api-key "$ZENML_STORE_API_KEY" "$ZENML_STORE_URL"
```

Verify:

```bash
zenml status
# Should show: Connected to your ZenML server
```

### 3.3 Initialize the project

```bash
cd pipelines
zenml init
```

This sets the source root so imports work correctly in remote containers.

### 3.4 Run the pipeline locally (CLI)

```bash
cd pipelines

# Ingest a URL
python run.py --content "https://example.com/interesting-article" --content-type url

# Ingest raw text
python run.py --content "Key insight: distributed systems need idempotent operations" --content-type text --source-title "Architecture notes"

# Ingest a conversation transcript
python run.py --content "Alice: We should use event sourcing. Bob: Agreed, let's prototype it." --content-type conversation --source-title "Architecture meeting"

# With caching disabled
python run.py --content "..." --content-type text --no-cache

# Custom synthesis threshold (default: 5 notes per tag)
python run.py --content "..." --content-type text --synthesis-threshold 3
```

CLI arguments:

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--content` | Yes | — | URL, base64 PDF, or raw text |
| `--content-type` | No | `text` | `url`, `pdf_b64`, `text`, or `conversation` |
| `--source-title` | No | `""` | Human-readable source title (auto-detected for URLs) |
| `--synthesis-threshold` | No | `5` | Min notes per tag to trigger MOC synthesis |
| `--config` | No | `configs/dev.yaml` | Config file path |
| `--no-cache` | No | `false` | Disable ZenML step caching |

### 3.5 Pipeline flow

```
Content (URL/PDF/text)
       │
       ▼
   ┌─────────┐
   │ Acquire  │  Fetch URL, extract text, process PDF, or passthrough
   └────┬─────┘
        ▼
   ┌─────────┐
   │  Chunk   │  Split on markdown headers, merge small sections
   └────┬─────┘
        ▼
   ┌────────────────────┐
   │ Extract Concepts   │  PydanticAI extracts atomic concepts per chunk
   │ (fan-out per chunk)│
   └────────┬───────────┘
            ▼
   ┌─────────────────┐
   │ Cross-Reference  │  Jaccard similarity on vault + artifact store dedup
   └────────┬────────┘
            ▼
   ┌────────────────┐
   │ Route: Create  │  New VaultNote → materializer dual-writes JSON + markdown
   │   or Update    │  Existing note → PydanticAI merges new info
   └────────┬───────┘
            ▼
   ┌─────────────────┐
   │ Rebuild Links   │  Add [[wikilinks]] across vault, update MOC pages
   └────────┬────────┘
            ▼
   ┌─────────────────┐
   │ Check Synthesis  │  If a tag has ≥ threshold notes → synthesize MOC
   └────────┬────────┘
            ▼
   ┌──────────┐
   │  Notify  │  Format summary → ZenML metadata → host polls → WhatsApp
   └──────────┘
```

### 3.6 What gets created in the vault

| Note type | Vault folder | Example |
|-----------|-------------|---------|
| Concept | `01-Knowledge/concepts/` | `event-sourcing.md` |
| Fact | `01-Knowledge/concepts/` | `cap-theorem.md` |
| Decision | `01-Knowledge/decisions/` | `use-event-sourcing.md` |
| Person | `01-Knowledge/people/` | `alice-smith.md` |
| Article summary | `03-Resources/articles/` | `scaling-microservices.md` |
| MOC (synthesis) | `04-MOCs/` | `moc-distributed-systems.md` |

Every note has:
- YAML frontmatter: `title`, `type`, `status` (seedling/developing/evergreen), `confidence` (verified/high/medium/speculative), `tags`, `wikilinks`, `source_url`, `zenml_run_id`
- Markdown body content
- `[[wikilinks]]` to related notes

### 3.7 Register the pipeline with ZenML Cloud

Run the pipeline once to register it:

```bash
cd pipelines
python run.py --content "test content" --content-type text --source-title "Test"
```

After this, the pipeline can be triggered remotely via WhatsApp.

### 3.8 Verify pipeline runs

```bash
zenml pipeline runs list
zenml pipeline runs describe <run-id>
```

Or in the ZenML Cloud dashboard at your `ZENML_STORE_URL`.

---

## 4. NanoClaw Host Integration

### 4.1 Rebuild NanoClaw

```bash
npm run build
```

This compiles:
- `src/integrations/zenml-client.ts` — ZenML Cloud REST client (with `getRunMetadata()`)
- `src/ipc.ts` — pipeline trigger handler + notification polling (30s interval)

### 4.2 Rebuild the container

```bash
./container/build.sh
```

This picks up:
- `ingest_knowledge` MCP tool in `container/agent-runner/src/ipc-mcp-stdio.ts`
- Existing ZenML pipeline tools (`trigger_zenml_pipeline`, `check_pipeline_status`, `list_pipelines`)
- Knowledge ingestion skill at `.claude/skills/knowledge-ingest/SKILL.md`

### 4.3 Restart NanoClaw

```bash
# macOS
launchctl kickstart -k gui/$(id -u)/com.nanoclaw

# Linux
systemctl --user restart nanoclaw

# Dev mode
npm run dev
```

---

## 5. Using Knowledge Ingestion

### 5.1 Via WhatsApp (recommended)

Send a message to the agent with content to ingest:

```
@Andy save this article: https://martinfowler.com/articles/microservices.html

@Andy ingest this: "Key architectural decision: we'll use CQRS with event sourcing
for the order service. This separates read and write models, allowing independent
scaling. Trade-off: eventual consistency requires careful handling of read-after-write."

@Andy here's the meeting transcript, please save the key points:
Alice: We should use Kafka for event streaming.
Bob: What about RabbitMQ?
Alice: Kafka has better throughput for our scale.
Decision: Go with Kafka.
```

The agent uses the `ingest_knowledge` MCP tool, which triggers the pipeline via IPC. You'll receive a WhatsApp notification when processing completes:

```
Knowledge ingested: *Microservices Architecture*  (url)
5 concepts extracted | 4 notes created | 1 note updated | 0 duplicates skipped

New notes:
  - Microservices
  - Service mesh
  - API gateway
  - Domain-driven design
```

### 5.2 Via CLI (direct)

```bash
cd pipelines
python run.py --content "https://example.com/article" --content-type url
```

### 5.3 Via generic pipeline trigger

```
@Andy trigger the knowledge_ingest pipeline with content="https://example.com" content_type="url"
```

---

## 6. Architecture Reference

### Data Flow

```
WhatsApp → NanoClaw Host → Container Agent → ingest_knowledge MCP tool
                │                                     │
                │  trigger_zenml_pipeline IPC          │
                ▼                                     │
         ZenML REST Client ──── ZenML Cloud           │
                                    │                 │
                                    ▼                 │
                           Knowledge Ingest Pipeline  │
                              │         │             │
                              ▼         ▼             ▼
                         S3 Vault   ZenML Artifacts  Direct vault writes
                              │
                              ▼
                    Obsidian (Remotely Save sync)
```

### Notification Flow

```
Pipeline notify step → log_metadata(notification_text)
                              │
NanoClaw host (30s poll) ─────┘
         │
         ▼
    getPipelineRun() → read metadata → sendMessage(chatJid, text)
```

### File Map

| Component | Key Files |
|-----------|-----------|
| Pipeline definition | `pipelines/pipelines/knowledge_ingest.py` |
| Pipeline steps | `pipelines/steps/knowledge_ingest/*.py` (8 steps) |
| Type system | `pipelines/src/shared/schemas.py` |
| Vault I/O (S3) | `pipelines/src/shared/obsidian_io.py` |
| Materializer | `pipelines/src/shared/materializers.py` |
| Notifications | `pipelines/src/shared/notify.py` |
| Config | `pipelines/src/shared/config.py` |
| CLI runner | `pipelines/run.py` |
| Pipeline config | `pipelines/configs/dev.yaml` |
| MCP tools | `container/agent-runner/src/ipc-mcp-stdio.ts` |
| Host IPC + polling | `src/ipc.ts` |
| ZenML TS client | `src/integrations/zenml-client.ts` |
| Agent skill | `.claude/skills/knowledge-ingest/SKILL.md` |
| Agent memory | `groups/main/CLAUDE.md` |

---

## 7. Troubleshooting

### ZenML login fails

```
ZenML login failed (401): ...
```

- Verify `ZENML_STORE_API_KEY` is a valid service account API key (not a user password)
- Verify `ZENML_STORE_URL` has no trailing slash
- Test: `curl -X POST "$ZENML_STORE_URL/api/v1/login" -d "password=$ZENML_STORE_API_KEY"`

### Pipeline not found when triggering via WhatsApp

```
Pipeline "knowledge_ingest" not found
```

The pipeline must be registered in ZenML Cloud first. Run it once locally:

```bash
cd pipelines && python run.py --content "test" --content-type text
```

This registers the pipeline and creates a snapshot that NanoClaw can trigger.

### URL extraction fails

If `readability-lxml` can't extract content from a URL:
- The site may block automated requests — try with a different URL
- Some SPAs don't render content in the initial HTML response
- PDFs served from URLs are auto-detected and routed through E2B sandbox

### No notification received after pipeline completes

1. Check if the pipeline actually completed: `zenml pipeline runs list`
2. Verify the notification polling is running — look for `Pipeline run completed, notification sent` in NanoClaw logs
3. Ensure the `chatJid` was set in the IPC file (check `data/ipc/errors/` for failed files)
4. Pipeline runs time out after 1 hour — check if the run took too long

### Cross-referencing creates duplicates

The cross-reference step uses Jaccard word similarity (threshold 0.5) on note titles/filenames. If concepts have very different names but cover the same topic, they'll be created as separate notes. The synthesis step will eventually group them via shared tags.

### Vault notes not syncing to Obsidian

- Verify Remotely Save plugin is configured with the correct S3 bucket and `vault/` prefix
- Check the plugin's sync log for errors
- For local-only mode, ensure `VAULT_ROOT` points to your Obsidian vault directory

### MCP tools not available in container

If the agent can't use `ingest_knowledge`:
1. Verify the container was rebuilt after changes: `./container/build.sh`
2. Check MCP server starts: look for `MCP server connected` in container stderr
3. Ensure `NANOCLAW_IS_MAIN=1` (only the main group can use ingestion tools)
4. Check available tools: agent should see `ingest_knowledge` in its tool list

### E2B sandbox fails for PDF

- Verify `E2B_API_KEY` is set and valid
- E2B sandbox needs internet access to install PyMuPDF
- For large PDFs (>50 pages), the sandbox may time out — try splitting the PDF first
