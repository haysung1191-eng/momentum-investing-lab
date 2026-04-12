from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / 'global_flow_observer' / 'outputs'
MEMO_DIR = ROOT / 'global_flow_observer' / 'memos'
PACKET_ROOT = ROOT / 'global_flow_observer' / 'packets'
CURRENT_MEMO_PATH = ROOT / 'GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO_CURRENT.md'
MEMO_INDEX_PATH = MEMO_DIR / 'memo_index.csv'


def main() -> None:
    regime = pd.read_csv(OUTPUT_DIR / 'current_regime_summary.csv').iloc[0]
    signal_date = str(regime['SignalDate'])
    packet_dir = PACKET_ROOT / signal_date
    packet_dir.mkdir(parents=True, exist_ok=True)
    ledger = pd.read_csv(MEMO_INDEX_PATH, dtype={'SignalDate': str})
    ledger_row = ledger[ledger['SignalDate'] == signal_date].iloc[0]

    files_to_copy = {
        CURRENT_MEMO_PATH: packet_dir / 'monthly_memo.md',
        MEMO_DIR / f'{signal_date}_GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO.md': packet_dir / f'{signal_date}_monthly_memo.md',
        MEMO_DIR / 'memo_index.csv': packet_dir / 'memo_index.csv',
        OUTPUT_DIR / 'top_status_bar.json': packet_dir / 'top_status_bar.json',
        OUTPUT_DIR / 'current_regime_summary.csv': packet_dir / 'current_regime_summary.csv',
        OUTPUT_DIR / 'asset_leadership_table.csv': packet_dir / 'asset_leadership_table.csv',
        OUTPUT_DIR / 'equity_region_rotation.csv': packet_dir / 'equity_region_rotation.csv',
        OUTPUT_DIR / 'real_assets_vs_financial_assets.csv': packet_dir / 'real_assets_vs_financial_assets.csv',
        OUTPUT_DIR / 'change_since_last_month.csv': packet_dir / 'change_since_last_month.csv',
    }

    for src, dst in files_to_copy.items():
        if not src.exists():
            raise FileNotFoundError(f'missing packet input: {src}')
        shutil.copy2(src, dst)

    manifest = {
        'SignalDate': signal_date,
        'PacketDir': str(packet_dir),
        'Files': [dst.name for dst in files_to_copy.values()],
    }
    (packet_dir / 'packet_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    readme = f"""# Global Flow Observer Monthly Packet

- Signal date: {signal_date}
- Regime: {ledger_row['Regime']}
- Strongest asset: {ledger_row['Strongest']}
- Weakest asset: {ledger_row['Weakest']}
- Final monthly verdict: {ledger_row['FinalMonthlyVerdict']}
- Confidence: {ledger_row['Confidence']}

## Open these first

1. `monthly_memo.md`
2. `current_regime_summary.csv`
3. `asset_leadership_table.csv`

## Then use if needed

- `equity_region_rotation.csv`
- `real_assets_vs_financial_assets.csv`
- `change_since_last_month.csv`
- `top_status_bar.json`
- `memo_index.csv`
"""
    (packet_dir / 'README.md').write_text(readme, encoding='utf-8')
    print(str(packet_dir))


if __name__ == '__main__':
    main()
