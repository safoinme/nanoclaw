"""WhatsApp Cloud API notification sender."""

from __future__ import annotations

import logging

import httpx

from src.shared.config import (
    WHATSAPP_API_URL,
    WHATSAPP_PHONE_ID,
    WHATSAPP_RECIPIENT,
    WHATSAPP_TOKEN,
)

logger = logging.getLogger(__name__)


def send_whatsapp_message(
    text: str,
    recipient: str | None = None,
) -> bool:
    """Send a text message via WhatsApp Cloud API.

    Returns True on success, False on failure.
    """
    recipient = recipient or WHATSAPP_RECIPIENT
    if not all([WHATSAPP_PHONE_ID, WHATSAPP_TOKEN, recipient]):
        logger.warning("WhatsApp credentials not configured, skipping notification")
        return False

    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": text},
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        logger.info("WhatsApp message sent successfully")
        return True
    except httpx.HTTPError as e:
        logger.error("Failed to send WhatsApp message: %s", e)
        return False


def format_briefing_message(
    summary: str,
    action_items: list[str],
    highlights: list[str],
) -> str:
    """Format a morning briefing for WhatsApp (plain text, no markdown)."""
    lines = [f"Good morning! Here's your briefing:\n\n{summary}"]

    if highlights:
        lines.append("\nHighlights:")
        for h in highlights:
            lines.append(f"- {h}")

    if action_items:
        lines.append("\nAction items:")
        for i, item in enumerate(action_items, 1):
            lines.append(f"{i}. {item}")

    return "\n".join(lines)
