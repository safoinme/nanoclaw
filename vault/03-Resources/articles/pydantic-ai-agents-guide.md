---
date: 2026-03-01
tags:
  - article
  - ai/pydantic
  - ai/agents
type: article
source: web
status: seed
url: https://ai.pydantic.dev/
---

# PydanticAI Agents Guide

## Summary

PydanticAI is a Python agent framework that brings Pydantic's type-safe validation to LLM interactions. Agents define a `result_type` (a Pydantic model) and the framework handles prompt construction, response parsing, and validation with automatic retries.

## Key Takeaways

- `Agent(model, result_type=MyModel)` creates a type-safe agent that returns validated Pydantic instances
- `system_prompt` can be a string or a function that receives `RunContext` for dynamic prompts
- Tools are plain Python functions decorated with `@agent.tool` — the framework injects parameters from context
- `result_type` supports `Union` types, letting the model choose the most appropriate output shape
- Built-in retry logic re-prompts the model with validation errors until output conforms

## Notes

Used in NanoClaw's pipeline steps for all AI summarization. Each step defines its output as a Pydantic model in `schemas.py`, then wraps the LLM call in a PydanticAI agent. This gives type-safe outputs that integrate naturally with ZenML's artifact system.

## Related

- [[pydantic-ai-structured-output]]
- [[nanoclaw-pipelines]]
