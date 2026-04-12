from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
REGIME_HISTORY_PATH = ROOT / 'global_flow_observer' / 'outputs' / 'regime_history.csv'
PRICE_DIR = ROOT / 'data' / 'prices_us_etf_dm_v1' / 'etf'
OUTPUT_DIR = ROOT / 'backtests' / 'global_flow_observer_first_model_mapping_correction_run'

UNIVERSE = ['SPY', 'EFA', 'EEM', 'IEF', 'TLT', 'GLD', 'PDBC', 'BIL']
ONE_WAY_COST_BPS = 10
ONE_WAY_COST_RATE = ONE_WAY_COST_BPS / 10000.0
REGIME_WEIGHTS = {
    'Risk-On': {'SPY': 0.35, 'EFA': 0.15, 'EEM': 0.15, 'IEF': 0.20, 'GLD': 0.05, 'PDBC': 0.05, 'BIL': 0.05},
    'Risk-Off': {'IEF': 0.45, 'TLT': 0.25, 'BIL': 0.30},
    'Inflation Tilt': {'GLD': 0.25, 'PDBC': 0.25, 'EEM': 0.10, 'IEF': 0.20, 'BIL': 0.20},
    'Duration Bid': {'TLT': 0.35, 'IEF': 0.35, 'BIL': 0.30},
    'Mixed': {'SPY': 0.15, 'EFA': 0.10, 'EEM': 0.05, 'IEF': 0.25, 'TLT': 0.10, 'GLD': 0.10, 'PDBC': 0.10, 'BIL': 0.15},
}


def load_close_matrix() -> pd.DataFrame:
    series = []
    for ticker in UNIVERSE:
        path = PRICE_DIR / f'{ticker}.csv.gz'
        df = pd.read_csv(path, compression='gzip', parse_dates=['date'])
        df = df[['date', 'close']].copy()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df = df.dropna(subset=['date', 'close'])
        df = df[df['close'] > 0].drop_duplicates(subset=['date']).sort_values('date')
        series.append(pd.Series(df['close'].values, index=pd.to_datetime(df['date']), name=ticker))
    close = pd.concat(series, axis=1).sort_index().dropna(how='any')
    if close.empty:
        raise ValueError('no common close matrix')
    return close


def next_trade_date(index: pd.DatetimeIndex, ts: pd.Timestamp) -> pd.Timestamp | None:
    later = index[index > ts]
    return pd.Timestamp(later[0]) if len(later) else None


def build_schedule(close: pd.DataFrame) -> pd.DataFrame:
    regime_history = pd.read_csv(REGIME_HISTORY_PATH, parse_dates=['SignalDate'])
    rows = []
    for rec in regime_history.to_dict(orient='records'):
        signal_date = pd.Timestamp(rec['SignalDate'])
        execution_date = next_trade_date(close.index, signal_date)
        if execution_date is None:
            continue
        weights = {ticker: 0.0 for ticker in UNIVERSE}
        for ticker, weight in REGIME_WEIGHTS[rec['Regime']].items():
            weights[ticker] = float(weight)
        row = {'SignalDate': signal_date.strftime('%Y-%m-%d'), 'ExecutionDate': execution_date.strftime('%Y-%m-%d'), 'Regime': rec['Regime']}
        row.update(weights)
        rows.append(row)
    schedule = pd.DataFrame(rows)
    if schedule.empty:
        raise ValueError('empty allocation schedule')
    return schedule


