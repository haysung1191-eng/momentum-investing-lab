from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
FRONTIER_CSV = ROOT / "output" / "split_models_tradeoff_frontier_review" / "tradeoff_frontier_compare.csv"
AUDIT_JSON = ROOT / "output" / "split_models_trade_data_audit" / "trade_data_audit_summary.json"
OUT_DIR = ROOT / "output" / "readme_assets"


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _svg_text(x: float, y: float, text: str, size: int = 14, weight: str = "400", fill: str = "#16324f", anchor: str = "start") -> str:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<text x="{x}" y="{y}" font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{safe}</text>'
    )


def _load_frontier_rows() -> list[dict[str, str]]:
    with FRONTIER_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _load_audit_summary() -> dict:
    with AUDIT_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def _variant_short_name(variant: str) -> str:
    alias = {
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on": "strongest",
        "hybrid_top2_plus_third00125": "broader",
        "bonus_recipient_top1_third_85_15": "quality",
        "tail_skip_entry_flowweakest_new_bottom4_top25_mid75": "headline",
        "regime_weight_defensive_if_top2flowsoft": "defensive",
        "multi_step_confirm_top1_flowtop2": "fragile",
        "tail_release_top50_mid50": "redistribution",
    }
    return alias.get(variant, variant[:28])


def _write_svg(path: Path, width: int, height: int, parts: Iterable[str]) -> None:
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{path.stem}">',
        '<rect width="100%" height="100%" fill="#f7f4ec"/>',
        *parts,
        "</svg>",
    ]
    path.write_text("\n".join(svg), encoding="utf-8")


def build_frontier_svg() -> Path:
    rows = _load_frontier_rows()
    selected = []
    wanted = {
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
        "hybrid_top2_plus_third00125",
        "bonus_recipient_top1_third_85_15",
        "tail_skip_entry_flowweakest_new_bottom4_top25_mid75",
        "regime_weight_defensive_if_top2flowsoft",
        "multi_step_confirm_top1_flowtop2",
        "tail_release_top50_mid50",
    }
    for row in rows:
        if row["Variant"] in wanted:
            selected.append(
                {
                    "name": _variant_short_name(row["Variant"]),
                    "cagr": float(row["CAGR"]),
                    "mdd": abs(float(row["MDD"])),
                    "sharpe": float(row["Sharpe"]),
                }
            )

    width = 980
    height = 640
    left = 90
    right = 80
    top = 90
    bottom = 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    min_x = min(p["mdd"] for p in selected) - 0.005
    max_x = max(p["mdd"] for p in selected) + 0.005
    min_y = min(p["cagr"] for p in selected) - 0.01
    max_y = max(p["cagr"] for p in selected) + 0.01
    max_s = max(p["sharpe"] for p in selected)
    min_s = min(p["sharpe"] for p in selected)

    def sx(v: float) -> float:
        return left + (v - min_x) / (max_x - min_x) * plot_w

    def sy(v: float) -> float:
        return top + plot_h - (v - min_y) / (max_y - min_y) * plot_h

    def sr(v: float) -> float:
        return 10 + (v - min_s) / (max_s - min_s + 1e-9) * 16

    palette = {
        "strongest": "#16324f",
        "broader": "#7c9d96",
        "quality": "#2a7f62",
        "headline": "#c56b2d",
        "defensive": "#596a7b",
        "fragile": "#b8405e",
        "redistribution": "#8d5a97",
    }

    parts: list[str] = [
        _svg_text(50, 44, "Current Truth Frontier", 28, "700"),
        _svg_text(50, 68, "x = drawdown severity (lower is better)   y = CAGR   bubble size = Sharpe", 14, "400", "#5c6b73"),
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fffdfa" stroke="#d7d0c4"/>',
    ]

    for i in range(6):
        x = left + plot_w * i / 5
        y = top + plot_h * i / 5
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" stroke="#ece6db"/>')
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#ece6db"/>')
        x_val = min_x + (max_x - min_x) * i / 5
        y_val = max_y - (max_y - min_y) * i / 5
        parts.append(_svg_text(x, top + plot_h + 26, _fmt_pct(x_val), 12, "400", "#5c6b73", "middle"))
        parts.append(_svg_text(left - 12, y + 4, _fmt_pct(y_val), 12, "400", "#5c6b73", "end"))

    parts.append(_svg_text(left + plot_w / 2, height - 24, "Max Drawdown (absolute)", 14, "600", "#36454f", "middle"))
    parts.append(f'<g transform="translate(24 {top + plot_h / 2}) rotate(-90)">{_svg_text(0, 0, "CAGR", 14, "600", "#36454f", "middle")}</g>')

    for point in selected:
        x = sx(point["mdd"])
        y = sy(point["cagr"])
        r = sr(point["sharpe"])
        color = palette.get(point["name"], "#6b7280")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" fill-opacity="0.84" stroke="#ffffff" stroke-width="2"/>')
        parts.append(_svg_text(x, y - r - 8, point["name"], 13, "600", color, "middle"))
        parts.append(_svg_text(x, y + r + 18, f"{point['sharpe']:.3f} Sharpe", 11, "400", "#5c6b73", "middle"))

    out_path = OUT_DIR / "current_truth_frontier.svg"
    _write_svg(out_path, width, height, parts)
    return out_path


def build_holdings_svg() -> Path:
    audit = _load_audit_summary()
    strongest = next(model for model in audit["models"] if model["label"] == "strongest")
    holdings = strongest["holdings"][:7]
    width = 980
    height = 520
    left = 220
    top = 90
    bar_h = 36
    gap = 18
    max_bar_w = 660
    max_weight = max(item["target_weight"] for item in holdings)

    parts: list[str] = [
        _svg_text(50, 44, "Latest Strongest Holdings Snapshot", 28, "700"),
        _svg_text(50, 68, f"Signal date {strongest['latest_signal_date']}   entered {', '.join(strongest['entered_symbols'][:6])}", 14, "400", "#5c6b73"),
    ]

    for idx, item in enumerate(holdings):
        y = top + idx * (bar_h + gap)
        label = f"{item['market']}:{item['symbol']}"
        name = item.get("name") or item["symbol"]
        weight = item["target_weight"]
        bar_w = weight / max_weight * max_bar_w
        color = "#16324f" if idx < 2 else "#c56b2d"
        parts.append(_svg_text(50, y + 24, label, 15, "700", "#16324f"))
        parts.append(_svg_text(50, y + 42, name, 12, "400", "#5c6b73"))
        parts.append(f'<rect x="{left}" y="{y}" width="{max_bar_w}" height="{bar_h}" rx="8" fill="#ebe5da"/>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="8" fill="{color}"/>')
        parts.append(_svg_text(left + min(bar_w + 14, max_bar_w - 6), y + 24, _fmt_pct(weight), 14, "700", "#16324f"))

    parts.append(_svg_text(50, height - 28, "Top 2 KR ETF sleeve dominates the latest book, with US industrial / health care names filling the residual tail.", 14, "400", "#5c6b73"))

    out_path = OUT_DIR / "strongest_latest_holdings.svg"
    _write_svg(out_path, width, height, parts)
    return out_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_frontier_svg()
    build_holdings_svg()
    print(f"Wrote visuals to {OUT_DIR}")


if __name__ == "__main__":
    main()
