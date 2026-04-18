from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


CURRENT_STATE_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_current_state.json"
MANIFEST_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_manifest.json"
HANDOFF_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_handoff" / "handoff_summary.json"
CLOSURE_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_closure" / "closure_summary.json"
OUTPUT_DIR = REPO_ROOT / "output" / "split_models_operational_conversion_dashboard"
OUTPUT_HTML = OUTPUT_DIR / "dashboard.html"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _status_color(gate_status: str) -> str:
    if gate_status.upper() == "OPEN":
        return "#1f7a4c"
    if gate_status.upper() == "BLOCKED":
        return "#9d2b2b"
    return "#8a6d1d"


def _card(title: str, value: str) -> str:
    return (
        "<div class='card'>"
        f"<div class='label'>{title}</div>"
        f"<div class='value'>{value}</div>"
        "</div>"
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    current_state = _load_json(CURRENT_STATE_JSON)
    manifest = _load_json(MANIFEST_JSON)
    handoff = _load_json(HANDOFF_JSON)
    closure = _load_json(CLOSURE_JSON)

    accent = _status_color(str(current_state["gate_status"]))
    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Operational Conversion Dashboard</title>
  <style>
    :root {{
      --accent: {accent};
      --bg1: #f7f1e8;
      --bg2: #eef3fb;
      --ink: #1f2430;
      --muted: #5f6673;
      --panel: rgba(255,255,255,0.86);
      --border: rgba(20,20,20,0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Apple SD Gothic Neo", sans-serif;
      color: var(--ink);
      background: linear-gradient(180deg, var(--bg1), var(--bg2));
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,255,255,0.7));
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 18px 50px rgba(40, 48, 71, 0.08);
    }}
    .eyebrow {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 10px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 36px;
    }}
    .subtitle {{
      color: var(--muted);
      line-height: 1.6;
      max-width: 760px;
    }}
    .pills {{
      margin-top: 18px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .pill {{
      padding: 10px 14px;
      border-radius: 999px;
      color: white;
      font-weight: 700;
    }}
    .pill.blue {{ background: #3b5b92; }}
    .pill.brown {{ background: #5d4037; }}
    .metrics {{
      margin-top: 22px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px;
    }}
    .label {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}
    .value {{
      font-size: 24px;
      font-weight: 700;
      line-height: 1.25;
      word-break: break-word;
    }}
    .grid {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: 1.2fr 0.9fr;
      gap: 18px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 20px;
    }}
    h2 {{
      margin-top: 0;
      font-size: 22px;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      line-height: 1.7;
    }}
    code, pre {{
      font-family: Consolas, monospace;
    }}
    .cmd {{
      background: #101522;
      color: #edf2ff;
      border-radius: 14px;
      padding: 12px 14px;
      margin: 10px 0;
      overflow-x: auto;
    }}
    .small {{
      color: var(--muted);
      font-size: 14px;
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 30px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">Split Models Operational Conversion Branch</div>
      <h1>한눈 대시보드</h1>
      <div class="subtitle">
        지금 이 branch는 운영 승격이 막혀 있습니다. 핵심 이유는 anchor drawdown이 baseline보다 더 깊고,
        지금까지 시험한 축 중 drawdown을 실제로 고친 구조가 없기 때문입니다.
      </div>
      <div class="pills">
        <div class="pill" style="background:{accent}">Gate: {current_state['gate_status']}</div>
        <div class="pill blue">Promotion: {current_state['promotion_status']}</div>
        <div class="pill brown">Anchor: {current_state['anchor_variant']}</div>
      </div>
      <div class="metrics">
        {_card("Anchor MDD", handoff["anchor_mdd_display"])}
        {_card("Baseline MDD", handoff["baseline_mdd_display"])}
        {_card("Drawdown Gap", handoff["drawdown_gap_vs_baseline_display"])}
        {_card("Best Quality Overlay", handoff["best_quality_variant"])}
        {_card("Drawdown Improvers", str(current_state["drawdown_improver_count"]))}
        {_card("Quality Overlays", str(current_state["quality_overlay_count"]))}
        {_card("No-op Axes", str(current_state["no_op_count"]))}
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>쉽게 보면</h2>
        <ul>
          <li>현재 상태는 <code>{current_state['gate_status']}</code> 입니다.</li>
          <li>운영 승격이 막힌 직접 이유는 <code>{current_state['promotion_status']}</code> 입니다.</li>
          <li>가장 좋은 기준 anchor는 <code>{current_state['anchor_variant']}</code> 입니다.</li>
          <li>품질만 좋아지는 overlay는 있었지만, drawdown 자체를 고친 축은 없었습니다.</li>
          <li>그래서 이 branch는 새 구조가 생길 때만 다시 열도록 닫혀 있습니다.</li>
        </ul>
      </div>
      <div class="panel">
        <h2>검증 상태</h2>
        <ul>
          <li>Doctor smoke: <code>{closure['doctor_smoke_test_status']}</code></li>
          <li>Probe smoke: <code>{closure['probe_smoke_test_status']}</code></li>
          <li>Probe exit codes: python <code>{closure['python_probe_exit_code']}</code>,
              powershell <code>{closure['powershell_probe_exit_code']}</code>,
              cmd <code>{closure['cmd_probe_exit_code']}</code></li>
        </ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>지금 쓰면 되는 명령</h2>
        <div class="cmd">{manifest['doctor_command']}</div>
        <div class="cmd">{manifest['gate_probe_command']}</div>
        <div class="cmd">python tools/analysis/check_split_models_operational_conversion_state.py</div>
      </div>
      <div class="panel">
        <h2>지금 보면 되는 파일</h2>
        <div class="cmd">{manifest['primary_read_file']}</div>
        <div class="small">
          사람이 볼 때는 doctor, 프로세스가 판정할 때는 probe, 원본 상태는 current_state.json 하나만 보면 됩니다.
        </div>
      </div>
    </section>
  </div>
</body>
</html>
"""

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(json.dumps({"dashboard_html": str(OUTPUT_HTML.relative_to(REPO_ROOT))}, indent=2))


if __name__ == "__main__":
    main()
