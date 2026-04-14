from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _build_status_payload() -> dict[str, object]:
    summary = _load_json(SHADOW_DIR / "shadow_summary.json")
    backtest = _load_json(SHADOW_DIR / "split_models_backtest_summary.json")
    drift = _load_json(SHADOW_DIR / "shadow_drift_report.json")
    readiness = _load_json(SHADOW_DIR / "shadow_live_readiness.json")
    transition = _load_json(SHADOW_DIR / "shadow_live_transition_summary.json")
    execution = _load_json(SHADOW_DIR / "shadow_rebalance_execution_summary.json")
    market_summary = _load_csv(SHADOW_DIR / "shadow_rebalance_market_summary.csv")

    trading_book = backtest.get("trading_book", {})
    payload: dict[str, object] = {
        "baseline_variant": summary.get("baseline_variant"),
        "live_readiness": readiness.get("live_readiness_verdict"),
        "health_verdict": summary.get("health_verdict"),
        "drift_verdict": drift.get("drift_verdict"),
        "current_holdings": summary.get("current_holdings"),
        "dominant_sector": summary.get("current_dominant_sector"),
        "cagr": float(trading_book.get("CAGR", 0.0)),
        "mdd": float(trading_book.get("MDD", 0.0)),
        "sharpe": float(trading_book.get("Sharpe", 0.0)),
        "transition_turnover": float(transition.get("weight_turnover", 0.0)),
        "actionable_rows": execution.get("actionable_rows"),
    }
    for _, row in market_summary.iterrows():
        payload[f"market_{row['Market']}_{row['ExecutionSide'].lower()}_orders"] = int(row["OrderCount"])
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    payload = _build_status_payload()
    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(f"baseline_variant={payload['baseline_variant']}")
    print(f"live_readiness={payload['live_readiness']}")
    print(f"health_verdict={payload['health_verdict']}")
    print(f"drift_verdict={payload['drift_verdict']}")
    print(f"current_holdings={payload['current_holdings']}")
    print(f"dominant_sector={payload['dominant_sector']}")
    print(f"cagr={float(payload['cagr']):.4f}")
    print(f"mdd={float(payload['mdd']):.4f}")
    print(f"sharpe={float(payload['sharpe']):.4f}")
    print(f"transition_turnover={float(payload['transition_turnover']):.6f}")
    print(f"actionable_rows={payload['actionable_rows']}")

    for key, value in payload.items():
        if key.startswith("market_"):
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
