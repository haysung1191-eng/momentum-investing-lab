import argparse
import json
from io import BytesIO
from typing import Any

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


def read_json_any(path: str) -> dict[str, Any]:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            no_scheme = path.replace("gs://", "", 1)
            bucket_name, blob_name = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
            text = storage.Client().bucket(bucket_name).blob(blob_name).download_as_text(encoding="utf-8")
            return json.loads(text)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] could not read {path}: {e}")
        return {}


def get_single_run_id(df: pd.DataFrame) -> str | None:
    if df.empty or "RunId" not in df.columns:
        return None
    vals = [str(v) for v in df["RunId"].dropna().astype(str).unique() if str(v)]
    if len(vals) != 1:
        return None
    return vals[0]


def natural_recommendation(tier: str, strategy: str, best_strategy: str, operational_status: str) -> str:
    if operational_status != "fresh":
        return "STALE_INPUTS_REBUILD"
    if strategy == best_strategy:
        if tier == "SMALL_LIVE_READY":
            return "START_SMALL_LIVE_FIRST"
        if tier == "PAPER_READY":
            return "START_PAPER_FIRST"
    if tier == "SMALL_LIVE_READY":
        return "LIVE_CANDIDATE"
    if tier == "PAPER_READY":
        return "PAPER_CANDIDATE"
    return "HOLD"


