from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / 'outputs'

st.set_page_config(
    page_title='글로벌 플로우 옵저버 MVP',
    page_icon='🌐',
    layout='wide',
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1380px;
    }
    html, body, [class*="css"] {
        font-size: 17px !important;
    }
    .main h1 {
        font-size: 2.0rem !important;
        font-weight: 800 !important;
        margin-bottom: 0.2rem !important;
    }
    .main h2, .main h3 {
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        margin-top: 1.4rem !important;
    }
    .metric-card {
        background: #f7f9fc;
        border: 1px solid #dbe3ef;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 12px;
    }
    .metric-label {
        font-size: 1rem !important;
        color: #44546a;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        color: #0f172a;
        line-height: 1.2;
    }
    .explain {
        font-size: 1rem !important;
        color: #334155;
        background: #f8fafc;
        border-left: 5px solid #94a3b8;
        padding: 12px 14px;
        border-radius: 8px;
        margin: 8px 0 14px 0;
    }
    .small-note {
        font-size: 1rem !important;
        color: #475569;
    }
    .hero {
        background: linear-gradient(135deg, #f8fafc 0%, #eef4ff 100%);
        border: 1px solid #d8e3f2;
        border-radius: 16px;
        padding: 18px 20px;
        margin: 12px 0 16px 0;
    }
    .hero-title {
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        color: #0f172a;
        margin-bottom: 8px;
    }
    .hero-body {
        font-size: 1.02rem !important;
        color: #334155;
        line-height: 1.55;
    }
    .hero-chips {
        margin-top: 10px;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
    .hero-chip {
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.92rem !important;
        color: #334155;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1rem !important;
    }
    table {
        font-size: 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


REGIME_KR = {
    'Risk-On': '위험 선호',
    'Risk-Off': '위험 회피',
    'Inflation Tilt': '인플레이션 기울기',
    'Duration Bid': '장기채 선호',
    'Mixed': '혼합',
}

TICKER_KR = {
    'SPY': '미국 대형주',
    'EFA': '선진국 주식',
    'EEM': '신흥국 주식',
    'IEF': '미국 중기채',
    'TLT': '미국 장기채',
    'LQD': '미국 투자등급 회사채',
    'HYG': '미국 하이일드채',
    'GLD': '금',
    'PDBC': '원자재',
    'VNQ': '미국 리츠',
}


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(OUTPUT_DIR / name)


@st.cache_data(show_spinner=False)
def load_json(name: str) -> dict:
    return json.loads((OUTPUT_DIR / name).read_text(encoding='utf-8'))


def pct(x: float) -> str:
    return f'{x * 100:.1f}%'


def signed_pct(x: float) -> str:
    sign = '+' if x > 0 else ''
    return f'{sign}{x * 100:.1f}%'


def regime_text(raw: str) -> str:
    return REGIME_KR.get(raw, raw)


def ticker_text(ticker: str) -> str:
    name = TICKER_KR.get(ticker, '')
    return f'{ticker} ({name})' if name else ticker


status = load_json('top_status_bar.json')
regime_df = load_csv('current_regime_summary.csv')
leadership_df = load_csv('asset_leadership_table.csv')
risk_defense_df = load_csv('risk_vs_defense.csv')
equity_df = load_csv('equity_region_rotation.csv')
real_vs_fin_df = load_csv('real_assets_vs_financial_assets.csv')
heatmap_df = load_csv('trend_heatmap.csv')
change_df = load_csv('change_since_last_month.csv')
validation_df = load_csv('validation_summary.csv')
leadership_history_df = load_csv('leadership_history.csv')
regime_history_df = load_csv('regime_history.csv')

signal_date = str(regime_df.loc[0, 'SignalDate'])
regime_label = regime_text(str(regime_df.loc[0, 'Regime']))
leaders = ', '.join(f"{item['Ticker']}" for item in status['Top3Leaders3M'])
laggards = ', '.join(f"{item['Ticker']}" for item in status['Top3Laggards3M'])
spread = float(status['RiskVsDefenseSpread3M'])
spread_label = '위험 우위' if spread > 0 else ('방어 우위' if spread < 0 else '중립')
leader_rows = leadership_df.sort_values('Rank3M').reset_index(drop=True)
leader1 = leader_rows.iloc[0]
leader2 = leader_rows.iloc[1]
leader3 = leader_rows.iloc[2]
laggard_rows = leadership_df.sort_values('Rank3M', ascending=False).reset_index(drop=True)
weak1 = laggard_rows.iloc[0]
risk_row = risk_defense_df.iloc[0]
real_row = real_vs_fin_df.iloc[0]
prev_regime_row = regime_history_df.iloc[-2] if len(regime_history_df) >= 2 else None
regime_change_text = (
    f"전월과 동일 ({regime_label})"
    if prev_regime_row is not None and regime_text(str(prev_regime_row['Regime'])) == regime_label
    else (
        f"전월 {regime_text(str(prev_regime_row['Regime']))} → 이번 달 {regime_label}"
        if prev_regime_row is not None
        else "전월 비교 없음"
    )
)
leader_gap = float(leader1["R3M"] - leader2["R3M"])
leader_gap_text = f"{ticker_text(str(leader1['Ticker']))}가 2위보다 {signed_pct(leader_gap)} 앞섬"
current_read = (
    f"지금은 {regime_label} 국면입니다. 최근 3개월 기준으로 "
    f"{ticker_text(str(leader1['Ticker']))}, {ticker_text(str(leader2['Ticker']))}, "
    f"{ticker_text(str(leader3['Ticker']))}가 상위권이고, "
    f"{ticker_text(str(weak1['Ticker']))}는 상대적으로 약합니다. "
    f"위험자산 대비 방어자산 스프레드는 {signed_pct(float(risk_row['Spread3M']))}로 크지는 않지만 플러스이고, "
    f"실물자산 우위 스프레드는 {signed_pct(float(real_row['Spread3M']))}로 더 강합니다."
)
history_window = regime_history_df.tail(24).copy()
history_chart = history_window[
    ['SignalDate', 'RiskVsDefenseSpread3M', 'RealVsFinancialSpread3M', 'DurationStrength3M']
].copy()
history_chart['SignalDate'] = pd.to_datetime(history_chart['SignalDate'])
history_chart = history_chart.set_index('SignalDate')
recent_regime_table = history_window[['SignalDate', 'Regime', 'TopLeader3M', 'TopLaggard3M']].tail(12).copy()
recent_regime_table['Regime'] = recent_regime_table['Regime'].map(regime_text)
recent_regime_table['TopLeader3M'] = recent_regime_table['TopLeader3M'].map(ticker_text)
recent_regime_table['TopLaggard3M'] = recent_regime_table['TopLaggard3M'].map(ticker_text)
leader_history = (
    leadership_history_df[leadership_history_df['Rank3M'] <= 3]
    .sort_values(['SignalDate', 'Rank3M'])
    .tail(36)
    .copy()
)
leader_history['SignalDate'] = pd.to_datetime(leader_history['SignalDate']).dt.strftime('%Y-%m')
leader_history['자산'] = leader_history['Ticker'].map(ticker_text)
leader_history['3개월'] = leader_history['R3M'].map(pct)
has_prior_change = change_df['PriorRank3M'].notna().any()

st.title('글로벌 플로우 옵저버 MVP')
st.caption(f'기준일: {signal_date}')
st.markdown(
    (
        '<div class="hero">'
        f'<div class="hero-title">지금 결론: 실물자산 쪽으로 돈이 더 강하게 기울어 있습니다.</div>'
        f'<div class="hero-body">{current_read}</div>'
        '<div class="hero-chips">'
        f'<div class="hero-chip">레짐 변화: {regime_change_text}</div>'
        f'<div class="hero-chip">리더 우위: {leader_gap_text}</div>'
        f'<div class="hero-chip">가장 약한 자산: {ticker_text(str(weak1["Ticker"]))}</div>'
        '</div>'
        '</div>'
    ),
    unsafe_allow_html=True,
)

cols = st.columns(4)
with cols[0]:
    st.metric('현재 레짐', regime_label)
with cols[1]:
    st.metric('위험 vs 방어', spread_label, signed_pct(spread))
with cols[2]:
    st.metric('최상위 리더', str(leader1['Ticker']))
with cols[3]:
    st.metric('가장 약한 자산', str(weak1['Ticker']))

st.markdown(
    '<div class="explain">여기까지만 보면 됩니다. 지금은 실물자산 우위, 최상위 리더는 원자재(PDBC), 가장 약한 자산은 미국 대형주(SPY)입니다.</div>',
    unsafe_allow_html=True,
)

st.subheader('1. 현재 레짐 요약')
row = regime_df.iloc[0]
summary_cols = st.columns(5)
summary_cols[0].metric('레짐', regime_label)
summary_cols[1].metric('위험 바스켓 3개월', pct(float(row['RiskBasket3M'])))
summary_cols[2].metric('방어 바스켓 3개월', pct(float(row['DefenseBasket3M'])))
summary_cols[3].metric('실물자산 강도', pct(float(row['RealAssetsStrength3M'])))
summary_cols[4].metric('듀레이션 강도', pct(float(row['DurationStrength3M'])))
st.markdown(
    '<div class="explain">지금은 위험 바스켓 3개월 수익률이 0.3%, 방어 바스켓은 거의 0.0%입니다. 차이는 크지 않지만, 실물자산 강도는 13.5%로 훨씬 높아서 현재 레짐이 인플레이션 기울기로 잡힌 것입니다.</div>',
    unsafe_allow_html=True,
)

st.subheader('2. 위험자산 vs 방어자산')
row = risk_defense_df.iloc[0]
cols = st.columns(3)
cols[0].metric('위험 바스켓 3개월', pct(float(row['RiskBasket3M'])))
cols[1].metric('방어 바스켓 3개월', pct(float(row['DefenseBasket3M'])))
cols[2].metric('스프레드', signed_pct(float(row['Spread3M'])))
st.markdown(
    '<div class="explain">지금 스프레드는 +0.3% 수준이라 위험자산이 완전히 무너진 상태는 아닙니다. 다만 강한 위험선호라기보다, 전체 위험자산 중에서도 일부 자산군만 선별적으로 강한 상태에 가깝습니다.</div>',
    unsafe_allow_html=True,
)

st.subheader('3. 실물자산 vs 금융자산')
row = real_vs_fin_df.iloc[0]
cols = st.columns(3)
cols[0].metric('실물자산 3개월', pct(float(row['RealAssets3M'])))
cols[1].metric('금융자산 3개월', pct(float(row['FinancialAssets3M'])))
cols[2].metric('스프레드', signed_pct(float(row['Spread3M'])))
st.markdown(
    '<div class="explain">이 구간이 지금 화면에서 가장 강한 신호입니다. 실물자산 3개월 성과가 금융자산보다 14.5%p 높아서, 현재 자금 흐름은 금리자산보다 원자재, 금, 리츠 쪽에 더 강하게 반응하고 있습니다.</div>',
    unsafe_allow_html=True,
)

st.subheader('4. 주식 지역 로테이션')
equity_show = equity_df.copy()
equity_show['자산'] = equity_show['Ticker'].map(ticker_text)
equity_show['1개월'] = equity_show['R1M'].map(pct)
equity_show['3개월'] = equity_show['R3M'].map(pct)
equity_show['6개월'] = equity_show['R6M'].map(pct)
equity_show['순위'] = equity_show['Rank3M'].astype(int)
st.dataframe(equity_show[['순위', '자산', '1개월', '3개월', '6개월']], width='stretch', hide_index=True)
st.markdown(
    '<div class="explain">지역별로는 신흥국(EEM)이 가장 강하고, 그다음이 선진국(EFA), 미국(SPY)은 가장 약합니다. 현재 주식 자금 흐름이 미국 일변도가 아니라 해외 쪽으로 더 기울어 있다는 뜻입니다.</div>',
    unsafe_allow_html=True,
)

st.subheader('5. 자산 리더십 표')
leadership_show = leadership_df.copy()
leadership_show['자산'] = leadership_show['Ticker'].map(ticker_text)
leadership_show['3개월'] = leadership_show['R3M'].map(pct)
leadership_show['12개월'] = leadership_show['R12M'].map(pct)
leadership_show['순위(3개월)'] = leadership_show['Rank3M'].astype(int)
st.dataframe(
    leadership_show[['순위(3개월)', '자산', '3개월', '12개월']],
    width='stretch',
    hide_index=True,
)
st.markdown(
    '<div class="explain">현재 리더십은 PDBC 1위, GLD 2위, EEM 3위입니다. 즉 자금이 미국 대표 주식보다 원자재, 금, 신흥국 쪽으로 더 강하게 이동한 흔적이 보입니다.</div>',
    unsafe_allow_html=True,
)

st.subheader('6. 트렌드 히트맵')
heatmap_show = heatmap_df.copy()
heatmap_show['자산'] = heatmap_show['Ticker'].map(ticker_text)
heatmap_show = heatmap_show[['자산', 'R1M', 'R3M', 'R6M', 'R12M']].set_index('자산')
st.dataframe(
    heatmap_show.style.format('{:.1%}').background_gradient(cmap='RdYlGn', axis=None),
    width='stretch',
)
st.markdown(
    '<div class="explain">지금 히트맵에서는 PDBC와 GLD가 중기 구간까지 상대적으로 강하고, SPY는 최근 1개월과 3개월이 약합니다. 단기 흔들림이 아니라 자산군 리더십 자체가 바뀌는지 확인하는 용도입니다.</div>',
    unsafe_allow_html=True,
)

st.subheader('7. 최근 24개월 큰 흐름')
st.line_chart(
    history_chart.rename(
        columns={
            'RiskVsDefenseSpread3M': '위험-방어 스프레드',
            'RealVsFinancialSpread3M': '실물-금융 스프레드',
            'DurationStrength3M': '듀레이션 강도',
        }
    ),
    height=240,
)
st.markdown(
    '<div class="explain">이 선들은 현재 상태가 우연인지, 최근 월별 흐름 위에서 나온 것인지 확인하는 구간입니다. 지금은 실물-금융 스프레드가 최근 구간에서 확실히 위쪽에 있습니다.</div>',
    unsafe_allow_html=True,
)

st.subheader('8. 최근 12개월 레짐과 리더 변화')
st.dataframe(
    recent_regime_table.rename(
        columns={
            'SignalDate': '기준월',
            'Regime': '레짐',
            'TopLeader3M': '상위 리더',
            'TopLaggard3M': '하위 약세',
        }
    ),
    width='stretch',
    hide_index=True,
)
st.markdown(
    '<div class="explain">이 표는 전월 대비 레짐 전환과 리더 교체를 한 번에 보는 구간입니다. 현재 판단이 이전 달과 얼마나 달라졌는지 여기서 확인합니다.</div>',
    unsafe_allow_html=True,
)

if has_prior_change:
    st.subheader('9. 전월 대비 순위 변화')
    change_show = change_df.copy()
    change_show['자산'] = change_show['Ticker'].map(ticker_text)
    change_show['현재 순위'] = change_show['Rank3M'].astype(int)
    change_show['전월 순위'] = change_show['PriorRank3M'].apply(lambda x: '-' if pd.isna(x) else int(x))
    change_show['순위 변화'] = change_show['RankChange'].apply(lambda x: '신규/비교불가' if pd.isna(x) else int(x))
    st.dataframe(change_show[['자산', '현재 순위', '전월 순위', '순위 변화']], width='stretch', hide_index=True)
    st.markdown(
        '<div class="explain">순위 변화는 어떤 자산이 한 달 사이에 급하게 올라오거나 밀렸는지 보는 보조 표입니다.</div>',
        unsafe_allow_html=True,
    )

# Validation footer
validation_row = validation_df.iloc[0].to_dict()
validation_text = ' | '.join(f'{k}: {v}' for k, v in validation_row.items())
st.markdown(f'<div class="small-note">검증 상태: {validation_text}</div>', unsafe_allow_html=True)
