from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

import config
from kis_api import KISApi
from live_core.kis_screener_metrics import calculate_momentum_metrics
from live_core.kis_screener_universe import (
    get_etf_tickers,
    get_historical_market_tickers,
    get_market_tickers_fdr,
    get_market_tickers_from_latest_results,
    get_market_tickers_pykrx,
    is_valid_kr_name,
    resolve_market_tickers,
)


class MomentumScreener:
    def __init__(self):
        self.api = KISApi()

    @staticmethod
    def _is_valid_name(name: str) -> bool:
        return is_valid_kr_name(name)

    def _get_market_tickers_pykrx(self):
        return get_market_tickers_pykrx(name_validator=self._is_valid_name)

    def _get_market_tickers_fdr(self):
        return get_market_tickers_fdr(name_validator=self._is_valid_name)

    def _get_market_tickers_from_latest_results(self):
        return get_market_tickers_from_latest_results(
            config_module=config,
            repo_root=Path(__file__).resolve().parent,
        )

    def get_market_tickers(self):
        print("국내 시장 전체 티커 다운로드 중...")
        return resolve_market_tickers(
            pykrx_loader=self._get_market_tickers_pykrx,
            fdr_loader=self._get_market_tickers_fdr,
            latest_loader=self._get_market_tickers_from_latest_results,
        )

    def get_historical_market_tickers(self, start_yyyymmdd: str, end_yyyymmdd: str, step_days: int = 30):
        return get_historical_market_tickers(
            start_yyyymmdd,
            end_yyyymmdd,
            step_days=step_days,
            name_validator=self._is_valid_name,
            fallback_loader=self.get_market_tickers,
        )

    def get_etf_tickers(self):
        return get_etf_tickers()

    def calculate_momentum(self, prices):
        return calculate_momentum_metrics(prices)

    def run(self, max_items=2500, etf_mode=False):
        if etf_mode:
            tickers = self.get_etf_tickers()
            mode_label = "ETF"
        else:
            tickers = self.get_market_tickers()
            mode_label = "개별종목"

        print(f"[{mode_label}] 스캔 대상: {len(tickers)}개")

        today_dt = datetime.today()
        while today_dt.weekday() >= 5:
            today_dt -= timedelta(days=1)

        past_dt = today_dt - timedelta(days=400)
        today_str = today_dt.strftime("%Y%m%d")
        past_str = past_dt.strftime("%Y%m%d")

        results = []
        total = min(len(tickers), max_items)

        for idx, (code, name) in enumerate(tickers[:max_items], start=1):
            log_interval = 20 if etf_mode else 50
            if idx % log_interval == 0:
                print(f"진행 상황: {idx}/{total} ({round(idx/total*100, 1)}%)")

            prices = self.api.get_historical_prices(code, past_str, today_str, "D")
            mom_data = self.calculate_momentum(prices)
            if mom_data:
                row = {"Code": code, "Name": name, "Type": mode_label}
                row.update(mom_data)
                results.append(row)

        df = pd.DataFrame(results)
        if not df.empty:
            sort_col = "avg_momentum" if etf_mode else "MAD_gap_pct"
            df = df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

        print(f"[{mode_label}] 스크리닝 완료. 결과 {len(df)}개")
        return df
