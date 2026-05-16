#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any

from build_change_plan import build_plan, normalize_state
from common import DEFAULT_PROMPT_REGEX, dump_json, get_password, safe_path_component, utc_now, write_json, write_text
from device_collect import DEFAULT_COMMANDS, collect_device_state
from parse_config import parse_config


PLAN_ONLY_VLAN_CANDIDATES = [4093, 3999, 2999, 1999, 999]


def default_output_dir(host: str) -> Path:
    timestamp = utc_now().replace(":", "-")
    return Path("/tmp/h3c-real-check") / f"{safe_path_component(host)}-{timestamp}"


def choose_plan_only_vlan(existing_vlans: set[int]) -> int:
    for candidate in PLAN_ONLY_VLAN_CANDIDATES:
        if candidate not in existing_vlans:
            return candidate
    candidate = max(existing_vlans or {100}) + 1
    return candidate if candidate <= 4094 else 4093


def build_plan_only_target(parsed: dict[str, Any]) -> tuple[dict[str, Any], int]:
    target = copy.deepcopy(parsed)
    existing_vlans = {int(vlan["id"]) for vlan in target.get("vlans", []) if vlan.get("id") is not None}
    sample_vlan = choose_plan_only_vlan(existing_vlans)
    target.setdefault("vlans", []).append({"id": sample_vlan, "name": "PLAN-ONLY-VALIDATION", "description": None})
    target["vlans"] = sorted(target["vlans"], key=lambda item: int(item["id"]))
    return target, sample_vlan


def parse_is_basic_pass(parsed: dict[str, Any]) -> bool:
    non_empty_categories = 0
    if parsed.get("vlans"):
        non_empty_categories += 1
    if parsed.get("interfaces"):
        non_empty_categories += 1
    if parsed.get("static_routes"):
        non_empty_categories += 1
    return parsed.get("version_family") in {"comware5", "comware7"} and non_empty_categories >= 2


def all_standard_commands_ok(collect: dict[str, Any]) -> bool:
    statuses = {entry["command"]: entry["status"] for entry in collect.get("command_results", [])}
    return all(statuses.get(command) == "ok" for command in DEFAULT_COMMANDS)


def recommended_for_next_phase(collect: dict[str, Any], parsed: dict[str, Any]) -> bool:
    return all_standard_commands_ok(collect) and parse_is_basic_pass(parsed)


def write_report(path: Path, content: str) -> None:
    write_text(path, content.strip() + "\n")


def render_failure_report(collect: dict[str, Any]) -> str:
    attempts = collect.get("connection_attempts", [])
    lines = [
        "# 华三只读验证报告",
        "",
        "## 结论",
        "- 状态：连接失败",
        "- 建议进入下一阶段实验设备小变更验证：否",
        "",
        "## 连接失败详情",
    ]
    for attempt in attempts:
        lines.append(f"- `{attempt.get('protocol')}`:{attempt.get('port')} -> {attempt.get('error', 'unknown error')}")
    if not attempts:
        lines.append("- 未产生有效连接尝试记录")
    return "\n".join(lines)


