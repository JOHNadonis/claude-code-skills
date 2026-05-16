#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from common import detect_version_family, dump_json, expand_vlan_expression, split_blocks, utc_now, write_text

PARSER_VERSION = "1.0.0"


def parse_vlan_block(lines: list[str]) -> dict:
    header = lines[0].strip()
    vlan_id = int(header.split()[1])
    vlan = {"id": vlan_id, "name": None, "description": None}

    for raw_line in lines[1:]:
        line = raw_line.strip()
        lowered = line.lower()
        if lowered.startswith("name "):
            vlan["name"] = line[5:].strip()
        elif lowered.startswith("description "):
            vlan["description"] = line[12:].strip()

    return vlan


def parse_interface_block(lines: list[str]) -> dict:
    header = lines[0].strip()
    name = header.split(None, 1)[1].strip()
    category = "physical"
    svi_match = re.match(r"(?i)^Vlan-interface\s*(\d+)$", name)
    agg_match = re.match(r"(?i)^Bridge-Aggregation\s*(\d+)$", name)
    if svi_match:
        category = "svi"
    elif agg_match:
        category = "aggregation"

    interface = {
        "name": name,
        "category": category,
        "description": None,
        "shutdown": None,
        "link_type": None,
        "access_vlan": None,
        "trunk_pvid": None,
        "trunk_vlans": [],
        "hybrid_tagged_vlans": [],
        "hybrid_untagged_vlans": [],
        "aggregation_group": None,
        "aggregation_mode": None,
        "ip_address": None,
        "mask": None,
        "unparsed_lines": [],
        "raw_lines": [line.rstrip() for line in lines[1:]],
    }

    if svi_match:
        interface["vlan"] = int(svi_match.group(1))
    if agg_match:
        interface["aggregation_id"] = int(agg_match.group(1))

    for raw_line in lines[1:]:
        line = raw_line.strip()
        lowered = line.lower()
        handled = True

        if lowered.startswith("description "):
            interface["description"] = line[12:].strip()
        elif lowered == "shutdown":
            interface["shutdown"] = True
        elif lowered == "undo shutdown":
            interface["shutdown"] = False
        elif lowered.startswith("port link-type "):
            interface["link_type"] = line.split()[-1].lower()
        elif lowered.startswith("port access vlan "):
            interface["access_vlan"] = int(line.split()[-1])
        elif lowered.startswith("port trunk pvid vlan "):
            interface["trunk_pvid"] = int(line.split()[-1])
        elif lowered.startswith("port trunk permit vlan "):
            interface["trunk_vlans"] = expand_vlan_expression(line.split("vlan", 1)[1].strip())
        elif lowered.startswith("port hybrid pvid vlan "):
            interface["trunk_pvid"] = int(line.split()[-1])
        elif lowered.startswith("port hybrid vlan ") and lowered.endswith(" tagged"):
            body = re.sub(r"(?i)^port hybrid vlan\s+", "", line)
            body = re.sub(r"(?i)\s+tagged$", "", body)
            interface["hybrid_tagged_vlans"] = expand_vlan_expression(body)
        elif lowered.startswith("port hybrid vlan ") and lowered.endswith(" untagged"):
            body = re.sub(r"(?i)^port hybrid vlan\s+", "", line)
            body = re.sub(r"(?i)\s+untagged$", "", body)
            interface["hybrid_untagged_vlans"] = expand_vlan_expression(body)
        elif lowered.startswith("port link-aggregation group "):
            interface["aggregation_group"] = int(line.split()[-1])
        elif lowered.startswith("link-aggregation mode "):
            interface["aggregation_mode"] = line.split()[-1].lower()
        elif lowered.startswith("ip address "):
            parts = line.split()
            if len(parts) >= 4:
                interface["ip_address"] = parts[2]
                interface["mask"] = parts[3]
        else:
            handled = False

        if not handled and line:
            interface["unparsed_lines"].append(line)

    return interface


def parse_route_line(line: str) -> dict | None:
    parts = line.split()
    if len(parts) < 4 or parts[0].lower() != "ip" or parts[1].lower() != "route-static":
        return None

    route = {
        "destination": parts[2],
        "mask": parts[3] if len(parts) > 3 else None,
        "next_hop": parts[4] if len(parts) > 4 else None,
        "raw": line.strip(),
    }
    if len(parts) > 5:
        route["extra"] = parts[5:]
    return route


