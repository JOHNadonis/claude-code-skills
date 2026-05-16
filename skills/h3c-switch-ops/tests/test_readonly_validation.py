from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILL_DIR = Path('/Users/whc/.codex/skills/h3c-switch-ops')
SCRIPT = SKILL_DIR / 'scripts' / 'readonly_validation.py'


class ReadonlyValidationTests(unittest.TestCase):
    def make_executable(self, path: Path, content: str) -> None:
        path.write_text(content, encoding='utf-8')
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def test_falls_back_to_telnet_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bin_dir = temp_path / 'bin'
            bin_dir.mkdir()

            self.make_executable(
                bin_dir / 'ssh',
                textwrap.dedent(
                    '''#!/usr/bin/env python3
import sys
sys.stderr.write('ssh: handshake failed\\n')
raise SystemExit(255)
'''
                ),
            )
            self.make_executable(
                bin_dir / 'telnet',
                textwrap.dedent(
                    '''#!/usr/bin/env python3
import sys
PROMPT_USER = "<H3C-MOCK>"
sys.stdout.write("Username:")
sys.stdout.flush()
if not sys.stdin.readline():
    raise SystemExit(1)
sys.stdout.write("Password:")
sys.stdout.flush()
if not sys.stdin.readline():
    raise SystemExit(1)
sys.stdout.write(PROMPT_USER)
sys.stdout.flush()
while True:
    line = sys.stdin.readline()
    if not line:
        break
    command = line.strip()
    if command == 'screen-length disable':
        sys.stdout.write("\\nInfo: screen length disabled.\\n")
    elif command == 'display version':
        sys.stdout.write("\\nH3C Comware Software, Version 5.20\\n")
    elif command == 'display current-configuration':
        sys.stdout.write("\\nsysname H3C-OLD\\nvlan 10\\n name OFFICE\\ninterface GigabitEthernet1/0/1\\n port link-type access\\n port access vlan 10\\nip route-static 0.0.0.0 0.0.0.0 192.168.1.1\\n")
    elif command == 'display vlan':
        sys.stdout.write("\\nVLAN 10 OFFICE\\n")
    elif command == 'display interface brief':
        sys.stdout.write("\\nGE1/0/1 up up\\n")
    elif command == 'display link-aggregation summary':
        sys.stdout.write("\\nNo aggregation\\n")
    else:
        sys.stdout.write(f"\\nExecuted: {command}\\n")
    sys.stdout.write(PROMPT_USER)
    sys.stdout.flush()
'''
                ),
            )

            output_dir = temp_path / 'out'
            env = os.environ.copy()
            env['PATH'] = f"{bin_dir}:{env.get('PATH', '')}"
            env['H3C_PASSWORD'] = 'secret'

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    '--host',
                    '198.51.100.10',
                    '--username',
                    'admin',
                    '--output-dir',
                    str(output_dir),
                ],
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            collect = json.loads((output_dir / 'collect.json').read_text(encoding='utf-8'))
            plan = json.loads((output_dir / 'plan.json').read_text(encoding='utf-8'))
            report = (output_dir / 'report.md').read_text(encoding='utf-8')

            self.assertEqual(collect['metadata']['selected_protocol'], 'telnet')
            self.assertTrue((output_dir / 'current.cfg').exists())
            self.assertTrue((output_dir / 'parsed.json').exists())
            self.assertIn('PLAN-ONLY-VALIDATION', '\n'.join(plan['target_config']))
            self.assertIn('telnet', report.lower())

    def test_writes_failure_report_when_both_protocols_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bin_dir = temp_path / 'bin'
            bin_dir.mkdir()

            failing_script = textwrap.dedent(
                '''#!/usr/bin/env python3
import sys
sys.stderr.write('connection failed\\n')
raise SystemExit(1)
'''
            )
            self.make_executable(bin_dir / 'ssh', failing_script)
            self.make_executable(bin_dir / 'telnet', failing_script)

            output_dir = temp_path / 'out'
            env = os.environ.copy()
            env['PATH'] = f"{bin_dir}:{env.get('PATH', '')}"
            env['H3C_PASSWORD'] = 'secret'

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    '--host',
                    '203.0.113.20',
                    '--username',
                    'admin',
                    '--output-dir',
                    str(output_dir),
                ],
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            report = (output_dir / 'report.md').read_text(encoding='utf-8')
            self.assertIn('连接失败', report)
            self.assertFalse((output_dir / 'parsed.json').exists())


if __name__ == '__main__':
    unittest.main()
