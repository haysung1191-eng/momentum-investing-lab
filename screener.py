import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

import config
from kis_api import KISApi
from live_core.kis_screener_metrics import calculate_momentum_metrics
from live_core.kis_screener_universe import (
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
        """Build stock universe from historical listing snapshots to reduce survivorship bias."""
        from pykrx import stock as pykrx_stock

        start_dt = datetime.strptime(start_yyyymmdd, "%Y%m%d")
        end_dt = datetime.strptime(end_yyyymmdd, "%Y%m%d")
        if end_dt < start_dt:
            start_dt, end_dt = end_dt, start_dt

        union = {}
        dt = start_dt
        snap_count = 0
        while dt <= end_dt:
            d = dt.strftime("%Y%m%d")
            for market in ["KOSPI", "KOSDAQ"]:
                try:
                    codes = pykrx_stock.get_market_ticker_list(d, market=market)
                except Exception:
                    codes = []
                for code in codes:
                    try:
                        name = pykrx_stock.get_market_ticker_name(code)
                    except Exception:
                        continue
                    if self._is_valid_name(name):
                        union[str(code).zfill(6)] = name
                time.sleep(0.05)
            snap_count += 1
            dt += timedelta(days=max(7, step_days))

        if not union:
            print("historical universe 생성 실패, 현재 유니버스로 대체합니다.")
            return self.get_market_tickers()

        out = sorted(union.items(), key=lambda x: x[0])
        print(f"historical universe 스냅샷={snap_count}, 종목수={len(out)}")
        return out

    def get_etf_tickers(self):
        print("국내 ETF 목록 다운로드 중...")
        import FinanceDataReader as fdr

        df = fdr.StockListing("ETF/KR")
        tickers = sorted(list(zip(df["Symbol"], df["Name"])), key=lambda x: str(x[0]))
        print(f"ETF 총 개수: {len(tickers)}개")
        return tickers

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
