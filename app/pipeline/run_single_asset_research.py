from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from app.single_asset import evaluate_single_asset_candidate, get_single_asset_candidates


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run single-asset research candidates for KRW-BTC MVP validation.")
    p.add_argument("--output-dir", type=str, required=True)
    p.add_argument("--lookback-bars", type=int, default=6000)
    p.add_argument("--market", type=str, default="KRW-BTC")
    p.add_argument("--interval", type=str, default="1h")
    return p.parse_args()


def _fetch_upbit_1h_candles(market: str, lookback_bars: int) -> pd.DataFrame:
    unit = 60
    remaining = lookback_bars
    to_cursor: str | None = None
    rows: list[dict] = []

    while remaining > 0:
        count = min(200, remaining)
        params = {"market": market, "count": count}
        if to_cursor:
            params["to"] = to_cursor
        resp = requests.get("https://api.upbit.com/v1/candles/minutes/60", params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        if not payload:
            break
        for item in payload:
            rows.append(
                {
                    "timestamp": pd.Timestamp(item["candle_date_time_kst"]).tz_localize("Asia/Seoul"),
                    "open": float(item["opening_price"]),
                    "high": float(item["high_price"]),
                    "low": float(item["low_price"]),
                    "close": float(item["trade_price"]),
                    "volume": float(item["candle_acc_trade_volume"]),
                }
            )
        oldest = payload[-1]["candle_date_time_utc"] + "Z"
        to_cursor = oldest
        remaining -= len(payload)
        if len(payload) < count:
            break
        time.sleep(0.12)

    candles = pd.DataFrame(rows).drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    return candles


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_single_asset")
    candles = _fetch_upbit_1h_candles(args.market, args.lookback_bars)
    if candles.empty:
        raise SystemExit("no candles fetched")

    candles.to_csv(output_dir / "candles.csv", index=False, encoding="utf-8-sig")

    candidates = [c for c in get_single_asset_candidates() if c["symbol"] == args.market and c["interval"] == args.interval]
    pd.DataFrame(candidates).to_csv(output_dir / "candidate_registry.csv", index=False, encoding="utf-8-sig")

    results_rows = []
    for candidate in candidates:
        result, signal_frame, trade_log = evaluate_single_asset_candidate(candidate, candles, run_id=run_id)
        signal_frame.to_csv(output_dir / f"{candidate['candidate_id']}_signal_frame.csv", index=False, encoding="utf-8-sig")
        trade_log.to_csv(output_dir / f"{candidate['candidate_id']}_trade_log.csv", index=False, encoding="utf-8-sig")
        results_rows.append(
            {
                "run_id": result.run_id,
                "symbol": result.symbol,
                "interval": result.interval,
                "candidate_id": result.candidate_id,
                "candidate_included": int(result.candidate_included),
                "sharpe": result.sharpe,
                "cagr": result.cagr,
                "trades": result.trades,
                "win_rate": result.win_rate,
                "max_drawdown": result.max_drawdown,
                "total_return": result.total_return,
                "pass_fail": result.pass_fail,
                "failure_reason": result.failure_reason,
            }
        )

    results = pd.DataFrame(results_rows)
    results.to_csv(output_dir / "single_asset_results.csv", index=False, encoding="utf-8-sig")

    summary = {
        "run_id": run_id,
        "symbol": args.market,
        "interval": args.interval,
        "candidate_count": int(len(candidates)),
        "results_path": str((output_dir / "single_asset_results.csv").resolve()),
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(results.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

