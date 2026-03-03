"""ZenML Cloud connection settings and vault configuration."""

from __future__ import annotations

import os
from pathlib import Path


# ZenML Cloud connection
ZENML_STORE_URL: str = os.getenv(
    "ZENML_STORE_URL", "https://72982075-zenml.staging.cloudinfra.zenml.io"
)
ZENML_STORE_API_KEY: str = os.getenv("ZENML_STORE_API_KEY", "")

# S3 vault configuration (prefix within ZenML artifact store bucket)
VAULT_PREFIX: str = os.getenv("VAULT_PREFIX", "vault")

# Local vault root (fallback for dev/testing without S3)
VAULT_ROOT: Path = Path(os.getenv("VAULT_ROOT", str(Path.home() / "obsidian-vault")))

# Vault folder constants (S3-compatible string paths)
VAULT_INBOX = "00-Inbox"
VAULT_CAPTURES = "00-Inbox/captures"
VAULT_DAILY = "00-Inbox/daily"
VAULT_KNOWLEDGE = "01-Knowledge"
VAULT_PEOPLE = "01-Knowledge/people"
VAULT_CONCEPTS = "01-Knowledge/concepts"
VAULT_DECISIONS = "01-Knowledge/decisions"
VAULT_PROJECTS = "02-Projects"
VAULT_RESOURCES = "03-Resources"
VAULT_ARTICLES = "03-Resources/articles"
VAULT_ANALYSES = "03-Resources/analyses"
VAULT_MOC = "04-MOCs"
VAULT_TEMPLATES = "05-Templates"

# AI model (PydanticAI format: "provider:model", e.g. "openai:gpt-4o", "anthropic:claude-sonnet-4-20250514")
AI_MODEL: str = os.getenv("AI_MODEL", "openai:gpt-4o")

# E2B
E2B_API_KEY: str = os.getenv("E2B_API_KEY", "")


def vault_key(folder: str, filename: str) -> str:
    """Construct a full vault key for the artifact store.

    Returns a path like 'vault/01-Knowledge/concepts/my-note.md'.
    """
    return f"{VAULT_PREFIX}/{folder}/{filename}"
