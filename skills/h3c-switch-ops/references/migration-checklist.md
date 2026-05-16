# Migration Checklist

## Before Cutover

- Confirm model, software line, and whether the target is `Comware 5` or `Comware 7`.
- Back up `display current-configuration` and `display version`.
- Capture `display vlan`, `display interface brief`, and `display link-aggregation summary`.
- Identify management VLAN, default gateway, uplinks, aggregation members, and special static routes.
- Mark interfaces that carry management reachability or production uplinks.
- Produce a rollback command set before the maintenance window starts.

## During Cutover

- Disable paging with `screen-length disable`.
- Save pre-change evidence to a timestamped file.
- Apply low-risk object creation first: VLANs, aggregate interface, SVI.
- Apply interface membership and access/trunk changes next.
- Apply static routes last.
- Run verification commands after each stage, not only at the end.

## After Cutover

- Verify management reachability.
- Verify VLAN membership and expected interface states.
- Verify link aggregation member selection.
- Verify default route and application reachability.
- Save the post-change config only after checks are clean.

## Rollback Triggers

Rollback immediately if any of the following happen:

- management IP becomes unreachable
- uplink or aggregation members go down unexpectedly
- wrong VLAN reaches access ports
- default route or northbound reachability breaks
- syntax mismatch appears because the release is not what was assumed
