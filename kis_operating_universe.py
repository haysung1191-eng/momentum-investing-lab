import argparse
import shutil
from pathlib import Path

import pandas as pd


PRESETS = {
    "liquidity_v1": {
        "stock_min_bars": 750,
        "stock_min_price": 1000.0,
        "stock_min_avg_value": 2_000_000_000.0,
        "stock_min_median_value": 800_000_000.0,
        "stock_max_zero_days": 2,
        "etf_min_bars": 180,
        "etf_min_avg_value": 100_000_000.0,
        "etf_min_median_value": 50_000_000.0,
        "etf_max_zero_days": 2,
    },
    "institutional_v1": {
        "stock_min_bars": 750,
        "stock_min_price": 1000.0,
        "stock_min_avg_value": 5_000_000_000.0,
        "stock_min_median_value": 2_000_000_000.0,
        "stock_max_zero_days": 1,
        "etf_min_bars": 180,
        "etf_min_avg_value": 500_000_000.0,
        "etf_min_median_value": 100_000_000.0,
        "etf_max_zero_days": 1,
    },
}


def load_metrics(base: Path) -> pd.DataFrame:
    rows = []
    for market in ["stock", "etf"]:
        market_dir = base / market
        for path in sorted(market_dir.glob("*.csv.gz")):
            try:
                df = pd.read_csv(path, compression="gzip", parse_dates=["date"]).sort_values("date")
            except Exception:
                continue
            if df.empty:
                continue
            recent = df.tail(60).copy()
            recent["traded_value"] = recent["close"] * recent["volume"]
            rows.append(
                {
                    "Market": market.upper(),
                    "Code": path.stem.replace(".csv", ""),
                    "Bars": int(len(df)),
                    "FirstDate": str(df["date"].min().date()),
                    "LastDate": str(df["date"].max().date()),
                    "LastClose": float(df["close"].iloc[-1]),
                    "AvgDailyValue60D": float(recent["traded_value"].mean()) if not recent.empty else 0.0,
                    "MedianDailyValue60D": float(recent["traded_value"].median()) if not recent.empty else 0.0,
                    "AvgVolume60D": float(recent["volume"].mean()) if not recent.empty else 0.0,
                    "ZeroValueDays60D": int((recent["traded_value"] <= 0).sum()) if not recent.empty else 60,
                }
            )
    return pd.DataFrame(rows)


