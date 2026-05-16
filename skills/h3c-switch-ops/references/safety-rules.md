# Safety Rules

## High-Risk Changes

Treat these as high risk and call them out explicitly:

- changing the management VLAN or management SVI IP
- changing the default route
- modifying uplink trunks or bridge aggregations
- removing permitted VLANs from a trunk
- changing interfaces that currently carry remote access
- using `Telnet` for live execution

## Stop Conditions

Stop and ask the user before proceeding when:

- the release family cannot be confirmed
- command syntax differs across likely targets
- the user asks for direct execution without a prior collection step
- the current config is missing but the change depends on removals
- the requested change touches `ACL`, `QoS`, `IRF`, `OSPF`, or `BGP`

## Execution Rules

- Collect first, then plan, then execute.
- Require explicit confirmation before `device_apply.py` runs.
- Prefer additive commands unless the current state is confirmed.
- When rollback fidelity is uncertain, say so instead of faking certainty.
