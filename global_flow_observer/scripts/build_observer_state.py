import json
from pathlib import Path

import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data" / "prices"
OUTPUT_DIR = ROOT / "outputs"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> tuple[list[dict], dict, dict]:
    watchlist_cfg = read_json(CONFIG_DIR / "watchlist.json")["watchlist"]
    baskets_cfg = read_json(CONFIG_DIR / "baskets.json")
    regime_cfg = read_json(CONFIG_DIR / "regime_rules.json")
    return watchlist_cfg, baskets_cfg, regime_cfg


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "close", "volume"])
    out = df.copy()
    if "date" not in out.columns:
        out = out.reset_index()
    out = out.rename(columns={"Date": "date", "index": "date", "Close": "close", "Volume": "volume"})
    out = out.loc[:, ~out.columns.duplicated()].copy()
    lower = {c.lower(): c for c in out.columns}
    if "date" not in out.columns and "date" in lower:
        out = out.rename(columns={lower["date"]: "date"})
    if "close" not in out.columns and "close" in lower:
        out = out.rename(columns={lower["close"]: "close"})
    if "volume" not in out.columns and "volume" in lower:
        out = out.rename(columns={lower["volume"]: "volume"})
    out = out[["date", "close", "volume"]].copy()
    out["date"] = pd.to_datetime(out["date"])
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(0.0)
    out = out.dropna(subset=["date", "close"])
    out = out[out["close"] > 0].sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    return out


