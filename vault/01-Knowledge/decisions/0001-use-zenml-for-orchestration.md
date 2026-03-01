---
date: 2026-03-01
tags:
  - decision
  - zenml
  - nanoclaw/architecture
type: decision
source: user
status: growing
---

# Use ZenML for Pipeline Orchestration

## Context

NanoClaw needs scheduled data pipelines (morning briefing, CRM updates, content monitoring). These pipelines fetch from multiple sources, process with AI, and write to the Obsidian vault. Need: scheduling, parallelism, artifact tracking, and cloud execution.

## Options Considered

1. **ZenML** — Python-native pipeline framework with cloud orchestration, artifact versioning, and dynamic pipelines
2. **Prefect** — Python workflow orchestration with good scheduling but heavier infrastructure
3. **Custom cron + scripts** — Simple but no artifact tracking, retry logic, or observability
4. **Temporal** — Durable execution engine, powerful but over-engineered for personal use

## Decision

Use ZenML with ZenML Cloud for orchestration and tracking.

## Rationale

- Dynamic pipelines (`@pipeline(dynamic=True)`) support runtime branching and `.map()` fan-out — exactly what morning briefing needs
- ZenML Cloud provides scheduling, monitoring, and secret management without self-hosting
- Steps are plain Python functions with type annotations — minimal framework lock-in
- Artifact versioning gives free observability into what each pipeline produced
- PydanticAI integration is natural since both use Pydantic models

## Consequences

- Depends on ZenML Cloud availability for scheduled runs
- Pipeline code must follow ZenML step/pipeline conventions
- Secrets (API tokens) stored in ZenML secret store rather than local `.env`
- Local development requires `zenml init` and stack configuration
