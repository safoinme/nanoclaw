"""ZenML Cloud connection settings and vault configuration."""

from __future__ import annotations

import os
from pathlib import Path


# ZenML Cloud connection
ZENML_STORE_URL: str = os.getenv(
    "ZENML_STORE_URL", "https://11870fb5-zenml.cloudinfra.zenml.io"
)
ZENML_STORE_API_KEY: str = os.getenv("ZENML_STORE_API_KEY", "")

# Obsidian vault paths
VAULT_ROOT: Path = Path(os.getenv("VAULT_ROOT", str(Path.home() / "obsidian-vault")))
VAULT_INBOX: Path = VAULT_ROOT / "00-Inbox"
VAULT_PEOPLE: Path = VAULT_ROOT / "05-People"
VAULT_ARCHIVE: Path = VAULT_ROOT / "09-Archive"
VAULT_DAILY: Path = VAULT_ROOT / "01-Daily"
VAULT_PROJECTS: Path = VAULT_ROOT / "03-Projects"
VAULT_RESOURCES: Path = VAULT_ROOT / "04-Resources"
VAULT_MOC: Path = VAULT_ROOT / "02-MOCs"

# WhatsApp Cloud API
WHATSAPP_API_URL: str = os.getenv(
    "WHATSAPP_API_URL", "https://graph.facebook.com/v21.0"
)
WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_RECIPIENT: str = os.getenv("WHATSAPP_RECIPIENT", "")

# Anthropic
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# E2B
E2B_API_KEY: str = os.getenv("E2B_API_KEY", "")
