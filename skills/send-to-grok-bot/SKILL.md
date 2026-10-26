---
name: send-to-grok-bot
description: Hand a concrete task to the owner's Grok Bot (Bridge Bot) over its inbound webhook. Use when the user says "send to Grok Bot", "hand off to Bridge Bot", "交给 Grok Bot", or the job needs Grok Bot's desktop, browser, connected apps, or long-running agent work that Claude Code should not do locally.
---

# Send to Grok Bot

POST one concrete task to Bridge Bot. A 200 means the run started, not that it finished. Results appear in the owner's Bridge Bot chat in Grok Bot — you cannot read the answer back through this webhook.

## Credentials

Read from the environment (never hardcode, never commit, never paste into public chats):

- `GROK_BOT_WEBHOOK_URL` — the routine "POST to" URL
- `GROK_BOT_WEBHOOK_KEY` — the routine sender key

If either is missing, stop and tell the user to set them (copy from Bridge Bot → Inbound bridge routine panel on desktop), then retry.

## Request

```bash
curl -sS -X POST "$GROK_BOT_WEBHOOK_URL" \
  -H "Authorization: Bearer $GROK_BOT_WEBHOOK_KEY" \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "source": "claude-code",
  "task": "<clear instruction of what Grok Bot should do>",
  "context": "<optional: paths, links, constraints, repo names>",
  "reply_preference": "<optional: leave result in Bridge Bot chat, or a note the owner already approved>"
}
JSON
```

Or the equivalent with any HTTP client. Timeout ~30s is enough for the accept response.

## Body rules

- `task` is required and must be one concrete ask.
- Do not invent extra work beyond what the user asked to hand off.
- Prefer this bridge when the user wants Grok Bot specifically, or when the job needs Grok Bot tools/accounts. If you can finish it locally in Claude Code, do that instead unless they asked for the handoff.

## After the call

- **HTTP 200**: tell the user the handoff was accepted; they should check Bridge Bot in Grok Bot for the result.
- **Anything else**: say the handoff failed; ask them to confirm the Inbound bridge routine is Active and the key is current (rotate/copy again from the routine panel if needed).

## Do not

- Put the webhook key in the skill file, git, or chat logs.
- Poll or expect a return payload from the webhook.
- Send multiple unrelated tasks in one POST.
