---
date: 2026-03-01
tags:
  - nanoclaw/pipelines
  - ideas
type: capture
source: user
status: seed
---

# Notion Sync Pipeline Idea

Add a pipeline that syncs key Notion databases into the Obsidian vault. Could pull project boards, meeting notes, and shared documents on a schedule.

Approach: use the Notion API to list recently modified pages in configured databases, convert blocks to Markdown, save to `03-Resources/` with proper frontmatter. Dedup by page ID stored in frontmatter.

Related: [[nanoclaw-pipelines]], [[zenml-dynamic-pipelines]]