def main() -> None:
    default_base = f"gs://{config.GCS_BUCKET_NAME}/backtests" if config.GCS_BUCKET_NAME else "."
    p = argparse.ArgumentParser(description="Build a live-readiness summary from canonical KIS research artifacts.")
    p.add_argument("--base-summary-path", type=str, default=f"{default_base}/kis_bt_auto_summary.csv")
    p.add_argument("--grid-path", type=str, default=f"{default_base}/kis_param_grid_results.csv")
    p.add_argument("--walkforward-summary-path", type=str, default=f"{default_base}/kis_walkforward_summary.csv")
    p.add_argument("--cost-path", type=str, default=f"{default_base}/kis_bt_cost_sensitivity_extended.csv")
    p.add_argument("--leaderboard-path", type=str, default=f"{default_base}/kis_strategy_leaderboard.csv")
    p.add_argument("--manifest-path", type=str, default=f"{default_base}/kis_pipeline_run_manifest.json")
    p.add_argument("--save-path", type=str, default=f"{default_base}/kis_live_readiness.csv")
    p.add_argument("--min-cagr-net-05", type=float, default=0.08)
    p.add_argument("--max-worst-mdd", type=float, default=0.20)
    p.add_argument("--min-window-count", type=int, default=3)
    p.add_argument("--min-stability-score", type=float, default=0.50)
    p.add_argument("--operational-only", type=int, default=1)
    args = p.parse_args()

    base_df = read_csv_any(args.base_summary_path)
    grid_df = read_csv_any(args.grid_path)
    wf_df = read_csv_any(args.walkforward_summary_path)
    cost_df = read_csv_any(args.cost_path)
    leader_df = read_csv_any(args.leaderboard_path)
    if not leader_df.empty:
        if "OperationalCandidate" not in leader_df.columns:
            leader_df["OperationalCandidate"] = leader_df["Strategy"].astype(str).map(
                lambda s: int(is_operational_candidate_strategy_name(s))
            )
        if "ResearchOnly" not in leader_df.columns:
            leader_df["ResearchOnly"] = leader_df["Strategy"].astype(str).map(
                lambda s: int(is_research_only_strategy_name(s))
            )
        if int(args.operational_only) == 1:
            leader_df = leader_df[leader_df["OperationalCandidate"] == 1].reset_index(drop=True)
    manifest = read_json_any(args.manifest_path)

    manifest_run_id = manifest.get("run_id")
    manifest_started_at = manifest.get("started_at")

    source_run_ids = {
        "baseline": get_single_run_id(base_df),
        "walkforward": get_single_run_id(wf_df),
        "cost": get_single_run_id(cost_df),
        "leaderboard": get_single_run_id(leader_df),
    }
    is_fresh = bool(manifest_run_id) and all(v == manifest_run_id for v in source_run_ids.values())
    operational_status = "fresh" if is_fresh else "stale"

    baseline_map: dict[str, dict[str, float]] = {}
    if not base_df.empty and {"Strategy", "CAGR", "MDD", "AnnualTurnover"}.issubset(base_df.columns):
        for _, r in base_df.iterrows():
            baseline_map[str(r["Strategy"])] = {
                "BaselineCAGR": float(r.get("CAGR", np.nan)),
                "BaselineMDD": float(r.get("MDD", np.nan)),
                "AnnualTurnover": float(r.get("AnnualTurnover", np.nan)),
            }

    grid_map: dict[str, dict[str, float]] = {}
    if not grid_df.empty and {"StrategyConfig", "AnnualTurnover"}.issubset(grid_df.columns):
        for _, r in grid_df.iterrows():
            grid_map[str(r["StrategyConfig"])] = {
                "AnnualTurnover": float(r.get("AnnualTurnover", np.nan)),
            }

    wf_map: dict[str, dict[str, float]] = {}
    if not wf_df.empty and {"StrategyName", "WindowCount", "WorstMDD"}.issubset(wf_df.columns):
        for _, r in wf_df.iterrows():
            wf_map[str(r["StrategyName"])] = {
                "WindowCount": float(r.get("WindowCount", np.nan)),
                "WorstMDD": float(r.get("WorstMDD", np.nan)),
            }

    cost_05_map: dict[str, float] = {}
    cost_strategy_col = "StrategyName" if "StrategyName" in cost_df.columns else ("Strategy" if "Strategy" in cost_df.columns else "")
    if not cost_df.empty and cost_strategy_col and {"RoundtripCostPct", "CAGR_net"}.issubset(cost_df.columns):
        tmp = cost_df.copy()
        tmp["RoundtripCostPct"] = pd.to_numeric(tmp["RoundtripCostPct"], errors="coerce")
        c05 = tmp[np.isclose(tmp["RoundtripCostPct"], 0.5, atol=1e-12)]
        for _, r in c05.iterrows():
            cost_05_map[str(r[cost_strategy_col])] = float(r.get("CAGR_net", np.nan))

    rows: list[dict[str, Any]] = []
    for _, r in leader_df.iterrows():
        strategy = str(r["Strategy"])
        baseline = baseline_map.get(strategy, {})
        wf = wf_map.get(strategy, {})
        row = {
            "Strategy": strategy,
            "RunId": manifest_run_id,
            "RunStartedAt": manifest_started_at,
            "BaselineCAGR": baseline.get("BaselineCAGR", np.nan),
            "BaselineMDD": baseline.get("BaselineMDD", np.nan),
            "CAGR_net_0.5pct": float(r.get("CAGR_net_0.5pct", cost_05_map.get(strategy, np.nan))),
            "WorstMDD": float(r.get("WorstMDD", wf.get("WorstMDD", np.nan))),
            "WindowCount": int(float(r.get("WindowCount", wf.get("WindowCount", 0)))) if pd.notna(r.get("WindowCount", wf.get("WindowCount", np.nan))) else 0,
            "StabilityScore": float(r.get("StabilityScore", np.nan)),
            "AnnualTurnover": float(
                r.get(
                    "AnnualTurnover",
                    baseline.get("AnnualTurnover", grid_map.get(strategy, {}).get("AnnualTurnover", np.nan)),
                )
            ),
            "ResearchOnly": int(r.get("ResearchOnly", is_research_only_strategy_name(strategy))),
            "OperationalCandidate": int(r.get("OperationalCandidate", is_operational_candidate_strategy_name(strategy))),
        }
        row["CostRobust"] = int(pd.notna(row["CAGR_net_0.5pct"]) and float(row["CAGR_net_0.5pct"]) >= args.min_cagr_net_05)
        row["WalkforwardAdequate"] = int(int(row["WindowCount"]) >= args.min_window_count)
        row["OperationalStatus"] = operational_status

        worst_mdd_ok = pd.notna(row["WorstMDD"]) and abs(float(row["WorstMDD"])) <= args.max_worst_mdd
        stability_ok = pd.notna(row["StabilityScore"]) and float(row["StabilityScore"]) >= args.min_stability_score
        if row["CostRobust"] == 1 and row["WalkforwardAdequate"] == 1 and worst_mdd_ok and stability_ok and operational_status == "fresh":
            row["ReadinessTier"] = "SMALL_LIVE_READY"
        elif row["CostRobust"] == 1 and operational_status == "fresh":
            row["ReadinessTier"] = "PAPER_READY"
        else:
            row["ReadinessTier"] = "NOT_READY"
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        cols = [
            "Strategy", "RunId", "RunStartedAt", "BaselineCAGR", "BaselineMDD", "CAGR_net_0.5pct", "WorstMDD",
            "WindowCount", "StabilityScore", "AnnualTurnover", "CostRobust", "WalkforwardAdequate",
            "OperationalStatus", "ReadinessTier", "Recommendation", "ResearchOnly", "OperationalCandidate",
        ]
        out = pd.DataFrame(columns=cols)
    else:
        readiness_rank = {"SMALL_LIVE_READY": 2, "PAPER_READY": 1, "NOT_READY": 0}
        out["_rank"] = out["ReadinessTier"].map(readiness_rank).fillna(-1)
        out = out.sort_values(
            ["OperationalCandidate", "ResearchOnly", "_rank", "CAGR_net_0.5pct", "WorstMDD", "StabilityScore", "Strategy"],
            ascending=[False, True, False, False, False, False, True],
        ).reset_index(drop=True)
        best_strategy = str(out.iloc[0]["Strategy"])
        out["Recommendation"] = [
            natural_recommendation(tier, strategy, best_strategy, op)
            for tier, strategy, op in zip(out["ReadinessTier"], out["Strategy"], out["OperationalStatus"])
        ]
        out = out.drop(columns="_rank")

    cols = [
        "Strategy", "RunId", "RunStartedAt", "BaselineCAGR", "BaselineMDD", "CAGR_net_0.5pct", "WorstMDD",
        "WindowCount", "StabilityScore", "AnnualTurnover", "CostRobust", "WalkforwardAdequate",
        "OperationalStatus", "ReadinessTier", "Recommendation", "ResearchOnly", "OperationalCandidate",
    ]
    for col in cols:
        if col not in out.columns:
            out[col] = np.nan
    out = out[cols]
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print("\n=== Live Readiness (top 20) ===")
    print(out.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
