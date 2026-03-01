---
date: 2026-03-01
tags:
  - moc
  - nanoclaw
type: moc
source: agent
status: seed
---

# NanoClaw Architecture

Map of content for NanoClaw system architecture, decisions, and components.

## Core Decisions

- [[0001-use-zenml-for-orchestration]] — Pipeline framework selection
- [[0002-replace-whatsapp-cloud-api]] — Messaging channel choice

## Components

- [[nanoclaw-pipelines]] — ZenML pipeline system (briefing, CRM, content, inbox)
- [[pipeline-notification-strategy]] — How pipelines deliver notifications

## Technical Concepts

- [[zenml-dynamic-pipelines]] — Dynamic pipeline patterns used throughout
- [[pydantic-ai-structured-output]] — AI output validation for pipeline steps

## People

- [[zenml-team]] — ZenML framework team

## System Overview

```
WhatsApp (Baileys) → NanoClaw Host (Node.js)
    ├── Message Router → Claude Agent SDK (containers)
    ├── Task Scheduler → ZenML Pipelines (cloud)
    │   ├── Morning Briefing (daily)
    │   ├── Inbox Processor (daily)
    │   ├── Personal CRM (nightly)
    │   ├── Content Monitor (6h)
    │   └── Weekly Review (weekly)
    └── Obsidian Vault (persistent knowledge)
```
