# Obsidian Vault Conventions

This vault is the agent's persistent knowledge base. Follow these rules exactly.

## When to Save

Save when the conversation contains:
- **Knowledge worth preserving** — concepts, explanations, technical details, how-tos
- **People mentioned** — names, roles, preferences, relationship context
- **Decisions made** — choices with rationale, trade-offs considered
- **Interesting articles or links** — with summary and key takeaways
- **Daily activity** — notable events, tasks completed, observations

Do NOT save trivial chit-chat, transient status updates, or duplicate information already in the vault.

## Where to Save

| Content type | Folder | Template |
|---|---|---|
| Quick captures, unsorted notes | `00-Inbox/captures/` | `05-Templates/capture.md` |
| Daily notes | `00-Inbox/daily/` | `05-Templates/daily.md` |
| Concepts, explanations, how-tos | `01-Knowledge/concepts/` | — |
| Decision records | `01-Knowledge/decisions/` | `05-Templates/decision.md` |
| People notes | `01-Knowledge/people/` | `05-Templates/person.md` |
| Active projects | `02-Projects/` | — |
| Article summaries | `03-Resources/articles/` | `05-Templates/article.md` |
| Analyses, deep dives | `03-Resources/analyses/` | `05-Templates/analysis.md` |
| Maps of Content (index notes) | `04-MOCs/` | — |

## Frontmatter Schema

Every note MUST start with YAML frontmatter:

```yaml
---
date: 2026-03-01
tags:
  - topic/subtopic
type: capture | person | decision | article | analysis | daily | concept | project
source: whatsapp | web | agent | user
status: seed | growing | evergreen
---
```

- `date` — creation date in YYYY-MM-DD format
- `tags` — use nested tags like `topic/subtopic`
- `type` — one of the listed types, matching the content
- `source` — where the information came from
- `status` — `seed` (new/rough), `growing` (being developed), `evergreen` (mature/stable)

## Linking Rules

- Use `[[wikilinks]]` for all internal vault links
- Use `[[Note Name#Heading]]` to link to specific sections
- Use `[[Note Name|Display Text]]` for custom display text
- Use standard `[text](url)` only for external URLs
- Prefer linking to existing notes over creating duplicates

## File Naming

- Use descriptive kebab-case: `my-note-title.md`
- People: `firstname-lastname.md`
- Daily: `YYYY-MM-DD.md`
- Decisions: `NNNN-decision-title.md` (zero-padded sequence number)

## What NEVER to Do

- **Never touch `.obsidian/`** — this directory contains app config and plugins
- **Never delete existing notes** — only append, update, or create new ones
- **Never overwrite a note without reading it first** — always use atomic writes (read → modify → write)
- **Never create notes without frontmatter** — every `.md` file needs the YAML header
- **Never use raw Markdown links for internal vault references** — always use `[[wikilinks]]`
