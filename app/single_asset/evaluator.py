from __future__ import annotations

import importlib
from dataclasses import dataclass

import numpy as np
import pandas as pd


HOURS_PER_YEAR = 24 * 365


@dataclass(frozen=True)
class EvaluationResult:
    run_id: str
    candidate_id: str
    symbol: str
    interval: str
    candidate_included: bool
    sharpe: float
    cagr: float
    trades: int
    win_rate: float
    max_drawdown: float
    total_return: float
    pass_fail: str
    failure_reason: str


def _compute_trade_log(signal_frame: pd.DataFrame) -> pd.DataFrame:
    entries = signal_frame[signal_frame["event"] == "ENTER"][["timestamp", "close"]].reset_index(drop=True)
    exits = signal_frame[signal_frame["event"] == "EXIT"][["timestamp", "close"]].reset_index(drop=True)
    pair_count = min(len(entries), len(exits))
    if pair_count == 0:
        return pd.DataFrame(columns=["entry_time", "entry_price", "exit_time", "exit_price", "trade_return"])
    trades = pd.DataFrame(
        {
            "entry_time": entries.loc[: pair_count - 1, "timestamp"].values,
            "entry_price": entries.loc[: pair_count - 1, "close"].astype(float).values,
            "exit_time": exits.loc[: pair_count - 1, "timestamp"].values,
            "exit_price": exits.loc[: pair_count - 1, "close"].astype(float).values,
        }
    )
    trades["trade_return"] = trades["exit_price"] / trades["entry_price"] - 1.0
    return trades


def evaluate_single_asset_candidate(candidate: dict, candles: pd.DataFrame, run_id: str) -> tuple[EvaluationResult, pd.DataFrame, pd.DataFrame]:
    module = importlib.import_module(candidate["strategy_module"])
    signal_frame = module.build_signal_frame(candles)
    signal_frame["asset_return"] = signal_frame["close"].pct_change().fillna(0.0)
    signal_frame["strategy_return"] = signal_frame["position"].shift(1).fillna(0.0) * signal_frame["asset_return"]
    signal_frame["equity_curve"] = (1.0 + signal_frame["strategy_return"]).cumprod()
    signal_frame["equity_peak"] = signal_frame["equity_curve"].cummax()
    signal_frame["drawdown"] = signal_frame["equity_curve"] / signal_frame["equity_peak"] - 1.0

    rets = signal_frame["strategy_return"]
    mean_ret = float(rets.mean())
    std_ret = float(rets.std(ddof=1)) if len(rets) > 1 else 0.0
    sharpe = (mean_ret / std_ret) * np.sqrt(HOURS_PER_YEAR) if std_ret > 0 else 0.0

    total_return = float(signal_frame["equity_curve"].iloc[-1] - 1.0)
    start_ts = pd.Timestamp(signal_frame["timestamp"].iloc[0])
    end_ts = pd.Timestamp(signal_frame["timestamp"].iloc[-1])
    years = max((end_ts - start_ts).total_seconds() / (365.25 * 24 * 3600), 1e-9)
    cagr = float(signal_frame["equity_curve"].iloc[-1] ** (1.0 / years) - 1.0)
    max_drawdown = float(signal_frame["drawdown"].min())

    trade_log = _compute_trade_log(signal_frame)
    trades = int(len(trade_log))
    win_rate = float((trade_log["trade_return"] > 0).mean()) if trades > 0 else 0.0

    failure_reason = ""
    pass_fail = "PASS"
    if sharpe <= 0:
        pass_fail = "FAIL"
        failure_reason = "Sharpe <= 0 on first research run; kill rule triggered"

    result = EvaluationResult(
        run_id=run_id,
        candidate_id=candidate["candidate_id"],
        symbol=candidate["symbol"],
        interval=candidate["interval"],
        candidate_included=bool(candidate.get("included", False)),
        sharpe=float(sharpe),
        cagr=float(cagr),
        trades=trades,
        win_rate=win_rate,
        max_drawdown=max_drawdown,
        total_return=total_return,
        pass_fail=pass_fail,
        failure_reason=failure_reason,
    )
    return result, signal_frame, trade_log

