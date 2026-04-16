from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_nightly_safe_summary"


SUMMARY = {
    "as_of_date": "2026-04-17",
    "repo": "momentum",
    "asset_class": "stocks_etfs",
    "operational_baseline": "rule_breadth_it_us5_cap",
    "aggressive_strongest": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
    "broader_challenger": "hybrid_top2_plus_third00125",
    "strongest_metrics": {
        "cagr": "63.16%",
        "mdd": "-29.27%",
        "sharpe": "1.6892",
        "annual_turnover": "15.32",
    },
    "broader_challenger_metrics": {
        "cagr": "63.12%",
        "mdd": "-29.27%",
        "sharpe": "1.6895",
        "annual_turnover": "15.32",
    },
    "broader_challenger_delta_vs_strongest": {
        "cagr_delta": "-0.04%p",
        "mdd_delta": "+0.00%p",
        "sharpe_delta": "+0.0003",
        "cost_75bps_cagr_delta": "-0.04%p",
        "walkforward": "2 positive / 2 negative",
    },
    "benchmark_check": {
        "benchmark": "benchmark_xs_mom_12_1_top5_eq",
        "strongest_cost_75bps_cagr_delta": "+11.49%p",
        "start_shift_cagr_record": "5 positive / 0 negative",
    },
    "nightly_verdict": {
        "keep_strongest": True,
        "promote_broader_challenger": False,
        "reason": "strongest remains the stronger branch; broader challenger is close but still weaker on CAGR and promotion robustness",
    },
}


def _build_markdown(summary: dict) -> str:
    strongest = summary["aggressive_strongest"]
    broader = summary["broader_challenger"]
    strongest_metrics = summary["strongest_metrics"]
    broader_metrics = summary["broader_challenger_metrics"]
    broader_delta = summary["broader_challenger_delta_vs_strongest"]
    benchmark = summary["benchmark_check"]

    return "\n".join(
        [
            "# Split Models Nightly Safe Summary",
            "",
            "## Current truth",
            "",
            f"- repo: `{summary['repo']}`",
            f"- asset class: `{summary['asset_class']}`",
            f"- operational baseline: `{summary['operational_baseline']}`",
            f"- aggressive strongest: `{strongest}`",
            f"- broader challenger: `{broader}`",
            "",
            "## Strongest snapshot",
            "",
            f"- CAGR: `{strongest_metrics['cagr']}`",
            f"- MDD: `{strongest_metrics['mdd']}`",
            f"- Sharpe: `{strongest_metrics['sharpe']}`",
            f"- Annual turnover: `{strongest_metrics['annual_turnover']}`",
            "",
            "## Broader challenger snapshot",
            "",
            f"- variant: `{broader}`",
            f"- CAGR: `{broader_metrics['cagr']}`",
            f"- MDD: `{broader_metrics['mdd']}`",
            f"- Sharpe: `{broader_metrics['sharpe']}`",
            f"- Annual turnover: `{broader_metrics['annual_turnover']}`",
            "",
            "## Why strongest still stays",
            "",
            f"- CAGR delta vs strongest: `{broader_delta['cagr_delta']}`",
            f"- MDD delta vs strongest: `{broader_delta['mdd_delta']}`",
            f"- Sharpe delta vs strongest: `{broader_delta['sharpe_delta']}`",
            f"- `75 bps` cost CAGR delta: `{broader_delta['cost_75bps_cagr_delta']}`",
            f"- walk-forward: `{broader_delta['walkforward']}`",
            "",
            "## Benchmark guardrail",
            "",
            f"- benchmark: `{benchmark['benchmark']}`",
            f"- strongest `75 bps` CAGR delta vs benchmark: `{benchmark['strongest_cost_75bps_cagr_delta']}`",
            f"- strongest start-date shift record: `{benchmark['start_shift_cagr_record']}`",
            "",
            "## Nightly verdict",
            "",
            "- keep the current strongest as the mainline aggressive branch",
            "- treat the broader challenger as a near-miss, not a promotion",
            "- if more overnight work is run, prefer broader-challenger exploration over disturbing the strongest baseline again",
            "",
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "nightly_safe_summary.json").write_text(json.dumps(SUMMARY, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "nightly_safe_summary.md").write_text(_build_markdown(SUMMARY), encoding="utf-8")
    print(json.dumps(SUMMARY, indent=2))


if __name__ == "__main__":
    main()
