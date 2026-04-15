from pathlib import Path

import config
from kis_api import KISApi
from live_core.kis_screener_metrics import calculate_momentum_metrics
from live_core.kis_screening_service import run_default_screening
from live_core.kis_screener_universe import (
    get_current_stock_universe,
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
        return get_current_stock_universe(
            config_module=config,
            repo_root=Path(__file__).resolve().parent,
            name_validator=self._is_valid_name,
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
        return run_default_screening(
            etf_mode=etf_mode,
            max_items=max_items,
            config_module=config,
            repo_root=Path(__file__).resolve().parent,
            api_factory=lambda: self.api,
            momentum_calculator=self.calculate_momentum,
        )
