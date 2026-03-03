---
name: obsidian-save
description: Save knowledge to the Obsidian vault. Use when the conversation contains information worth preserving — concepts, people, decisions, articles, or daily notes. Triggers on "save this", "remember this", "note this", "add to vault", or when knowledge worth preserving appears in conversation.
---

# Obsidian Save Skill

Save information from conversations into the Obsidian vault at `vault/`. Read `vault/AGENT.md` for full conventions before writing any notes.

## Vault Structure

| Folder | Content type |
|---|---|
| `00-Inbox/captures/` | Quick captures, unsorted notes |
| `00-Inbox/daily/` | Daily notes (one per day) |
| `01-Knowledge/concepts/` | Concepts, explanations, how-tos |
| `01-Knowledge/decisions/` | Decision records with rationale |
| `01-Knowledge/people/` | People — roles, preferences, context |
| `02-Projects/` | Active project notes |
| `03-Resources/articles/` | Article summaries with takeaways |
| `03-Resources/analyses/` | Deep dives and analyses |
| `04-MOCs/` | Maps of Content (index notes) |
| `05-Templates/` | Note templates (do not modify) |

## Save Rules

1. **Always read `vault/AGENT.md` first** if you haven't this session
2. **Check for existing notes** before creating — search the vault to avoid duplicates
3. **Use the correct folder** based on content type (see table above)
4. **Use templates** from `05-Templates/` as starting points
5. **Always include frontmatter**:

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

6. **Use `[[wikilinks]]`** for internal vault links, standard `[text](url)` for external URLs only
7. **Use kebab-case filenames**: `my-note-title.md`
8. **People files**: `firstname-lastname.md` in `01-Knowledge/people/`
9. **Daily notes**: `YYYY-MM-DD.md` in `00-Inbox/daily/`
10. **Decision records**: `NNNN-decision-title.md` in `01-Knowledge/decisions/`

## What NEVER to Do

- Never touch `vault/.obsidian/`
- Never delete existing notes
- Never overwrite without reading first
- Never create notes without frontmatter
- Never use raw Markdown links for internal references

## Formatting

For Obsidian-specific markdown formatting (callouts, embeds, block references), refer to the `obsidian-markdown` skill which is available to container agents.
