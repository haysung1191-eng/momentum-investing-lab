from __future__ import annotations

import pandas as pd


CANDIDATE_ID = "krw_btc_1h_bb20_rsi14_mr_v1"
SYMBOL = "KRW-BTC"
INTERVAL = "1h"


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, pd.NA)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(100.0)


def build_signal_frame(candles: pd.DataFrame) -> pd.DataFrame:
    df = candles.copy()
    if "close" not in df.columns:
        raise ValueError("candles must include close")
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    if df["close"].isna().any():
        raise ValueError("close contains NaN")

    df["sma20"] = df["close"].rolling(20, min_periods=20).mean()
    rolling_std = df["close"].rolling(20, min_periods=20).std(ddof=0)
    df["lower_bb20_2"] = df["sma20"] - (2.0 * rolling_std)
    df["rsi14"] = _compute_rsi(df["close"], period=14)
    df["entry_condition"] = (df["close"] < df["lower_bb20_2"]) & (df["rsi14"] < 30.0)
    df["exit_condition"] = df["close"] >= df["sma20"]

    in_position = False
    positions: list[int] = []
    events: list[str] = []
    entry_prices: list[float | None] = []
    active_entry_price: float | None = None

    for row in df.itertuples():
        event = ""
        if not in_position and bool(row.entry_condition):
            in_position = True
            active_entry_price = float(row.close)
            event = "ENTER"
        elif in_position and bool(row.exit_condition):
            in_position = False
            event = "EXIT"
            active_entry_price = None
        positions.append(1 if in_position else 0)
        events.append(event)
        entry_prices.append(active_entry_price)

    df["position"] = positions
    df["event"] = events
    df["active_entry_price"] = entry_prices
    return df