def batch_download(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    out: dict[str, pd.DataFrame] = {}
    if raw.empty:
        return out
    if isinstance(raw.columns, pd.MultiIndex):
        for ticker in tickers:
            if ticker in raw.columns.get_level_values(0):
                out[ticker] = normalize_frame(raw[ticker])
    elif len(tickers) == 1:
        out[tickers[0]] = normalize_frame(raw)
    return out


def sync_prices(watchlist_cfg: list[dict], start: str, end: str) -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    tickers = [row["ticker"] for row in watchlist_cfg]
    downloaded = batch_download(tickers, start, end)
    for row in watchlist_cfg:
        ticker = row["ticker"]
        df = downloaded.get(ticker, pd.DataFrame(columns=["date", "close", "volume"]))
        path = DATA_DIR / f"{ticker}.csv.gz"
        if df.empty:
            rows.append(
                {
                    "Ticker": ticker,
                    "Label": row["label"],
                    "Status": "EMPTY",
                    "Bars": 0,
                    "FirstDate": "",
                    "LastDate": "",
                    "DuplicateDates": 0,
                    "InvalidCloses": 0,
                }
            )
            continue
        invalid_closes = int((pd.to_numeric(df["close"], errors="coerce") <= 0).fillna(True).sum())
        duplicate_dates = int(df["date"].duplicated().sum())
        df.to_csv(path, index=False, compression="gzip", encoding="utf-8-sig")
        rows.append(
            {
                "Ticker": ticker,
                "Label": row["label"],
                "Status": "OK",
                "Bars": int(len(df)),
                "FirstDate": str(df["date"].iloc[0].date()),
                "LastDate": str(df["date"].iloc[-1].date()),
                "DuplicateDates": duplicate_dates,
                "InvalidCloses": invalid_closes,
            }
        )
    coverage = pd.DataFrame(rows)
    coverage.to_csv(OUTPUT_DIR / "price_sync_validation.csv", index=False, encoding="utf-8-sig")
    return coverage


def load_close_matrix(watchlist_cfg: list[dict]) -> tuple[pd.DataFrame, list[str]]:
    issues: list[str] = []
    series = []
    for row in watchlist_cfg:
        ticker = row["ticker"]
        path = DATA_DIR / f"{ticker}.csv.gz"
        if not path.exists():
            issues.append(f"missing price file: {ticker}")
            continue
        df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
        df = normalize_frame(df)
        if df.empty:
            issues.append(f"empty price file: {ticker}")
            continue
        if df["date"].duplicated().any():
            issues.append(f"duplicate dates: {ticker}")
        if (df["close"] <= 0).any():
            issues.append(f"invalid closes: {ticker}")
        series.append(pd.Series(df["close"].values, index=pd.to_datetime(df["date"]), name=ticker))
    close = pd.concat(series, axis=1).sort_index() if series else pd.DataFrame()
    return close, issues


def compute_month_end(close: pd.DataFrame, tickers: list[str]) -> tuple[pd.DataFrame, pd.Timestamp, list[str]]:
    issues: list[str] = []
    common = close[tickers].dropna(how="any").copy()
    if common.empty:
        return pd.DataFrame(), pd.NaT, ["no fully populated common date matrix"]
    month_end = common.groupby(common.index.to_period("M")).tail(1).copy()
    latest_common = pd.Timestamp(common.index.max())
    calendar_month_end = pd.Timestamp(latest_common.to_period("M").end_time.normalize())
    if latest_common.normalize() < calendar_month_end.normalize():
        month_end = month_end[month_end.index.to_period("M") < latest_common.to_period("M")].copy()
    if month_end.empty:
        return month_end, pd.NaT, ["no completed month-end rows"]
    latest_month_end = pd.Timestamp(month_end.index.max())
    month_mask = common.index.to_period("M") == latest_month_end.to_period("M")
    expected = pd.Timestamp(common.index[month_mask].max())
    if latest_month_end != expected:
        issues.append("latest month-end not detected correctly")
    return month_end.sort_index(), latest_month_end, issues


def compute_return_table(month_end: pd.DataFrame, signal_date: pd.Timestamp) -> pd.DataFrame:
    pos = month_end.index.get_loc(signal_date)
    rows = []
    for ticker in month_end.columns:
        row = {"SignalDate": signal_date.strftime("%Y-%m-%d"), "Ticker": ticker}
        for label, months in [("R1M", 1), ("R3M", 3), ("R6M", 6), ("R12M", 12)]:
            row[label] = float(month_end.iloc[pos][ticker] / month_end.iloc[pos - months][ticker] - 1.0)
        rows.append(row)
    return pd.DataFrame(rows)


def compute_history_tables(month_end: pd.DataFrame, baskets: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    history_returns: list[pd.DataFrame] = []
    regime_rows: list[dict] = []
    for pos in range(12, len(month_end)):
        signal_date = pd.Timestamp(month_end.index[pos])
        return_table = compute_return_table(month_end, signal_date)
        regime_label, regime_metrics = compute_regime(return_table, baskets)
        leadership = return_table.sort_values(["R3M", "Ticker"], ascending=[False, True]).reset_index(drop=True)
        leadership["Rank3M"] = range(1, len(leadership) + 1)
        history_returns.append(leadership.copy())
        regime_rows.append(
            {
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "Regime": regime_label,
                "RiskBasket3M": regime_metrics["risk_basket"],
                "DefenseBasket3M": regime_metrics["defense_basket"],
                "RiskVsDefenseSpread3M": regime_metrics["risk_basket"] - regime_metrics["defense_basket"],
                "RealAssetsStrength3M": regime_metrics["real_assets_strength"],
                "FinancialAssetsStrength3M": regime_metrics["financial_assets_strength"],
                "RealVsFinancialSpread3M": regime_metrics["real_assets_strength"] - regime_metrics["financial_assets_strength"],
                "DurationStrength3M": regime_metrics["duration_strength"],
                "TopLeader3M": leadership.iloc[0]["Ticker"],
                "TopLaggard3M": leadership.iloc[-1]["Ticker"],
            }
        )
    history_df = pd.concat(history_returns, ignore_index=True) if history_returns else pd.DataFrame()
    regime_history_df = pd.DataFrame(regime_rows)
    return history_df, regime_history_df


def basket_mean(return_table: pd.DataFrame, basket: list[str], col: str) -> float:
    return float(return_table[return_table["Ticker"].isin(basket)][col].mean())


def compute_regime(return_table: pd.DataFrame, baskets: dict) -> tuple[str, dict]:
    lookup = return_table.set_index("Ticker")
    metrics = {
        "risk_basket": basket_mean(return_table, baskets["risk_basket"], "R3M"),
        "defense_basket": basket_mean(return_table, baskets["defense_basket"], "R3M"),
        "duration_strength": basket_mean(return_table, baskets["duration_strength"], "R3M"),
        "real_assets_strength": basket_mean(return_table, baskets["real_assets_strength"], "R3M"),
        "financial_assets_strength": basket_mean(return_table, baskets["financial_assets_strength"], "R3M"),
        "SPY": float(lookup.loc["SPY", "R3M"]),
        "IEF": float(lookup.loc["IEF", "R3M"]),
        "TLT": float(lookup.loc["TLT", "R3M"]),
        "HYG": float(lookup.loc["HYG", "R3M"]),
        "GLD": float(lookup.loc["GLD", "R3M"]),
        "PDBC": float(lookup.loc["PDBC", "R3M"]),
    }
    if metrics["risk_basket"] > metrics["defense_basket"] and metrics["SPY"] > metrics["IEF"] and metrics["HYG"] > metrics["IEF"]:
        return "Risk-On", metrics
    if metrics["defense_basket"] > metrics["risk_basket"] and metrics["IEF"] > metrics["SPY"] and metrics["TLT"] > metrics["HYG"]:
        return "Risk-Off", metrics
    if metrics["real_assets_strength"] > metrics["defense_basket"] and metrics["PDBC"] > metrics["IEF"] and metrics["GLD"] > metrics["IEF"]:
        return "Inflation Tilt", metrics
    if metrics["duration_strength"] > metrics["risk_basket"] and metrics["TLT"] > metrics["SPY"] and metrics["IEF"] > metrics["HYG"]:
        return "Duration Bid", metrics
    return "Mixed", metrics


def write_outputs(
    signal_date: pd.Timestamp,
    return_table: pd.DataFrame,
    regime_label: str,
    regime_metrics: dict,
    baskets: dict,
    history_table: pd.DataFrame,
    regime_history: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    leadership = return_table.sort_values(["R3M", "Ticker"], ascending=[False, True]).reset_index(drop=True)
    leadership["Rank3M"] = range(1, len(leadership) + 1)

    previous_signal = pd.Timestamp(return_table["SignalDate"].iloc[0])
    prev_table = pd.read_csv(OUTPUT_DIR / "_previous_return_table.csv") if (OUTPUT_DIR / "_previous_return_table.csv").exists() else pd.DataFrame()
    if not prev_table.empty:
        prev_rank = prev_table.sort_values(["R3M", "Ticker"], ascending=[False, True]).reset_index(drop=True)[["Ticker"]].copy()
        prev_rank["PriorRank3M"] = range(1, len(prev_rank) + 1)
    else:
        prev_rank = leadership[["Ticker"]].copy()
        prev_rank["PriorRank3M"] = pd.NA

    change = leadership[["Ticker", "Rank3M"]].merge(prev_rank, on="Ticker", how="left")
    change["RankChange"] = change["PriorRank3M"] - change["Rank3M"]

    top_status = {
        "SignalDate": signal_date.strftime("%Y-%m-%d"),
        "Regime": regime_label,
        "Top3Leaders3M": leadership.head(3)[["Ticker", "R3M"]].to_dict(orient="records"),
        "Top3Laggards3M": leadership.tail(3).sort_values("R3M")[["Ticker", "R3M"]].to_dict(orient="records"),
        "RiskVsDefenseSpread3M": regime_metrics["risk_basket"] - regime_metrics["defense_basket"],
    }
    (OUTPUT_DIR / "top_status_bar.json").write_text(json.dumps(top_status, indent=2), encoding="utf-8")

    regime_summary = pd.DataFrame(
        [
            {
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "Regime": regime_label,
                "RiskBasket3M": regime_metrics["risk_basket"],
                "DefenseBasket3M": regime_metrics["defense_basket"],
                "DurationStrength3M": regime_metrics["duration_strength"],
                "RealAssetsStrength3M": regime_metrics["real_assets_strength"],
                "FinancialAssetsStrength3M": regime_metrics["financial_assets_strength"],
            }
        ]
    )
    regime_summary.to_csv(OUTPUT_DIR / "current_regime_summary.csv", index=False, encoding="utf-8-sig")

    leadership[["SignalDate", "Ticker", "R1M", "R3M", "R6M", "R12M", "Rank3M"]].to_csv(
        OUTPUT_DIR / "asset_leadership_table.csv", index=False, encoding="utf-8-sig"
    )

    risk_vs_defense = pd.DataFrame(
        [
            {
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "RiskBasket3M": regime_metrics["risk_basket"],
                "DefenseBasket3M": regime_metrics["defense_basket"],
                "Spread3M": regime_metrics["risk_basket"] - regime_metrics["defense_basket"],
            }
        ]
    )
    risk_vs_defense.to_csv(OUTPUT_DIR / "risk_vs_defense.csv", index=False, encoding="utf-8-sig")

    equity_rotation = return_table[return_table["Ticker"].isin(baskets["equity_region_rotation"])][["SignalDate", "Ticker", "R1M", "R3M", "R6M"]].copy()
    equity_rotation = equity_rotation.sort_values(["R3M", "Ticker"], ascending=[False, True]).reset_index(drop=True)
    equity_rotation["Rank3M"] = range(1, len(equity_rotation) + 1)
    equity_rotation.to_csv(OUTPUT_DIR / "equity_region_rotation.csv", index=False, encoding="utf-8-sig")

    real_assets_vs_financial = pd.DataFrame(
        [
            {
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "RealAssets3M": regime_metrics["real_assets_strength"],
                "FinancialAssets3M": regime_metrics["financial_assets_strength"],
                "Spread3M": regime_metrics["real_assets_strength"] - regime_metrics["financial_assets_strength"],
            }
        ]
    )
    real_assets_vs_financial.to_csv(OUTPUT_DIR / "real_assets_vs_financial_assets.csv", index=False, encoding="utf-8-sig")

    return_table[["SignalDate", "Ticker", "R1M", "R3M", "R6M", "R12M"]].to_csv(
        OUTPUT_DIR / "trend_heatmap.csv", index=False, encoding="utf-8-sig"
    )

    change.insert(0, "SignalDate", signal_date.strftime("%Y-%m-%d"))
    change.to_csv(OUTPUT_DIR / "change_since_last_month.csv", index=False, encoding="utf-8-sig")

    history_table.to_csv(OUTPUT_DIR / "leadership_history.csv", index=False, encoding="utf-8-sig")
    regime_history.to_csv(OUTPUT_DIR / "regime_history.csv", index=False, encoding="utf-8-sig")

    return_table.to_csv(OUTPUT_DIR / "_previous_return_table.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    watchlist_cfg, baskets_cfg, _ = load_config()
    tickers = [row["ticker"] for row in watchlist_cfg]
    coverage = sync_prices(watchlist_cfg, start="2015-01-01", end=pd.Timestamp.today().strftime("%Y-%m-%d"))

    issues = []
    if set(coverage["Ticker"].astype(str)) != set(tickers):
        issues.append("all 10 tickers not present in sync report")
    if coverage["Status"].astype(str).ne("OK").any():
        issues.append("one or more tickers failed price sync")
    if coverage["DuplicateDates"].fillna(0).astype(int).sum() != 0:
        issues.append("duplicate dates detected in synced prices")
    if coverage["InvalidCloses"].fillna(0).astype(int).sum() != 0:
        issues.append("invalid closes detected in synced prices")

    close, load_issues = load_close_matrix(watchlist_cfg)
    issues.extend(load_issues)
    month_end, signal_date, month_end_issues = compute_month_end(close, tickers)
    issues.extend(month_end_issues)

    if signal_date is pd.NaT or month_end.empty:
        raise SystemExit("; ".join(issues) if issues else "no valid completed month-end")

    if month_end.index.max().to_period("M") == pd.Timestamp.today().to_period("M"):
        issues.append("current incomplete month was not excluded")

    pos = month_end.index.get_loc(signal_date)
    if pos < 12:
        issues.append("insufficient 12M history for return calculations")

    if issues:
        raise SystemExit("; ".join(sorted(set(issues))))

    return_table = compute_return_table(month_end, signal_date)
    regime_label, regime_metrics = compute_regime(return_table, baskets_cfg)
    history_table, regime_history = compute_history_tables(month_end, baskets_cfg)
    write_outputs(signal_date, return_table, regime_label, regime_metrics, baskets_cfg, history_table, regime_history)

    validation = pd.DataFrame(
        [
            {
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "AllTickersPresent": 1,
                "NoDuplicateDates": 1,
                "NoInvalidCloses": 1,
                "IncompleteMonthExcluded": 1,
                "OutputsGenerated": 1,
                "HistoryGenerated": int(not history_table.empty and not regime_history.empty),
                "Regime": regime_label,
            }
        ]
    )
    validation.to_csv(OUTPUT_DIR / "validation_summary.csv", index=False, encoding="utf-8-sig")
    print(validation.to_string(index=False))


if __name__ == "__main__":
    main()