def select_universe(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    stock_mask = (
        (df["Market"] == "STOCK")
        & (df["Bars"] >= args.stock_min_bars)
        & (df["LastClose"] >= args.stock_min_price)
        & (df["AvgDailyValue60D"] >= args.stock_min_avg_value)
        & (df["MedianDailyValue60D"] >= args.stock_min_median_value)
        & (df["ZeroValueDays60D"] <= args.stock_max_zero_days)
    )
    etf_mask = (
        (df["Market"] == "ETF")
        & (df["Bars"] >= args.etf_min_bars)
        & (df["AvgDailyValue60D"] >= args.etf_min_avg_value)
        & (df["MedianDailyValue60D"] >= args.etf_min_median_value)
        & (df["ZeroValueDays60D"] <= args.etf_max_zero_days)
    )

    stock_df = df[stock_mask].sort_values("AvgDailyValue60D", ascending=False).copy()
    etf_df = df[etf_mask].sort_values("AvgDailyValue60D", ascending=False).copy()

    if args.stock_max_count > 0:
        stock_df = stock_df.head(args.stock_max_count).copy()
    if args.etf_max_count > 0:
        etf_df = etf_df.head(args.etf_max_count).copy()

    selected = pd.concat([stock_df, etf_df], ignore_index=True)
    selected["SelectionRuleVersion"] = args.rule_version
    return selected.sort_values(["Market", "AvgDailyValue60D"], ascending=[True, False]).reset_index(drop=True)


def review_current(current_base: Path, selected: pd.DataFrame) -> pd.DataFrame:
    selected_codes = set(selected["Code"].astype(str))
    rows = []
    for market in ["stock", "etf"]:
        for path in sorted((current_base / market).glob("*.csv.gz")):
            code = path.stem.replace(".csv", "")
            rows.append(
                {
                    "Market": market.upper(),
                    "Code": code,
                    "CurrentOperating": 1,
                    "SelectedNew": int(code in selected_codes),
                    "Decision": "KEEP" if code in selected_codes else "DROP",
                }
            )
    return pd.DataFrame(rows).sort_values(["Decision", "Market", "Code"]).reset_index(drop=True)


def sync_selected(input_base: Path, output_base: Path, selected: pd.DataFrame) -> None:
    for market in ["stock", "etf"]:
        (output_base / market).mkdir(parents=True, exist_ok=True)
        for stale in (output_base / market).glob("*.csv.gz"):
            stale.unlink()
    for _, row in selected.iterrows():
        market = row["Market"].lower()
        code = str(row["Code"])
        src = input_base / market / f"{code}.csv.gz"
        dst = output_base / market / src.name
        if src.exists():
            shutil.copy2(src, dst)


def main() -> None:
    p = argparse.ArgumentParser(description="Build a rule-based operating universe from local price files.")
    p.add_argument("--input-base", type=str, default="data/prices")
    p.add_argument("--current-operating-base", type=str, default="data/prices_operating")
    p.add_argument("--output-base", type=str, default="data/prices_operating_v2")
    p.add_argument("--report-path", type=str, default="backtests/kis_operating_universe_candidates.csv")
    p.add_argument("--review-path", type=str, default="backtests/kis_operating_universe_review.csv")
    p.add_argument("--preset", choices=sorted(PRESETS), default="liquidity_v1")
    p.add_argument("--stock-min-bars", type=int, default=750)
    p.add_argument("--stock-min-price", type=float, default=1000.0)
    p.add_argument("--stock-min-avg-value", type=float, default=2_000_000_000.0)
    p.add_argument("--stock-min-median-value", type=float, default=800_000_000.0)
    p.add_argument("--stock-max-zero-days", type=int, default=2)
    p.add_argument("--stock-max-count", type=int, default=0, help="0 means no cap")
    p.add_argument("--etf-min-bars", type=int, default=180)
    p.add_argument("--etf-min-avg-value", type=float, default=100_000_000.0)
    p.add_argument("--etf-min-median-value", type=float, default=50_000_000.0)
    p.add_argument("--etf-max-zero-days", type=int, default=2)
    p.add_argument("--etf-max-count", type=int, default=0, help="0 means no cap")
    p.add_argument("--rule-version", type=str, default="liquidity_v1")
    args = p.parse_args()

    preset = PRESETS.get(args.preset, {})
    for key, value in preset.items():
        setattr(args, key, value)
    if args.rule_version == "liquidity_v1" and args.preset != "liquidity_v1":
        args.rule_version = args.preset

    input_base = Path(args.input_base)
    current_base = Path(args.current_operating_base)
    output_base = Path(args.output_base)
    report_path = Path(args.report_path)
    review_path = Path(args.review_path)

    metrics = load_metrics(input_base)
    if metrics.empty:
        raise RuntimeError(f"no metrics from {input_base}")

    selected = select_universe(metrics, args)
    review = review_current(current_base, selected)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(report_path, index=False)
    review.to_csv(review_path, index=False)
    sync_selected(input_base, output_base, selected)

    stock_count = int((selected["Market"] == "STOCK").sum())
    etf_count = int((selected["Market"] == "ETF").sum())
    print(f"selected stocks={stock_count}, etfs={etf_count}, total={len(selected)}")
    print(f"saved {report_path}")
    print(f"saved {review_path}")
    print(f"synced {output_base}")
    print("\n=== Selected universe ===")
    print(selected[["Market", "Code", "LastClose", "Bars", "AvgDailyValue60D", "MedianDailyValue60D"]].to_string(index=False))
    print("\n=== Current operating review ===")
    print(review.to_string(index=False))


if __name__ == "__main__":
    main()