def parse_config(config_text: str, source: str = "<stdin>") -> dict:
    version_family = detect_version_family(config_text)
    result = {
        "hostname": None,
        "version_family": version_family,
        "version_hints": [],
        "vlans": [],
        "interfaces": [],
        "aggregations": [],
        "svis": [],
        "static_routes": [],
        "unparsed_blocks": [],
        "metadata": {
            "source": source,
            "parser_version": PARSER_VERSION,
            "generated_at": utc_now(),
        },
    }

    aggregations: dict[int, dict] = {}

    for block in split_blocks(config_text):
        header = block[0].strip()
        lowered = header.lower()

        if lowered.startswith("sysname "):
            result["hostname"] = header.split(None, 1)[1].strip()
            continue

        if lowered.startswith("version "):
            result["version_hints"].append(header)
            continue

        if re.match(r"(?i)^vlan\s+\d+$", header):
            result["vlans"].append(parse_vlan_block(block))
            continue

        if lowered.startswith("interface "):
            interface = parse_interface_block(block)
            result["interfaces"].append(interface)

            if interface["category"] == "svi":
                result["svis"].append(
                    {
                        "vlan": interface.get("vlan"),
                        "interface": interface["name"],
                        "description": interface.get("description"),
                        "ip_address": interface.get("ip_address"),
                        "mask": interface.get("mask"),
                        "shutdown": interface.get("shutdown"),
                    }
                )

            if interface["category"] == "aggregation":
                agg_id = interface.get("aggregation_id")
                if agg_id is not None:
                    entry = aggregations.setdefault(
                        agg_id,
                        {
                            "id": agg_id,
                            "name": interface["name"],
                            "members": [],
                            "mode": None,
                            "description": None,
                            "link_type": None,
                            "access_vlan": None,
                            "trunk_pvid": None,
                            "trunk_vlans": [],
                            "shutdown": interface.get("shutdown"),
                        },
                    )
                    entry.update(
                        {
                            "mode": interface.get("aggregation_mode"),
                            "description": interface.get("description"),
                            "link_type": interface.get("link_type"),
                            "access_vlan": interface.get("access_vlan"),
                            "trunk_pvid": interface.get("trunk_pvid"),
                            "trunk_vlans": interface.get("trunk_vlans", []),
                            "shutdown": interface.get("shutdown"),
                        }
                    )

            group_id = interface.get("aggregation_group")
            if group_id is not None:
                entry = aggregations.setdefault(
                    group_id,
                    {
                        "id": group_id,
                        "name": f"Bridge-Aggregation{group_id}",
                        "members": [],
                        "mode": None,
                        "description": None,
                        "link_type": None,
                        "access_vlan": None,
                        "trunk_pvid": None,
                        "trunk_vlans": [],
                        "shutdown": None,
                    },
                )
                if interface["name"] not in entry["members"]:
                    entry["members"].append(interface["name"])
            continue

        if lowered.startswith("ip route-static "):
            route = parse_route_line(header)
            if route:
                result["static_routes"].append(route)
            continue

        route_lines = [line.strip() for line in block if line.strip().lower().startswith("ip route-static ")]
        if route_lines:
            for route_line in route_lines:
                route = parse_route_line(route_line)
                if route:
                    result["static_routes"].append(route)
            continue

        if header.lower() == "return":
            continue

        result["unparsed_blocks"].append({"header": header, "lines": block[1:]})

    result["aggregations"] = sorted(aggregations.values(), key=lambda item: item["id"])
    return result


def load_input_text(path: str | None) -> tuple[str, str]:
    if path:
        source = str(Path(path).resolve())
        return Path(path).read_text(encoding="utf-8"), source
    if sys.stdin.isatty():
        raise SystemExit("Provide --input or pipe configuration text into stdin.")
    return sys.stdin.read(), "<stdin>"


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse H3C Comware configuration into structured JSON.")
    parser.add_argument("--input", help="Path to a configuration file. Reads stdin when omitted.")
    parser.add_argument("--output", help="Optional output file path.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    config_text, source = load_input_text(args.input)
    parsed = parse_config(config_text, source=source)
    payload = dump_json(parsed, pretty=args.pretty) + "\n"

    if args.output:
        write_text(args.output, payload)
    else:
        sys.stdout.write(payload)


if __name__ == "__main__":
    main()
