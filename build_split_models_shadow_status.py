from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def main() -> None:
    summary = _load_json(SHADOW_DIR / "shadow_summary.json")
    backtest = _load_json(SHADOW_DIR / "split_models_backtest_summary.json")
    drift = _load_json(SHADOW_DIR / "shadow_drift_report.json")
    readiness = _load_json(SHADOW_DIR / "shadow_live_readiness.json")
    transition = _load_json(SHADOW_DIR / "shadow_live_transition_summary.json")
    execution = _load_json(SHADOW_DIR / "shadow_rebalance_execution_summary.json")
    market_summary = _load_csv(SHADOW_DIR / "shadow_rebalance_market_summary.csv")

    trading_book = backtest.get("trading_book", {})

    print(f"baseline_variant={summary.get('baseline_variant')}")
    print(f"live_readiness={readiness.get('live_readiness_verdict')}")
    print(f"health_verdict={summary.get('health_verdict')}")
    print(f"drift_verdict={drift.get('drift_verdict')}")
    print(f"current_holdings={summary.get('current_holdings')}")
    print(f"dominant_sector={summary.get('current_dominant_sector')}")
    print(f"cagr={float(trading_book.get('CAGR', 0.0)):.4f}")
    print(f"mdd={float(trading_book.get('MDD', 0.0)):.4f}")
    print(f"sharpe={float(trading_book.get('Sharpe', 0.0)):.4f}")
    print(f"transition_turnover={float(transition.get('weight_turnover', 0.0)):.6f}")
    print(f"actionable_rows={execution.get('actionable_rows')}")

    for _, row in market_summary.iterrows():
        print(
            f"market_{row['Market']}_{row['ExecutionSide'].lower()}_orders={int(row['OrderCount'])}"
        )


if __name__ == "__main__":
    main()
