---
date: 2026-03-01
tags:
  - nanoclaw
  - zenml
  - pipelines
type: project
source: agent
status: growing
---

# NanoClaw Pipelines

Automated data pipelines for the NanoClaw personal assistant, built on ZenML.

## Status

Active — initial pipeline set implemented, expanding feeds and vault integration.

## Pipelines

| Pipeline | Schedule | Purpose |
|----------|----------|---------|
| Inbox Processor | Daily midnight | Classify and file inbox notes |
| Morning Briefing | Weekdays 7 AM | Aggregate GitHub, calendar, Gmail, Slack, Discord, RSS |
| Personal CRM | Nightly 11 PM | Extract people and commitments from conversations |
| Document Processor | On-demand | Process uploaded files (PDF, CSV, XLSX) |
| Weekly Review | Sundays 10 AM | Vault changes, commitments, orphan detection |
| Content Monitor | Every 6 hours | RSS feed digest |

## Architecture

- All pipelines use `@pipeline(dynamic=True)` for runtime control flow
- Steps organized in per-pipeline subdirectories under `pipelines/steps/`
- AI steps use [[pydantic-ai-structured-output]] for typed LLM responses
- Notifications stored in ZenML metadata, delivered by NanoClaw host via WhatsApp

## Key Decisions

- [[0001-use-zenml-for-orchestration]]
- [[0002-replace-whatsapp-cloud-api]]

## Links

- [ZenML Cloud Dashboard](https://cloud.zenml.io)
- [Pipeline Source](../pipelines/)

## Related

- [[ai-tooling]]
- [[nanoclaw-architecture]]
- [[zenml-dynamic-pipelines]]
