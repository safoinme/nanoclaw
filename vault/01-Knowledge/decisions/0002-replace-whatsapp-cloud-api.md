---
date: 2026-03-01
tags:
  - decision
  - nanoclaw/channels
  - whatsapp
type: decision
source: user
status: growing
---

# Replace WhatsApp Cloud API with Baileys

## Context

NanoClaw originally used the WhatsApp Cloud API (Meta Business Platform) for messaging. This required a Meta Business account, app review, phone number registration, and webhook hosting. The setup was fragile and rate-limited.

## Options Considered

1. **Baileys (whatsapp-web.js successor)** — Open-source library that connects via WhatsApp Web protocol, no Meta account needed
2. **WhatsApp Cloud API** — Official API, requires Meta Business setup, webhook endpoint, app review
3. **Telegram Bot API** — Simple and well-documented, but different user base
4. **Matrix/Element** — Open protocol, self-hostable, but less mainstream adoption

## Decision

Use Baileys for WhatsApp connectivity. Keep Telegram as an optional additional channel.

## Rationale

- No Meta Business account or app review required — just scan a QR code
- Works with personal WhatsApp number — no separate business number needed
- Full message access including media, reactions, and group management
- Can run as a background service without a public webhook URL
- Community-maintained and actively developed

## Consequences

- Relies on reverse-engineered protocol — could break if WhatsApp changes their web client
- No official support or SLA
- Must handle session persistence (auth state) carefully to avoid re-authentication
- Need to respect WhatsApp rate limits to avoid account bans