def render_success_report(
    collect: dict[str, Any],
    parsed: dict[str, Any],
    plan: dict[str, Any],
    sample_vlan: int,
) -> str:
    command_lines = []
    for entry in collect.get("command_results", []):
        if entry["status"] == "ok":
            command_lines.append(f"- `{entry['command']}` -> ok")
        else:
            command_lines.append(f"- `{entry['command']}` -> error: {entry['error']}")

    parse_lines = [
        f"- 版本识别：`{parsed.get('version_family')}`",
        f"- VLAN 数：`{len(parsed.get('vlans', []))}`",
        f"- 接口数：`{len(parsed.get('interfaces', []))}`",
        f"- 聚合数：`{len(parsed.get('aggregations', []))}`",
        f"- SVI 数：`{len(parsed.get('svis', []))}`",
        f"- 静态路由数：`{len(parsed.get('static_routes', []))}`",
        f"- 未识别块数：`{len(parsed.get('unparsed_blocks', []))}`",
    ]

    warnings = collect.get("warnings") or []
    risk_lines = [f"- {item}" for item in plan.get("risks", [])] or ["- 无额外风险提示"]
    warning_lines = [f"- {item}" for item in warnings] or ["- 无"]
    allow_next = recommended_for_next_phase(collect, parsed)

    lines = [
        "# 华三只读验证报告",
        "",
        "## 结论",
        f"- 状态：{'通过' if allow_next else '部分通过'}",
        f"- 选用协议：`{collect['metadata'].get('selected_protocol')}`",
        f"- 计划演练测试 VLAN：`{sample_vlan}` / `PLAN-ONLY-VALIDATION`",
        f"- 建议进入下一阶段实验设备小变更验证：{'是' if allow_next else '否'}",
        "",
        "## 采集结果",
        *command_lines,
        "",
        "## 解析结果",
        *parse_lines,
        "",
        "## 风险提示",
        *risk_lines,
        "",
        "## 警告",
        *warning_lines,
        "",
        "## 产物",
    ]
    for label, file_path in sorted((collect.get("files") or {}).items()):
        lines.append(f"- `{label}`: `{file_path}`")
    lines.extend(
        [
            f"- `parsed`: `{collect['files'].get('parsed', '')}`" if collect.get("files", {}).get("parsed") else "",
            f"- `plan`: `{collect['files'].get('plan', '')}`" if collect.get("files", {}).get("plan") else "",
            f"- `report`: `{collect['files'].get('report', '')}`" if collect.get("files", {}).get("report") else "",
        ]
    )
    return "\n".join(line for line in lines if line != "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a read-only validation workflow for a real H3C switch.")
    parser.add_argument("--host", required=True, help="Device hostname or IP.")
    parser.add_argument("--username", required=True, help="Login username.")
    parser.add_argument("--password", help="Login password. Defaults to env H3C_PASSWORD or interactive prompt.")
    parser.add_argument("--password-env", default="H3C_PASSWORD", help="Environment variable used for password fallback.")
    parser.add_argument("--protocol", choices=["ssh", "telnet", "auto"], default="auto", help="Connection protocol selection.")
    parser.add_argument("--port", type=int, help="Override destination port for single-protocol runs.")
    parser.add_argument("--ssh-port", type=int, help="Override SSH port when using protocol auto.")
    parser.add_argument("--telnet-port", type=int, help="Override Telnet port when using protocol auto.")
    parser.add_argument("--timeout", type=int, default=15, help="Per-command timeout in seconds.")
    parser.add_argument("--prompt-regex", default=DEFAULT_PROMPT_REGEX, help="Prompt detection regex.")
    parser.add_argument("--output-dir", help="Directory for collect.json, current.cfg, parsed.json, plan.json, and report.md.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir(args.host)
    output_dir.mkdir(parents=True, exist_ok=True)
    password = get_password(args.password, password_env=args.password_env)

    success, collect = collect_device_state(
        host=args.host,
        username=args.username,
        password=password,
        protocol=args.protocol,
        port=args.port,
        ssh_port=args.ssh_port,
        telnet_port=args.telnet_port,
        timeout=args.timeout,
        prompt_regex=args.prompt_regex,
        commands=list(DEFAULT_COMMANDS),
        output_dir=str(output_dir),
    )

    collect_file = output_dir / "collect.json"
    if not collect_file.exists():
        write_json(collect_file, collect, pretty=True)
    collect.setdefault("files", {})["collect"] = str(collect_file.resolve())

    if not success:
        report_path = output_dir / "report.md"
        write_report(report_path, render_failure_report(collect))
        collect["files"]["report"] = str(report_path.resolve())
        write_json(collect_file, collect, pretty=True)
        sys.stderr.write(f"Connection failed for {args.host}. See {report_path}\n")
        raise SystemExit(2)

    current_config = collect.get("results", {}).get("display current-configuration", "")
    current_cfg_path = output_dir / "current.cfg"
    if not current_cfg_path.exists():
        write_text(current_cfg_path, current_config + ("\n" if current_config else ""))
    collect["files"]["current_config"] = str(current_cfg_path.resolve())

    parsed = parse_config(current_config, source=str(current_cfg_path.resolve()))
    parsed_path = output_dir / "parsed.json"
    write_json(parsed_path, parsed, pretty=True)
    collect["files"]["parsed"] = str(parsed_path.resolve())

    target, sample_vlan = build_plan_only_target(parsed)
    plan_input = {"current": parsed, "target": target}
    plan_input_path = output_dir / "plan-input.json"
    write_json(plan_input_path, plan_input, pretty=True)
    collect["files"]["plan_input"] = str(plan_input_path.resolve())

    plan = build_plan(normalize_state(parsed), normalize_state(target))
    plan_path = output_dir / "plan.json"
    write_json(plan_path, plan, pretty=True)
    collect["files"]["plan"] = str(plan_path.resolve())

    report_path = output_dir / "report.md"
    write_report(report_path, render_success_report(collect, parsed, plan, sample_vlan))
    collect["files"]["report"] = str(report_path.resolve())
    write_json(collect_file, collect, pretty=True)

    summary = {
        "host": args.host,
        "selected_protocol": collect["metadata"].get("selected_protocol"),
        "output_dir": str(output_dir.resolve()),
        "files": collect["files"],
        "version_family": parsed.get("version_family"),
        "plan_only_vlan": sample_vlan,
        "next_phase_recommended": recommended_for_next_phase(collect, parsed),
    }
    sys.stdout.write(dump_json(summary, pretty=True) + "\n")


if __name__ == "__main__":
    main()
