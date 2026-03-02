# NanoClaw Pipelines

ZenML-based Knowledge Ingestion & Synthesis pipeline for the Obsidian vault. Acquires content (URL/PDF/text), extracts atomic concepts via PydanticAI, cross-references the vault, creates/updates notes with wikilinks, and conditionally synthesizes MOC pages.

Connects to [ZenML Cloud](https://cloud.zenml.io) for orchestration and tracking. Vault storage uses the ZenML artifact store's S3 bucket with a `vault/` prefix.

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
export ZENML_STORE_URL="https://your-tenant.cloudinfra.zenml.io"
export ZENML_STORE_API_KEY="your-api-key"
export AI_MODEL="openai:gpt-4o"          # PydanticAI model string (provider:model)
export OPENAI_API_KEY="your-key"         # or ANTHROPIC_API_KEY for anthropic: models
export E2B_API_KEY="your-key"            # Required for PDF processing

# Vault
export VAULT_ROOT="$HOME/obsidian-vault"  # Local fallback for dev/testing
export VAULT_PREFIX="vault"               # Prefix in artifact store (default: "vault")
```

No AWS credentials needed — ZenML handles S3 auth through its service connectors.

## Run

```bash
# Ingest a URL
python run.py --content "https://example.com/article" --content-type url

# Ingest raw text
python run.py --content "Key insight about distributed systems..." --content-type text --source-title "Arch notes"

# Ingest a conversation
python run.py --content "Alice: Let's use Kafka. Bob: Agreed." --content-type conversation

# Base64 PDF
python run.py --content "$(base64 < document.pdf)" --content-type pdf_b64

# Disable caching
python run.py --content "..." --content-type text --no-cache

# Custom synthesis threshold (default: 5)
python run.py --content "..." --content-type text --synthesis-threshold 3

# Custom config
python run.py --content "..." --content-type text --config configs/dev.yaml
```

## Pipeline

Single pipeline: `knowledge_ingest` (on-demand, triggered via WhatsApp or CLI).

```
acquire ──► chunk ──► extract_concepts (per chunk) ──► cross_reference (per concept)
                                                              │
                                          ┌───────────────────┼───────────────────┐
                                          ▼                   ▼                   ▼
                                     create_note         update_note            skip
                                          │                   │
                                          └─────────┬─────────┘
                                                    ▼
                                              rebuild_links
                                                    ▼
                                             check_synthesis
                                                    │
                                          [threshold met?]──► synthesize_topic
                                                    │
                                                    ▼
                                                 notify
```

### Steps

| Step | File | Cache | Description |
|------|------|-------|-------------|
| `acquire` | `acquire.py` | No | Fetch URL (readability-lxml), process PDF (E2B), or passthrough text |
| `chunk` | `chunk.py` | Yes | Split on markdown headers, merge small sections (max 500 words) |
| `extract_concepts` | `extract.py` | Yes | PydanticAI extracts atomic `ExtractedConcept` models |
| `cross_reference` | `cross_reference.py` | No | Jaccard similarity on vault titles + artifact store dedup |
| `create_note` | `route.py` | Yes | Build `VaultNote` from concept, map type → folder |
| `update_note` | `route.py` | No | PydanticAI merges new info into existing note |
| `rebuild_links` | `rebuild_links.py` | No | Back-link `[[wikilinks]]` across vault, update MOC pages |
| `check_synthesis` | `synthesis.py` | No | Group by tag, check if count ≥ threshold |
| `synthesize_topic` | `synthesis.py` | Yes | PydanticAI generates comprehensive MOC |
| `notify` | `notify.py` | No | Format summary → ZenML metadata → host polls → WhatsApp |

### Note Types

| Type | Folder | Example |
|------|--------|---------|
| concept / fact | `01-Knowledge/concepts/` | `event-sourcing.md` |
| decision | `01-Knowledge/decisions/` | `use-kafka.md` |
| person | `01-Knowledge/people/` | `alice-smith.md` |
| article_summary | `03-Resources/articles/` | `scaling-microservices.md` |
| moc / synthesis | `04-MOCs/` | `moc-distributed-systems.md` |

## Notifications

The `notify` step stores notification text in ZenML step metadata via `log_notification()`. The NanoClaw host polls completed runs every 30 seconds, reads the metadata, and delivers via WhatsApp.

## Vault I/O

`obsidian_io.py` abstracts vault storage:
- **Remote (S3):** Uses ZenML artifact store's `store.open()` — no direct boto3 calls
- **Local fallback:** Reads/writes to `VAULT_ROOT` on disk when no S3 artifact store is configured
- Cross-reference and synthesis steps read from the same abstraction

The `VaultNoteMaterializer` dual-writes each note: JSON to ZenML artifact store (standard) + markdown to the `vault/` prefix. No local Obsidian vault is required — browsing notes in Obsidian is optional (see `docs/OBSIDIAN_ZENML_SETUP.md`).

## Project Structure

```
pipelines/
├── pyproject.toml
├── run.py                          # CLI entry point
├── configs/
│   └── dev.yaml                    # Docker requirements, parameters
├── src/
│   └── shared/
│       ├── config.py               # Vault paths, ZenML settings, env vars
│       ├── schemas.py              # Pydantic models (NoteType, VaultNote, etc.)
│       ├── obsidian_io.py          # Vault read/write via artifact store or local
│       ├── materializers.py        # VaultNoteMaterializer (dual-write)
│       └── notify.py               # ZenML metadata notifications
├── steps/
│   └── knowledge_ingest/
│       ├── acquire.py
│       ├── chunk.py
│       ├── extract.py
│       ├── cross_reference.py
│       ├── route.py                # create_note + update_note
│       ├── rebuild_links.py
│       ├── synthesis.py            # check_synthesis + synthesize_topic
│       └── notify.py
└── pipelines/
    └── knowledge_ingest.py
```
