from pathlib import Path

import config
from kis_api import KISApi
from live_core.kis_screener_metrics import calculate_momentum_metrics
from live_core.kis_screener_runner import build_screening_frame
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
        else:
            tickers = self.get_market_tickers()
        return build_screening_frame(
            api=self.api,
            tickers=tickers,
            momentum_calculator=self.calculate_momentum,
            etf_mode=etf_mode,
            max_items=max_items,
        )
