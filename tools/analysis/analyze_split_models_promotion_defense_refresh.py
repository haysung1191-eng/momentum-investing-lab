from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_promotion_defense_refresh"

SUMMARY = {
    "as_of_date": "2026-04-17",
    "repo": "momentum",
    "asset_class": "stocks_etfs",
    "operational_baseline": "rule_breadth_it_us5_cap",
    "aggressive_strongest": {
        "variant": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
        "cagr": "63.16%",
        "mdd": "-29.27%",
        "sharpe": "1.6892",
        "annual_turnover": "15.32",
    },
    "broader_challenger": {
        "variant": "hybrid_top2_plus_third00125",
        "cagr": "63.12%",
        "mdd": "-29.27%",
        "sharpe": "1.6895",
        "cost_75bps_cagr_delta_vs_strongest": "-0.04%p",
        "walkforward": "2 positive / 2 negative",
        "takeaway": "best broader-but-weaker point",
    },
    "quality_near_miss": {
        "variant": "bonus_recipient_top1_third_85_15",
        "cagr": "65.43%",
        "mdd": "-29.52%",
        "sharpe": "1.6927",
        "cost_75bps_cagr_delta_vs_strongest": "+1.68%p",
        "walkforward": "3 positive / 1 negative",
        "takeaway": "best blended-quality extension, but drawdown and walk-forward Sharpe still fail promotion grade",
    },
    "headline_near_miss": {
        "variant": "tail_skip_entry_flowweakest_new_bottom4_top25_mid75",
        "cagr": "63.21%",
        "mdd": "-28.77%",
        "sharpe": "1.6625",
        "cost_75bps_cagr_delta_vs_strongest": "+0.53%p",
        "walkforward": "3 positive / 1 negative",
        "takeaway": "best headline extension, but Sharpe still stays too weak",
    },
    "recent_failed_families": [
        {
            "family": "quality-headline hybrid",
            "best_tested_point": "hybrid_quality85_skipentry_top25_mid75",
            "headline": "+1.56%p CAGR and +0.25%p MDD",
            "failure": "Sharpe delta -0.0394 and walk-forward Sharpe stayed clearly negative",
        },
        {
            "family": "risk-on exposure",
            "best_tested_point": "risk_on_exposure_106",
            "headline": "no candidate beat strongest headline",
            "failure": "all scanned points were weaker on CAGR, walk-forward, and cost together",
        },
        {
            "family": "risk-off tightening",
            "best_tested_point": "risk_off_tighten_sector075",
            "headline": "+0.0150 Sharpe",
            "failure": "CAGR delta -1.53%p with 1 positive / 3 negative walk-forward windows",
        },
        {
            "family": "entry filter",
            "best_tested_point": "entry_filter_soft_r1m20_pen50",
            "headline": "+0.50%p MDD improvement",
            "failure": "CAGR delta -0.73%p and cost-adjusted Sharpe stayed negative",
        },
        {
            "family": "hold buffer",
            "best_tested_point": "hold_buffer1 / hold_buffer2",
            "headline": "no-op",
            "failure": "identical to strongest; no research value in this branch family",
        },
        {
            "family": "position cap",
            "best_tested_point": "position_cap_us4",
            "headline": "+2.40%p MDD improvement",
            "failure": "CAGR delta -22.78%p and walk-forward 0 positive / 4 negative",
        },
        {
            "family": "sector cap relaxation",
            "best_tested_point": "sector_cap3",
            "headline": "+2.18%p MDD improvement",
            "failure": "CAGR delta -6.07%p and walk-forward 0 positive / 4 negative",
        },
        {
            "family": "flow filter",
            "best_tested_point": "flow_filter_uscap035",
            "headline": "none",
            "failure": "CAGR delta -33.00%p and Sharpe delta -0.3538",
        },
        {
            "family": "soft blacklist",
            "best_tested_point": "soft_blacklist_top3_pen85",
            "headline": "+0.20%p MDD improvement",
            "failure": "CAGR delta -2.05%p and Sharpe delta -0.0824",
        },
        {
            "family": "dynamic bonus sizing",
            "best_tested_point": "dynamic_bonus_tight14_if_top42",
            "headline": "slightly lower turnover",
            "failure": "CAGR delta -1.51%p and fragility worsened",
        },
    ],
    "promotion_defense_verdict": "keep the current strongest; recent search widened the near-miss map but did not produce a new promotion-grade stronger branch",
}


def _build_markdown(summary: dict) -> str:
    strongest = summary["aggressive_strongest"]
    broader = summary["broader_challenger"]
    quality = summary["quality_near_miss"]
    headline = summary["headline_near_miss"]

    lines = [
        "# Split Models Promotion Defense Refresh",
        "",
        "## Purpose",
        "",
        "- freeze the current strongest after another batch of family exploration",
        "- make it obvious why the strongest still stays after many near-miss tests",
        "",
        "## Current Truth",
        "",
        f"- strongest: `{strongest['variant']}`",
        f"  - CAGR `{strongest['cagr']}`",
        f"  - MDD `{strongest['mdd']}`",
        f"  - Sharpe `{strongest['sharpe']}`",
        f"  - Annual turnover `{strongest['annual_turnover']}`",
        f"- broader challenger: `{broader['variant']}`",
        f"  - CAGR `{broader['cagr']}`",
        f"  - Sharpe `{broader['sharpe']}`",
        f"  - walk-forward `{broader['walkforward']}`",
        f"  - takeaway `{broader['takeaway']}`",
        f"- quality near-miss: `{quality['variant']}`",
        f"  - CAGR `{quality['cagr']}`",
        f"  - Sharpe `{quality['sharpe']}`",
        f"  - walk-forward `{quality['walkforward']}`",
        f"  - takeaway `{quality['takeaway']}`",
        f"- headline near-miss: `{headline['variant']}`",
        f"  - CAGR `{headline['cagr']}`",
        f"  - MDD `{headline['mdd']}`",
        f"  - walk-forward `{headline['walkforward']}`",
        f"  - takeaway `{headline['takeaway']}`",
        "",
        "## Recent Failed Families",
        "",
    ]

    for row in summary["recent_failed_families"]:
        lines.extend(
            [
                f"- {row['family']}: `{row['best_tested_point']}`",
                f"  - strongest signal: `{row['headline']}`",
                f"  - failure reason: `{row['failure']}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- {summary['promotion_defense_verdict']}",
            "- recent search mostly improved explanation quality, not mainline promotion quality",
            "- keep future search focused on genuinely different families instead of re-litigating dead axes",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "promotion_defense_refresh_summary.json").write_text(
        json.dumps(SUMMARY, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "promotion_defense_refresh.md").write_text(
        _build_markdown(SUMMARY), encoding="utf-8"
    )
    print(json.dumps(SUMMARY, indent=2))


if __name__ == "__main__":
    main()