def build_target_weights(close: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
    target = pd.DataFrame(0.0, index=close.index, columns=UNIVERSE)
    for _, row in schedule.iterrows():
        execution_date = pd.Timestamp(row['ExecutionDate'])
        if execution_date not in target.index:
            continue
        target.loc[execution_date, UNIVERSE] = [float(row[ticker]) for ticker in UNIVERSE]
    target = target.mask(target.eq(0.0), other=float('nan')).ffill().fillna(0.0)
    first_exec = pd.Timestamp(schedule['ExecutionDate'].iloc[0])
    return target.loc[first_exec:].copy()


def compute_cost_series(target: pd.DataFrame) -> pd.Series:
    prev = pd.Series(0.0, index=UNIVERSE)
    costs = pd.Series(0.0, index=target.index)
    for date in target.index:
        curr = target.loc[date]
        turnover_one_way = 0.5 * float((curr - prev).abs().sum())
        costs.loc[date] = turnover_one_way * ONE_WAY_COST_RATE
        prev = curr.copy()
    return costs


def compute_navs(close: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    close = close.loc[target.index].copy()
    returns = close.pct_change().fillna(0.0)
    shifted = target.shift(1).fillna(0.0)
    gross_daily = (shifted * returns[UNIVERSE]).sum(axis=1)
    costs = compute_cost_series(target)
    net_daily = (1.0 + gross_daily) * (1.0 - costs) - 1.0
    gross_nav = (1.0 + gross_daily).cumprod()
    net_nav = (1.0 + net_daily).cumprod()
    return pd.DataFrame({
        'Date': target.index.strftime('%Y-%m-%d'),
        'GrossDailyReturn': gross_daily.values,
        'NetDailyReturn': net_daily.values,
        'TurnoverOneWay': (costs / ONE_WAY_COST_RATE).values,
        'CostApplied': costs.values,
        'GrossNAV': gross_nav.values,
        'NetNAV': net_nav.values,
    })


def compute_benchmark(close: pd.DataFrame, start_date: pd.Timestamp) -> pd.DataFrame:
    spy = close.loc[start_date:, ['SPY']].copy()
    ret = spy['SPY'].pct_change().fillna(0.0)
    nav = (1.0 + ret).cumprod()
    return pd.DataFrame({'Date': spy.index.strftime('%Y-%m-%d'), 'SPYDailyReturn': ret.values, 'SPYNAV': nav.values})


def summarize(nav: pd.DataFrame, benchmark: pd.DataFrame, schedule: pd.DataFrame) -> dict:
    start = pd.Timestamp(nav['Date'].iloc[0])
    end = pd.Timestamp(nav['Date'].iloc[-1])
    years = max((end - start).days / 365.25, 1e-9)

    def mdd(series: pd.Series) -> float:
        hwm = series.cummax()
        return float((series / hwm - 1.0).min())

    gross_final = float(nav['GrossNAV'].iloc[-1])
    net_final = float(nav['NetNAV'].iloc[-1])
    spy_final = float(benchmark['SPYNAV'].iloc[-1])
    gross_cagr = gross_final ** (1.0 / years) - 1.0
    net_cagr = net_final ** (1.0 / years) - 1.0
    spy_cagr = spy_final ** (1.0 / years) - 1.0
    gross_vol = float(nav['GrossDailyReturn'].std(ddof=0) * math.sqrt(252))
    net_vol = float(nav['NetDailyReturn'].std(ddof=0) * math.sqrt(252))
    spy_vol = float(benchmark['SPYDailyReturn'].std(ddof=0) * math.sqrt(252))
    gross_sharpe = float(nav['GrossDailyReturn'].mean() / (nav['GrossDailyReturn'].std(ddof=0) + 1e-12) * math.sqrt(252))
    net_sharpe = float(nav['NetDailyReturn'].mean() / (nav['NetDailyReturn'].std(ddof=0) + 1e-12) * math.sqrt(252))
    spy_sharpe = float(benchmark['SPYDailyReturn'].mean() / (benchmark['SPYDailyReturn'].std(ddof=0) + 1e-12) * math.sqrt(252))
    gross_mdd = mdd(nav['GrossNAV'])
    net_mdd = mdd(nav['NetNAV'])
    spy_mdd = mdd(benchmark['SPYNAV'])
    avg_turnover = float(nav['TurnoverOneWay'].mean())
    annual_turnover = avg_turnover * 12.0
    regime_counts = schedule['Regime'].value_counts().sort_index().to_dict()
    drawdown_improvement = net_mdd - spy_mdd
    clearly_better_drawdown = drawdown_improvement >= 0.05

    if net_sharpe <= 0.5:
        verdict = 'FAIL'
        failure_reason = 'net Sharpe <= 0.5'
    elif net_cagr < spy_cagr and not clearly_better_drawdown:
        verdict = 'FAIL'
        failure_reason = 'net CAGR trails SPY without better drawdown'
    else:
        verdict = 'PASS'
        failure_reason = ''

    return {
        'start_date': str(start.date()),
        'end_date': str(end.date()),
        'months': int(len(schedule)),
        'gross_cagr': float(gross_cagr),
        'net_cagr': float(net_cagr),
        'spy_cagr': float(spy_cagr),
        'gross_final_nav': gross_final,
        'net_final_nav': net_final,
        'spy_final_nav': spy_final,
        'gross_max_drawdown': gross_mdd,
        'net_max_drawdown': net_mdd,
        'spy_max_drawdown': spy_mdd,
        'gross_volatility': gross_vol,
        'net_volatility': net_vol,
        'spy_volatility': spy_vol,
        'gross_sharpe': gross_sharpe,
        'net_sharpe': net_sharpe,
        'spy_sharpe': spy_sharpe,
        'drawdown_improvement_vs_spy': drawdown_improvement,
        'avg_monthly_turnover_one_way': avg_turnover,
        'annualized_turnover_one_way': annual_turnover,
        'cost_bps_one_way': ONE_WAY_COST_BPS,
        'verdict': verdict,
        'failure_reason': failure_reason,
        'regime_counts': regime_counts,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    close = load_close_matrix()
    schedule = build_schedule(close)
    target = build_target_weights(close, schedule)
    nav = compute_navs(close, target)
    benchmark = compute_benchmark(close, pd.Timestamp(nav['Date'].iloc[0]))
    summary = summarize(nav, benchmark, schedule)

    schedule.to_csv(OUTPUT_DIR / 'allocation_schedule.csv', index=False, encoding='utf-8-sig')
    nav.to_csv(OUTPUT_DIR / 'daily_nav.csv', index=False, encoding='utf-8-sig')
    benchmark.to_csv(OUTPUT_DIR / 'benchmark_spy.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame([summary]).drop(columns=['regime_counts']).to_csv(OUTPUT_DIR / 'run_summary.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(sorted(summary['regime_counts'].items()), columns=['Regime', 'Count']).to_csv(OUTPUT_DIR / 'regime_counts.csv', index=False, encoding='utf-8-sig')
    (OUTPUT_DIR / 'run_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(pd.DataFrame([summary]).drop(columns=['regime_counts']).to_string(index=False))


if __name__ == '__main__':
    main()
