import argparse
from io import BytesIO
from typing import Dict, List

import numpy as np
import pandas as pd

import config
from kis_backtest_from_prices import (
    is_operational_candidate_strategy_name,
    is_research_only_strategy_name,
    write_csv_any,
)


def read_csv_any(path: str) -> pd.DataFrame:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            no_scheme = path.replace("gs://", "", 1)
            bucket_name, blob_name = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
            raw = storage.Client().bucket(bucket_name).blob(blob_name).download_as_bytes()
            return pd.read_csv(BytesIO(raw))
        return pd.read_csv(path)
    except Exception as e:
        print(f"[WARN] could not read {path}: {e}")
        return pd.DataFrame()


def main() -> None:
    default_base = f"gs://{config.GCS_BUCKET_NAME}/backtests" if config.GCS_BUCKET_NAME else "."
    p = argparse.ArgumentParser(description="Build unified strategy leaderboard from base/grid/walkforward/cost outputs.")
    p.add_argument("--base-summary-path", type=str, default=f"{default_base}/kis_bt_auto_summary.csv")
    p.add_argument("--grid-path", type=str, default=f"{default_base}/kis_param_grid_results.csv")
    p.add_argument("--walkforward-results-path", type=str, default=f"{default_base}/kis_walkforward_results.csv")
    p.add_argument("--walkforward-summary-path", type=str, default=f"{default_base}/kis_walkforward_summary.csv")
    p.add_argument("--cost-path", type=str, default=f"{default_base}/kis_bt_cost_sensitivity_extended.csv")
    p.add_argument("--grid-top-k", type=int, default=5)
    p.add_argument("--operational-only", type=int, default=0)
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_strategy_leaderboard.csv")
    args = p.parse_args()

    base_df = read_csv_any(args.base_summary_path)
    grid_df = read_csv_any(args.grid_path)
    wf_res = read_csv_any(args.walkforward_results_path)
    wf_sum = read_csv_any(args.walkforward_summary_path)
    cost_df = read_csv_any(args.cost_path)

    strategies: List[str] = []
    if not base_df.empty and "Strategy" in base_df.columns:
        strategies.extend(list(base_df["Strategy"].dropna().astype(str).unique()))
    if not grid_df.empty and "StrategyConfig" in grid_df.columns:
        strategies.extend(list(grid_df["StrategyConfig"].dropna().astype(str).head(args.grid_top_k).unique()))
    if not wf_sum.empty and "StrategyName" in wf_sum.columns:
        strategies.extend(list(wf_sum["StrategyName"].dropna().astype(str).unique()))
    if not cost_df.empty and "StrategyName" in cost_df.columns:
        strategies.extend(list(cost_df["StrategyName"].dropna().astype(str).unique()))
    strategies = sorted(set(strategies))

    wf_stats_map: Dict[str, Dict[str, float]] = {}
    if not wf_res.empty and {"StrategyName", "CAGR_net", "MDD"}.issubset(wf_res.columns):
        for s, g in wf_res.groupby("StrategyName"):
            c = g["CAGR_net"].astype(float)
            m = g["MDD"].astype(float)
            wf_stats_map[str(s)] = {
                "WindowCount": int(g["WindowStart"].nunique()) if "WindowStart" in g.columns else int(len(g)),
                "MedianCAGR": float(c.median()),
                "WorstCAGR": float(c.min()),
                "MedianMDD": float(m.median()),
                "WorstMDD": float(m.min()),
                "CAGRStd": float(c.std(ddof=0)),
            }

    cost_05: Dict[str, Dict[str, float]] = {}
    cost_strategy_col = "StrategyName" if "StrategyName" in cost_df.columns else ("Strategy" if "Strategy" in cost_df.columns else "")
    if not cost_df.empty and cost_strategy_col and {"RoundtripCostPct", "CAGR_net"}.issubset(cost_df.columns):
        c = cost_df.copy()
        c["RoundtripCostPct"] = pd.to_numeric(c["RoundtripCostPct"], errors="coerce")
        c05 = c[np.isclose(c["RoundtripCostPct"], 0.5, atol=1e-12)]
        for _, r in c05.iterrows():
            s = str(r[cost_strategy_col])
            cost_05[s] = {
                "CAGR_net_0.5pct": float(r.get("CAGR_net", np.nan)),
                "AnnualTurnover": float(r.get("AnnualTurnover", np.nan)),
            }

    base_map: Dict[str, Dict[str, float]] = {}
    if not base_df.empty and {"Strategy", "CAGR", "MDD"}.issubset(base_df.columns):
        for _, r in base_df.iterrows():
            s = str(r["Strategy"])
            base_map[s] = {
                "WindowCount": 1,
                "MedianCAGR": float(r.get("CAGR", np.nan)),
                "WorstCAGR": float(r.get("CAGR", np.nan)),
                "MedianMDD": float(r.get("MDD", np.nan)),
                "WorstMDD": float(r.get("MDD", np.nan)),
                "CAGRStd": np.nan,
                "AnnualTurnover": float(r.get("AnnualTurnover", np.nan)),
                "RangeDaysPct": float(r.get("RangeDaysPct", np.nan)),
                "UptrendDaysPct": float(r.get("UptrendDaysPct", np.nan)),
                "DowntrendDaysPct": float(r.get("DowntrendDaysPct", np.nan)),
                "TransitionDaysPct": float(r.get("TransitionDaysPct", np.nan)),
                "OscEntryCount": float(r.get("OscEntryCount", np.nan)),
                "OscExitCount": float(r.get("OscExitCount", np.nan)),
                "OscStopCount": float(r.get("OscStopCount", np.nan)),
                "RotationSignalAvg": float(r.get("RotationSignalAvg", np.nan)),
                "AvgStockSleeve": float(r.get("AvgStockSleeve", np.nan)),
                "AvgEtfSleeve": float(r.get("AvgEtfSleeve", np.nan)),
            }

    grid_map: Dict[str, Dict[str, float]] = {}
    if not grid_df.empty and {"StrategyConfig", "CAGR", "MDD", "CAGR_net_0.5pct_cost"}.issubset(grid_df.columns):
        for _, r in grid_df.iterrows():
            s = str(r["StrategyConfig"])
            grid_map[s] = {
                "WindowCount": 1,
                "MedianCAGR": float(r.get("CAGR", np.nan)),
                "WorstCAGR": float(r.get("CAGR", np.nan)),
                "MedianMDD": float(r.get("MDD", np.nan)),
                "WorstMDD": float(r.get("MDD", np.nan)),
                "CAGRStd": np.nan,
                "CAGR_net_0.5pct": float(r.get("CAGR_net_0.5pct_cost", np.nan)),
                "AnnualTurnover": float(r.get("AnnualTurnover", np.nan)),
            }

    rows: List[Dict[str, float]] = []
    for s in strategies:
        row: Dict[str, float] = {"Strategy": s}
        if s in wf_stats_map:
            row.update(wf_stats_map[s])
            if s in base_map:
                for key, value in base_map[s].items():
                    if key not in row or pd.isna(row.get(key)):
                        row[key] = value
        elif s in base_map:
            row.update(base_map[s])
        elif s in grid_map:
            row.update({k: v for k, v in grid_map[s].items() if k in {"MedianCAGR", "WorstCAGR", "MedianMDD", "WorstMDD", "CAGRStd"}})
        else:
            row.update({"WindowCount": 0, "MedianCAGR": np.nan, "WorstCAGR": np.nan, "MedianMDD": np.nan, "WorstMDD": np.nan, "CAGRStd": np.nan})

        if s in cost_05:
            row["CAGR_net_0.5pct"] = cost_05[s]["CAGR_net_0.5pct"]
            row["AnnualTurnover"] = cost_05[s]["AnnualTurnover"]
        elif s in grid_map:
            row["CAGR_net_0.5pct"] = grid_map[s].get("CAGR_net_0.5pct", np.nan)
            row["AnnualTurnover"] = grid_map[s].get("AnnualTurnover", np.nan)
        elif s in base_map:
            row["CAGR_net_0.5pct"] = np.nan
            row["AnnualTurnover"] = base_map[s].get("AnnualTurnover", np.nan)
        else:
            row["CAGR_net_0.5pct"] = np.nan
            row["AnnualTurnover"] = np.nan

        wc = int(row.get("WindowCount", 0))
        cstd = row.get("CAGRStd", np.nan)
        mcagr = row.get("MedianCAGR", np.nan)
        worst_mdd = row.get("WorstMDD", np.nan)
        if wc >= 3 and pd.notna(cstd) and abs(float(cstd)) > 1e-12:
            row["StabilityScore"] = float(mcagr) / float(cstd)
        elif pd.notna(mcagr) and pd.notna(worst_mdd) and abs(float(worst_mdd)) > 1e-12:
            row["StabilityScore"] = float(mcagr) / abs(float(worst_mdd))
        else:
            row["StabilityScore"] = np.nan
        row["ResearchOnly"] = int(is_research_only_strategy_name(s))
        row["OperationalCandidate"] = int(is_operational_candidate_strategy_name(s))
        rows.append(row)

    out = pd.DataFrame(rows)
    if int(args.operational_only) == 1 and not out.empty:
        out = out[out["OperationalCandidate"] == 1].reset_index(drop=True)
    cols = [
        "Strategy",
        "MedianCAGR",
        "WorstCAGR",
        "MedianMDD",
        "WorstMDD",
        "CAGR_net_0.5pct",
        "AnnualTurnover",
        "StabilityScore",
        "RangeDaysPct",
        "UptrendDaysPct",
        "DowntrendDaysPct",
        "TransitionDaysPct",
        "OscEntryCount",
        "OscExitCount",
        "OscStopCount",
        "RotationSignalAvg",
        "AvgStockSleeve",
        "AvgEtfSleeve",
        "ResearchOnly",
        "OperationalCandidate",
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = np.nan
    out = out[cols].sort_values(
        ["OperationalCandidate", "ResearchOnly", "CAGR_net_0.5pct", "WorstMDD", "StabilityScore", "MedianCAGR", "Strategy"],
        ascending=[False, True, False, False, False, False, True],
    ).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print(f"leaderboard_rows={len(out)}")
    print("\n=== Strategy Leaderboard (top 20) ===")
    print(out.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
