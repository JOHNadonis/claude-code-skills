---
name: mcp-okx-trade-kit
description: Install and use OKX Agent Trade Kit via the official OKX MCP/CLI packages, including read-only market setup, demo/live profiles, and Hermes native MCP integration.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [okx, trading, mcp, cli, crypto]
    related_skills: [native-mcp, mcporter]
---

# OKX Trade Kit

Use this skill when the user wants to install, upgrade, or use **OKX Agent Trade Kit** / **OKX Trade MCP** / **OKX Trade CLI**.

It covers:
- global install / upgrade
- MCP server setup for Hermes
- CLI usage
- demo vs live profiles
- the common "read-only market first" workflow

## Quick Summary

The OKX stack is split into two official packages:
- `@okx_ai/okx-trade-mcp` — MCP server for AI tools
- `@okx_ai/okx-trade-cli` — CLI tool for humans / scripted use

There are alias packages on npm as well:
- `okx-trade-mcp`
- `okx-trade-cli`

Both install paths are equivalent.

## Install / Upgrade

### Global install

```bash
npm install -g @okx_ai/okx-trade-mcp @okx_ai/okx-trade-cli
```

Or, with the alias packages:

```bash
npm install -g okx-trade-mcp okx-trade-cli
```

### Upgrade existing install

```bash
npm update -g @okx_ai/okx-trade-mcp @okx_ai/okx-trade-cli
```

Or:

```bash
npm update -g okx-trade-mcp okx-trade-cli
```

## First-Run Configuration

The official MCP package reads credentials from:

```bash
~/.okx/config.toml
```

A minimal example:

```toml
default_profile = "demo"

[profiles.demo]
api_key = "your-demo-api-key"
secret_key = "your-demo-secret-key"
passphrase = "your-demo-passphrase"
demo = true

[profiles.live]
api_key = "your-live-api-key"
secret_key = "your-live-secret-key"
passphrase = "your-live-passphrase"
```

If the user does not have API keys yet, prefer **read-only market mode** first.

## Safe Default: Read-Only Market Mode

If the goal is to inspect markets or prototype agents, start without trading permissions:

```bash
okx-trade-mcp --modules market --read-only
```

This is the safest way to get value immediately.

## Hermes Native MCP Integration

To make OKX tools available inside Hermes Agent, add a server to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  okx:
    command: "npx"
    args: ["-y", "@okx_ai/okx-trade-mcp", "--modules", "market", "--read-only"]
```

For a demo or live profile:

```yaml
mcp_servers:
  okx-demo:
    command: "npx"
    args: ["-y", "@okx_ai/okx-trade-mcp", "--profile", "demo", "--modules", "all"]

  okx-live:
    command: "npx"
    args: ["-y", "@okx_ai/okx-trade-mcp", "--profile", "live", "--modules", "all"]
```

Remember:
- restart Hermes after changing `mcp_servers`
- keep `read-only` on until you explicitly want trading actions
- use demo mode before live mode

## CLI Usage

```bash
okx --help
okx market ticker BTC-USDT
okx account balance
okx swap positions
```

If the tool name is `okx-trade-cli` in the user's environment, the package is still the same functionality.

## Useful Agent Prompts

For read-only market work, ask the agent things like:
- "Use the OKX market tools to summarize BTC-USDT trend and volume."
- "Filter OKX market data for unusual price/volume behavior."
- "Track sentiment-related signals around this token and summarize the result."

If the upstream kit exposes specialized skills/modules such as `okx-market-filter` or `okx-sentiment-tracker`, treat them as part of the OKX trade workflow and explain what they do before using them.

## Troubleshooting

- **Command not found**: ensure Node.js/npm are installed and the global npm bin is on PATH.
- **No tools appear in Hermes**: restart Hermes after adding `mcp_servers`.
- **Auth errors**: verify `~/.okx/config.toml`, especially `api_key`, `secret_key`, and `passphrase`.
- **Prefer demo first**: live trading should only be enabled after confirming the setup in demo mode.

## Recommended Workflow

1. Install the packages.
2. Start with `--modules market --read-only`.
3. Confirm Hermes can see the MCP tools.
4. Switch to `--profile demo`.
5. Only then consider `--profile live`.
