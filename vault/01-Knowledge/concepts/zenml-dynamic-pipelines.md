---
date: 2026-03-01
tags:
  - zenml
  - pipelines/orchestration
type: concept
source: web
status: growing
---

# ZenML Dynamic Pipelines

Dynamic pipelines (`@pipeline(dynamic=True)`) enable runtime control flow: conditional branches, fan-out/fan-in, and artifact loading by name. This replaced static pipeline definitions in NanoClaw.

## Core Patterns

### Fan-out with `.map()`

```python
@pipeline(dynamic=True)
def morning_briefing():
    configs = get_source_configs()
    results = fetch_source.map(configs)  # parallel execution
    summary = summarize(results)
    deliver(summary)
```

Each item in `configs` spawns a separate `fetch_source` step. ZenML handles parallelism.

### Fire-and-forget with `.submit()`

```python
deliver.submit(summary)  # non-blocking, pipeline doesn't wait
```

### Artifact loading with `.load()`

```python
data = some_step.load()  # reference artifact by step name
```

### Conditional branches

```python
if has_feeds:
    summarize_feeds(items)
else:
    log.info("No feeds to process")
```

Standard Python `if` works inside dynamic pipelines — skipped branches don't create steps.

## NanoClaw Usage

| Pipeline | Pattern |
|----------|---------|
| Morning Briefing | `.map()` across source configs |
| Content Monitor | Conditional on feed availability |
| Document Processor | `.submit()` for async vault write |

## Related

- [[0001-use-zenml-for-orchestration]]
- [[pydantic-ai-structured-output]]
- [[nanoclaw-pipelines]]
