#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import DEFAULT_PROMPT_REGEX, dump_json, get_password, open_session, run_command, utc_now, write_json, write_text


def read_commands(commands_file: str | None, extra_commands: list[str] | None) -> list[str]:
    commands: list[str] = []
    if commands_file:
        for raw_line in Path(commands_file).read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            commands.append(line)
    commands.extend(extra_commands or [])
    return commands


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply H3C commands only after explicit confirmation.")
    parser.add_argument("--host", required=True, help="Device hostname or IP.")
    parser.add_argument("--username", required=True, help="Login username.")
    parser.add_argument("--password", help="Login password. Defaults to env H3C_PASSWORD or interactive prompt.")
    parser.add_argument("--password-env", default="H3C_PASSWORD", help="Environment variable used for password fallback.")
    parser.add_argument("--protocol", choices=["ssh", "telnet"], default="ssh", help="Connection protocol.")
    parser.add_argument("--port", type=int, help="Override destination port.")
    parser.add_argument("--timeout", type=int, default=15, help="Per-command timeout in seconds.")
    parser.add_argument("--prompt-regex", default=DEFAULT_PROMPT_REGEX, help="Prompt detection regex.")
    parser.add_argument("--commands-file", help="Path to a newline-delimited commands file.")
    parser.add_argument("--command", action="append", dest="commands", help="Additional command to run. Can repeat.")
    parser.add_argument("--verify-command", action="append", dest="verify_commands", help="Optional verification command to run after the change.")
    parser.add_argument("--log-dir", default="./h3c-apply-logs", help="Directory used for session transcripts and JSON results.")
    parser.add_argument("--confirm-execute", action="store_true", help="Required flag. Without it, the script exits without connecting.")
    args = parser.parse_args()

    commands = read_commands(args.commands_file, args.commands)
    if not commands:
        raise SystemExit("Provide --commands-file or at least one --command.")

    preview = {
        "metadata": {
            "generated_at": utc_now(),
            "host": args.host,
            "protocol": args.protocol,
            "port": args.port or (22 if args.protocol == "ssh" else 23),
            "confirmed": bool(args.confirm_execute),
        },
        "commands": commands,
        "verify_commands": args.verify_commands or [],
    }

    if not args.confirm_execute:
        sys.stderr.write("Refusing to execute without --confirm-execute. Preview follows on stdout.\n")
        sys.stdout.write(dump_json(preview, pretty=True) + "\n")
        raise SystemExit(2)

    password = get_password(args.password, password_env=args.password_env)
    timestamp = utc_now().replace(":", "-")
    log_dir = Path(args.log_dir) / f"{args.host}-{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = log_dir / "session.log"
    commands_path = log_dir / "commands.txt"
    result_path = log_dir / "result.json"

    write_text(commands_path, "\n".join(commands) + "\n")

    session = open_session(
        host=args.host,
        username=args.username,
        password=password,
        protocol=args.protocol,
        port=args.port,
        timeout=args.timeout,
        prompt_regex=args.prompt_regex,
        logfile_path=str(transcript_path),
    )

    command_results = []
    verify_results = []

    try:
        for command in commands:
            output = run_command(session, command, prompt_regex=args.prompt_regex, timeout=args.timeout, auto_confirm=False)
            command_results.append({"command": command, "output": output})

        for command in args.verify_commands or []:
            output = run_command(session, command, prompt_regex=args.prompt_regex, timeout=args.timeout, auto_confirm=False)
            verify_results.append({"command": command, "output": output})
    finally:
        session.close(force=True)

    result = {
        "metadata": {
            "generated_at": utc_now(),
            "host": args.host,
            "protocol": args.protocol,
            "port": args.port or (22 if args.protocol == "ssh" else 23),
            "log_dir": str(log_dir.resolve()),
            "transcript": str(transcript_path.resolve()),
            "commands_file": str(commands_path.resolve()),
        },
        "command_results": command_results,
        "verify_results": verify_results,
    }
    write_json(result_path, result, pretty=True)
    sys.stdout.write(dump_json(result, pretty=True) + "\n")


if __name__ == "__main__":
    main()
