from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

import pandas as pd


def resolve_screening_window(now: datetime | None = None) -> tuple[str, str]:
    today_dt = now or datetime.today()
    while today_dt.weekday() >= 5:
        today_dt -= timedelta(days=1)

    past_dt = today_dt - timedelta(days=400)
    return past_dt.strftime("%Y%m%d"), today_dt.strftime("%Y%m%d")


def build_screening_frame(
    *,
    api,
    tickers: list[tuple[str, str]],
    momentum_calculator: Callable[[list[dict]], dict | None],
    etf_mode: bool = False,
    max_items: int = 2500,
    print_fn: Callable[[str], None] = print,
    now: datetime | None = None,
) -> pd.DataFrame:
    mode_label = "ETF" if etf_mode else "개별종목"
    print_fn(f"[{mode_label}] 스캔 대상: {len(tickers)}개")

    past_str, today_str = resolve_screening_window(now=now)
    results: list[dict] = []
    total = min(len(tickers), max_items)

    for idx, (code, name) in enumerate(tickers[:max_items], start=1):
        log_interval = 20 if etf_mode else 50
        if idx % log_interval == 0:
            print_fn(f"진행 상황: {idx}/{total} ({round(idx/total*100, 1)}%)")

        prices = api.get_historical_prices(code, past_str, today_str, "D")
        mom_data = momentum_calculator(prices)
        if mom_data:
            row = {"Code": code, "Name": name, "Type": mode_label}
            row.update(mom_data)
            results.append(row)

    df = pd.DataFrame(results)
    if not df.empty:
        sort_col = "avg_momentum" if etf_mode else "MAD_gap_pct"
        df = df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

    print_fn(f"[{mode_label}] 스크리닝 완료. 결과 {len(df)}개")
    return df
