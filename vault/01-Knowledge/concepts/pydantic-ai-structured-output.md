---
date: 2026-03-01
tags:
  - ai/pydantic
  - python/typing
type: concept
source: web
status: seed
---

# PydanticAI Structured Output

PydanticAI uses `result_type` on the `Agent` constructor to enforce structured output from LLMs. The model's response is validated against a Pydantic model, with automatic retries on validation failure.

## How It Works

```python
from pydantic import BaseModel
from pydantic_ai import Agent

class BriefingSummary(BaseModel):
    headline: str
    key_points: list[str]
    action_items: list[str]

agent = Agent("claude-3-5-sonnet-latest", result_type=BriefingSummary)
result = await agent.run("Summarize this briefing...")
# result.data is a validated BriefingSummary instance
```

The agent serializes the Pydantic model schema into the system prompt, instructing the LLM to return JSON matching that schema. On validation error, it feeds the error back to the LLM and retries (default 3 attempts).

## Key Patterns

- **Nested models** work — use them for complex outputs like briefings with sections
- **`Optional` fields** let the model skip things it can't determine
- **`Field(description=...)`** adds context the model uses to fill the field correctly
- **Union types** (`result_type=A | B`) let the model choose the most appropriate shape

## Used In NanoClaw

The pipelines use `result_type` in summarization steps: `summarize.py` (morning briefing), `summarize_feeds.py` (content monitor), `compile_review.py` (weekly review). Each defines a Pydantic model in `src/shared/schemas.py`.

## Related

- [[zenml-dynamic-pipelines]]
- [[nanoclaw-pipelines]]
