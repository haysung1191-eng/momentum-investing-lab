from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_transition_diff(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    numeric_cols = ["BaselineWeight", "CandidateWeight", "WeightDelta"]
    for col in numeric_cols:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    return frame


def _format_order_sheet(frame: pd.DataFrame, total_capital: float | None) -> pd.DataFrame:
    out = frame.copy()
    out["TargetWeightPct"] = out["CandidateWeight"] * 100.0
    out["DeltaWeightPct"] = out["WeightDelta"] * 100.0
    out["ExecutionSide"] = out["WeightDelta"].map(lambda v: "BUY" if v > 0 else ("SELL" if v < 0 else "HOLD"))

    if total_capital is not None:
        out["TargetNotional"] = out["CandidateWeight"] * total_capital
        out["DeltaNotional"] = out["WeightDelta"] * total_capital
    else:
        out["TargetNotional"] = pd.NA
        out["DeltaNotional"] = pd.NA

    out["OrderPriority"] = out["ExecutionSide"].map({"SELL": 0, "BUY": 1, "HOLD": 2}).fillna(9)
    out = out.sort_values(["OrderPriority", "Market", "Symbol"], ascending=[True, True, True]).reset_index(drop=True)
    return out[
        [
            "ExecutionSide",
            "Action",
            "Market",
            "AssetType",
            "Symbol",
            "Name",
            "Sector",
            "BaselineWeight",
            "CandidateWeight",
            "WeightDelta",
            "TargetWeightPct",
            "DeltaWeightPct",
            "TargetNotional",
            "DeltaNotional",
        ]
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transition-diff", default=str(SHADOW_DIR / "shadow_live_transition_diff.csv"))
    parser.add_argument("--output-path", default=str(SHADOW_DIR / "shadow_rebalance_orders.csv"))
    parser.add_argument("--total-capital", type=float, default=None)
    args = parser.parse_args()

    transition_diff = _load_transition_diff(Path(args.transition_diff))
    orders = _format_order_sheet(transition_diff, args.total_capital)
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    orders.to_csv(output_path, index=False, encoding="utf-8-sig")

    actionable = orders[orders["ExecutionSide"] != "HOLD"].copy()
    print(f"orders_path={output_path}")
    print(f"actionable_rows={len(actionable)}")
    if not actionable.empty:
        sell_count = int((actionable["ExecutionSide"] == "SELL").sum())
        buy_count = int((actionable["ExecutionSide"] == "BUY").sum())
        print(f"sells={sell_count}")
        print(f"buys={buy_count}")


if __name__ == "__main__":
    main()
