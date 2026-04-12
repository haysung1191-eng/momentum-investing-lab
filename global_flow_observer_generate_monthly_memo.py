from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / 'global_flow_observer' / 'outputs'
ARCHIVE_DIR = ROOT / 'global_flow_observer' / 'memos'
CURRENT_MEMO_PATH = ROOT / 'GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO_CURRENT.md'
TEMPLATE_PATH = ROOT / 'GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO_TEMPLATE.md'
MEMO_INDEX_PATH = ARCHIVE_DIR / 'memo_index.csv'


def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(OUTPUT_DIR / name)


def pct(x: float) -> str:
    return f'{x:.1%}'


def build_memo() -> tuple[str, str, dict]:
    regime = load_csv('current_regime_summary.csv').iloc[0]
    leadership = load_csv('asset_leadership_table.csv').sort_values('Rank3M')
    equity = load_csv('equity_region_rotation.csv').sort_values('Rank3M')
    real_vs_fin = load_csv('real_assets_vs_financial_assets.csv').iloc[0]
    change = load_csv('change_since_last_month.csv').sort_values('Rank3M')
    top_status = json.loads((OUTPUT_DIR / 'top_status_bar.json').read_text(encoding='utf-8'))

    signal_date = str(regime['SignalDate'])
    current_regime = str(regime['Regime'])
    top3 = leadership.head(3)['Ticker'].tolist()
    bottom3 = leadership.tail(3)['Ticker'].tolist()
    strongest = top3[0]
    weakest = bottom3[-1]
    risk_spread = float(top_status['RiskVsDefenseSpread3M'])
    real_spread = float(real_vs_fin['Spread3M'])
    equity_leader = str(equity.iloc[0]['Ticker'])
    equity_laggard = str(equity.iloc[-1]['Ticker'])
    meaningful_change = 'No meaningful rank change versus last month.' if change['RankChange'].fillna(0).abs().sum() == 0 else 'There was a meaningful rank change versus last month.'

    if current_regime == 'Inflation Tilt':
        regime_meaning = 'Leadership is concentrated in real assets rather than broad financial assets.'
        practical = 'Tilt interpretation favors real assets and selective non-US strength over a default US-equity-first stance.'
        may_justify = 'A cautious tilt toward real assets and away from default US-equity concentration.'
        does_not = 'An aggressive concentration move or a high-conviction directional call on its own.'
    elif current_regime == 'Risk-On':
        regime_meaning = 'Capital is favoring risk assets over defensive assets.'
        practical = 'Tilt interpretation supports broader risk exposure, but still through diversified allocation rather than concentration.'
        may_justify = 'A moderate increase in risk exposure.'
        does_not = 'Ignoring drawdown control or concentration risk.'
    elif current_regime == 'Risk-Off':
        regime_meaning = 'Capital is favoring defense over risk assets.'
        practical = 'Tilt interpretation supports defensive posture and caution toward broad equity beta.'
        may_justify = 'Higher allocation to defensive assets.'
        does_not = 'Assuming a full crisis regime without further evidence.'
    elif current_regime == 'Duration Bid':
        regime_meaning = 'Duration-sensitive assets are leading over risk assets.'
        practical = 'Tilt interpretation supports duration exposure over broad risk-taking.'
        may_justify = 'Higher interest-rate-sensitive defensive exposure.'
        does_not = 'A broad inflation-risk posture.'
    else:
        regime_meaning = 'Leadership is mixed and not cleanly concentrated in one major regime.'
        practical = 'Tilt interpretation supports diversification and caution rather than strong directional conviction.'
        may_justify = 'Balanced exposure with limited concentration.'
        does_not = 'A hard conviction move.'

    risk_read = 'Risk-positive' if risk_spread > 0 else 'Defense-positive'
    risk_strength = 'Strong' if abs(risk_spread) >= 0.05 else 'Weak to moderate'
    risk_interp = 'This is not a clean risk-off month, but it is also not strong enough to justify broad aggressive expansion.' if risk_spread > 0 else 'This month leans defensive rather than broad risk-taking.'

    real_read = 'Real assets stronger than financial assets' if real_spread > 0 else 'Financial assets stronger than real assets'
    real_strength = 'Strong' if abs(real_spread) >= 0.05 else 'Weak to moderate'
    real_interp = 'This is the clearest cross-asset message in the current observer state.' if abs(real_spread) >= 0.05 else 'This is present, but not decisive.'

    confidence = 'Moderate' if abs(real_spread) >= 0.05 or abs(risk_spread) >= 0.05 else 'Low to moderate'
    final_verdict = 'Useful as a regime and tilt observer, but not strong enough on its own to justify an aggressive allocation change.'
    supervisor = f'This month looks more like selective leadership in {strongest} and related areas than broad market strength.'

    memo = f'''# GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO_CURRENT\n\n## 1. Current Regime\n- Current regime: {current_regime}\n- One-line meaning: {regime_meaning}\n\n## 2. Key Cross-Asset Message\n- Core message this month: The clearest current rotation is toward {strongest} and related leadership rather than broad US-equity strength.\n- Strongest area of capital rotation: {', '.join(top3)}\n- Weakest area of capital rotation: {', '.join(bottom3)}\n\n## 3. Risk vs Defense Read\n- Risk vs defense reading: {risk_read}\n- Strength of the signal: {risk_strength}. The 3-month spread is {pct(risk_spread)}.\n- Operator interpretation: {risk_interp}\n\n## 4. Equity Region Rotation Read\n- Relative equity leader: {equity_leader}\n- Relative equity laggard: {equity_laggard}\n- Operator interpretation: Equity leadership is not centered on US equities this month.\n\n## 5. Real Assets vs Financial Assets Read\n- Real assets vs financial assets reading: {real_read}\n- Strength of the signal: {real_strength}. The 3-month spread is {pct(real_spread)}.\n- Operator interpretation: {real_interp}\n\n## 6. Leadership and Trend Change\n- Current top leaders: {', '.join(top3)}\n- Current laggards: {', '.join(bottom3)}\n- Meaningful change vs last month: {meaningful_change}\n\n## 7. Practical Allocation Interpretation\n- This month's practical read: {practical}\n- What this may justify: {may_justify}\n- What this does not justify: {does_not}\n\n## 8. What This Supports\n- Decision type 1: Whether to lean toward real assets versus financial assets this month.\n- Decision type 2: Whether US equities should be treated as leadership or lagging exposure.\n- Decision type 3: Whether the month reads as broad risk-on, defensive, or mixed with selective leadership.\n\n## 9. What It Does Not Prove\n- Limitation 1: It does not prove that following this read will outperform a passive benchmark.\n- Limitation 2: It does not prove that the current regime label is predictive rather than descriptive.\n- Limitation 3: It does not prove that current leaders will continue to lead next month.\n\n## 10. Final Monthly Verdict\n- Final monthly verdict: {final_verdict}\n- Confidence level: {confidence}\n- One-line supervisor summary: {supervisor}\n'''
    ledger_row = {
        'SignalDate': signal_date,
        'Regime': current_regime,
        'Strongest': strongest,
        'Weakest': weakest,
        'RiskVsDefenseSpread3M': risk_spread,
        'RealVsFinancialSpread3M': real_spread,
        'FinalMonthlyVerdict': final_verdict,
        'Confidence': confidence,
    }
    return signal_date, memo, ledger_row


def update_index(ledger_row: dict) -> None:
    row_df = pd.DataFrame([ledger_row])
    if MEMO_INDEX_PATH.exists():
        existing = pd.read_csv(MEMO_INDEX_PATH, dtype={'SignalDate': str})
        existing = existing[existing['SignalDate'] != ledger_row['SignalDate']].copy()
        out = pd.concat([existing, row_df], ignore_index=True)
    else:
        out = row_df
    out = out.sort_values('SignalDate').reset_index(drop=True)
    out.to_csv(MEMO_INDEX_PATH, index=False, encoding='utf-8-sig')


def main() -> None:
    _ = TEMPLATE_PATH.read_text(encoding='utf-8')
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    signal_date, memo, ledger_row = build_memo()
    CURRENT_MEMO_PATH.write_text(memo, encoding='utf-8')
    archive_path = ARCHIVE_DIR / f'{signal_date}_GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO.md'
    archive_path.write_text(memo.replace('GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO_CURRENT', f'GLOBAL_FLOW_OBSERVER_MONTHLY_MEMO_{signal_date}'), encoding='utf-8')
    update_index(ledger_row)
    print(str(archive_path))


if __name__ == '__main__':
    main()
