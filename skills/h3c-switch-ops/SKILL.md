---
name: h3c-switch-ops
description: Use when working with H3C/华三 Comware 5 or 7 switches for VLAN, access/trunk, bridge aggregation, SVI, static-route changes, old-to-new switch migration, current-configuration parsing, read-only real-device validation, rollback preparation, or cautious SSH/Telnet collection and execution.
---

# H3C Switch Ops

## Overview

Use this skill for H3C switch configuration, migration, cautious change execution, and real-device read-only validation. Prefer deterministic parsing and change planning before any direct device action.

## Route The Request

- **Generate config** — Use for greenfield or incremental switch changes. Ask for `Comware 5/7`, hostname, VLAN plan, interface roles, uplinks, SVI IPs, and routes.
- **Migrate old config** — Use when the user pastes old H3C config or wants old-to-new replacement. Run `scripts/parse_config.py` first, then `scripts/build_change_plan.py`.
- **Read-only real-device validation** — Use when the user wants to verify that SSH/Telnet collection, parsing, and plan generation work on a real legacy H3C switch without pushing config. Run `scripts/readonly_validation.py`.
- **Collect or execute** — Use when the user wants direct device interaction. Run `scripts/device_collect.py` first. Run `scripts/device_apply.py` only after explicit confirmation.

## Default Workflow

1. Detect `Comware 5` vs `Comware 7`. If unknown, ask or infer cautiously from version output or config text.
2. Normalize the request into structured intent: VLANs, interfaces, aggregations, SVIs, and static routes.
3. Return these sections whenever possible: `Target Config`, `Change Commands`, `Rollback`, `Verification`, `Risks`.
4. Mark uplinks, aggregation members, management VLANs, default routes, and `Telnet` as high risk.
5. For real-device validation, keep the workflow read-only: collect, parse, generate a plan-only sample, and write a report.

## Inputs To Gather

Request only the missing fields:

- device version or `display version`
- current config or desired port/VLAN plan
- which ports are access, trunk, uplink, or aggregation members
- management VLAN and gateway
- whether the task is plan-only, read-only validation, or confirmed execution

## Scripts

- Parse config:
  - `python3 scripts/parse_config.py --input /path/to/current.cfg --pretty`
- Build change plan:
  - `python3 scripts/build_change_plan.py --input /path/to/intent.json --pretty`
- Read-only real-device validation:
  - `python3 scripts/readonly_validation.py --host 10.0.0.10 --username admin --protocol auto --output-dir /tmp/h3c-real-check/sw01`
- Collect from device:
  - `python3 scripts/device_collect.py --host 10.0.0.10 --username admin --protocol auto --execute --output-dir /tmp/h3c-collect/sw01`
- Apply commands after confirmation:
  - `python3 scripts/device_apply.py --host 10.0.0.10 --username admin --commands-file ./commands.txt --confirm-execute`

## References

- `references/comware5.md` — common syntax and operational reminders for older releases
- `references/comware7.md` — common syntax and operational reminders for newer releases
- `references/migration-checklist.md` — pre-check, cutover, validation, rollback flow
- `references/safety-rules.md` — high-risk changes and stop conditions
- `references/prompt-templates.md` — structured prompt formats for new builds, migration, read-only validation, and execution

## Guardrails

- Never default to direct execution.
- Never silently remove trunk VLANs or change management reachability.
- For read-only validation, never enter `device_apply.py` or send `system-view` configuration changes.
- If syntax is uncertain, stop and say so.
- Treat `Telnet` as compatibility-only and insecure.
