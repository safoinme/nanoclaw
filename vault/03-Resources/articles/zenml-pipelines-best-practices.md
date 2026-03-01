---
date: 2026-03-01
tags:
  - article
  - zenml
  - pipelines/patterns
type: article
source: web
status: seed
url: https://docs.zenml.io/how-to/build-pipelines
---

# ZenML Pipelines Best Practices

## Summary

Collection of patterns and practices for building production ZenML pipelines, drawn from docs and community experience. Covers dynamic pipelines, step design, artifact management, and configuration.

## Key Takeaways

- Use `@pipeline(dynamic=True)` when you need runtime branching or fan-out — static pipelines can't do conditional logic
- Keep steps focused: one step = one logical operation. Combine only when the overhead of serialization outweighs clarity
- Use `Annotated[Type, "name"]` for step outputs to give artifacts meaningful names in the dashboard
- Store secrets in ZenML's secret store rather than environment variables — they're versioned and access-controlled
- Use `log_metadata()` to attach step-level metrics visible in the ZenML dashboard
- Configuration via YAML (`configs/dev.yaml`) keeps pipeline code clean and environments separate

## Notes

Applied these patterns in the NanoClaw pipelines rework:
- Morning briefing uses `.map()` to fan out across sources
- All steps use `Annotated` return types for clear artifact naming
- Secrets for GitHub, Gmail, Calendar stored in ZenML secret store
- `dev.yaml` config separates development settings from production

## Related

- [[zenml-dynamic-pipelines]]
- [[nanoclaw-pipelines]]
- [[0001-use-zenml-for-orchestration]]
