import argparse
from typing import Dict, List

import pandas as pd

import config
from kis_backtest_from_prices import build_close_matrix, write_csv_any


def _years_between(a: pd.Timestamp, b: pd.Timestamp) -> float:
    return max(float((b - a).days) / 365.25, 0.0)


def _coverage_rows(close: pd.DataFrame) -> List[Dict[str, float]]:
    rows: List[Dict[str, float]] = []
    if close.empty:
        return rows
    for sym in sorted(close.columns):
        s = close[sym].dropna()
        if s.empty:
            continue
        first_dt = pd.Timestamp(s.index.min()).normalize()
        last_dt = pd.Timestamp(s.index.max()).normalize()
        rows.append(
            {
                "Symbol": str(sym),
                "FirstDate": first_dt.strftime("%Y-%m-%d"),
                "LastDate": last_dt.strftime("%Y-%m-%d"),
                "YearsAvailable": round(_years_between(first_dt, last_dt), 6),
                "TotalBars": int(len(s)),
            }
        )
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description="Create symbol-level and common-date coverage report for KIS research data.")
    p.add_argument("--base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--max-files", type=int, default=0, help="0 means all")
    p.add_argument(
        "--save-path",
        type=str,
        default=(f"gs://{config.GCS_BUCKET_NAME}/backtests/kis_data_coverage_report.csv" if config.GCS_BUCKET_NAME else "kis_data_coverage_report.csv"),
    )
    args = p.parse_args()

    print("loading stock close matrix...")
    close_s = build_close_matrix(args.base, "stock", args.max_files)
    print("loading etf close matrix...")
    close_e = build_close_matrix(args.base, "etf", args.max_files)

    rows = _coverage_rows(close_s) + _coverage_rows(close_e)
    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame(columns=["Symbol", "FirstDate", "LastDate", "YearsAvailable", "TotalBars", "CommonStartDate", "CommonEndDate", "CommonYears"])
        write_csv_any(out, args.save_path, index=False)
        print(f"saved {args.save_path}")
        return

    common_idx = close_s.index.intersection(close_e.index).sort_values()
    if len(common_idx):
        common_start = pd.Timestamp(common_idx.min()).normalize()
        common_end = pd.Timestamp(common_idx.max()).normalize()
        common_years = _years_between(common_start, common_end)
        common_start_s = common_start.strftime("%Y-%m-%d")
        common_end_s = common_end.strftime("%Y-%m-%d")
    else:
        common_start_s = ""
        common_end_s = ""
        common_years = 0.0

    out["CommonStartDate"] = common_start_s
    out["CommonEndDate"] = common_end_s
    out["CommonYears"] = round(common_years, 6)
    out = out.sort_values(["Symbol", "FirstDate", "LastDate"], ascending=[True, True, True]).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(f"common_start={common_start_s}, common_end={common_end_s}, common_years={common_years:.2f}")
    print("\n=== Coverage report sample (top 20) ===")
    print(out.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
