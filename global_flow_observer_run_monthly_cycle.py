from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_SCRIPT = ROOT / 'global_flow_observer' / 'scripts' / 'build_observer_state.py'
MEMO_SCRIPT = ROOT / 'global_flow_observer_generate_monthly_memo.py'
PACKET_SCRIPT = ROOT / 'global_flow_observer_package_monthly_packet.py'


def run(script: Path) -> str:
    result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def main() -> None:
    build_out = run(BUILD_SCRIPT)
    memo_out = run(MEMO_SCRIPT)
    packet_out = run(PACKET_SCRIPT)
    print(f'build={build_out}')
    print(f'memo_archive={memo_out}')
    print(f'packet_dir={packet_out}')


if __name__ == '__main__':
    main()
