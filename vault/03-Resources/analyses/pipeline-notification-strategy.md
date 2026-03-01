---
date: 2026-03-01
tags:
  - analysis
  - nanoclaw/notifications
  - zenml
type: analysis
source: agent
status: seed
---

# Pipeline Notification Strategy

## Question

How should NanoClaw pipelines deliver notifications to the user? Pipelines run on ZenML Cloud but the user interacts via WhatsApp through the NanoClaw host process.

## Findings

Three approaches considered:

**Direct WhatsApp from pipeline** — Pipeline steps call WhatsApp API directly. Problem: Baileys session is tied to the host process, can't share across processes/machines.

**Webhook callback** — Pipeline hits a webhook on the NanoClaw host. Problem: requires the host to expose a public endpoint, adds infrastructure complexity.

**Metadata-based (chosen)** — Pipeline steps store notification text in ZenML step metadata via `log_notification()`. The host process polls pipeline run status and reads metadata on completion. No direct coupling between pipeline and messaging.

## Conclusions

The metadata approach wins because:
- Zero coupling between pipelines and messaging channel
- Works with any channel (WhatsApp, Telegram, Slack) — the host handles routing
- No infrastructure beyond what ZenML Cloud already provides
- Notifications are persisted as artifacts — visible in dashboard and queryable

Trade-off: slight delay (polling interval) between pipeline completion and notification delivery. Acceptable for non-real-time use cases like morning briefings.

## Related

- [[nanoclaw-pipelines]]
- [[nanoclaw-architecture]]
- [[0002-replace-whatsapp-cloud-api]]
