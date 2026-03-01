---
date: 2026-03-01
tags:
  - zenml
  - pipelines
type: capture
source: agent
status: seed
---

# ZenML Dynamic Pipeline Patterns

While reworking the pipelines package, learned several useful patterns for `@pipeline(dynamic=True)`:

- `.map(items)` fans out a step across a list — great for fetching multiple sources in parallel
- `.submit()` queues a step without blocking — useful for fire-and-forget notifications
- `.load()` references artifacts from previous steps by name — avoids passing large data through function args
- Conditional branches with `if` inside the pipeline function work naturally — unconfigured sources just skip

These patterns replaced 6 separate fetch steps with a single parameterized `fetch_source` step.

Related: [[zenml-dynamic-pipelines]], [[0001-use-zenml-for-orchestration]]
