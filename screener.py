import time
from datetime import datetime, timedelta

import pandas as pd

import config
from kis_api import KISApi
from live_core.kis_screener_metrics import calculate_momentum_metrics


class MomentumScreener:
    def __init__(self):
        self.api = KISApi()

    @staticmethod
    def _is_valid_name(name: str) -> bool:
        exclude_keywords = ["스팩", "리츠", "ETF", "ETN"]
        return not any(kw in name for kw in exclude_keywords)

    def _get_market_tickers_pykrx(self):
        from pykrx import stock as pykrx_stock

        tickers = []
        base_dt = datetime.today()
        for offset in range(10):
            target_dt = base_dt - timedelta(days=offset)
            target_str = target_dt.strftime("%Y%m%d")
            candidate = []

            for market in ["KOSPI", "KOSDAQ"]:
                codes = pykrx_stock.get_market_ticker_list(target_str, market=market)
                for code in codes:
                    name = pykrx_stock.get_market_ticker_name(code)
                    if self._is_valid_name(name):
                        candidate.append((code, name))
                time.sleep(0.3)

            if candidate:
                print(f"티커 기준일(pykrx): {target_str}")
                tickers = candidate
                break

        return tickers

    def _get_market_tickers_fdr(self):
        import FinanceDataReader as fdr

        df = fdr.StockListing("KRX")
        if df is None or df.empty:
            return []

        market_col = "Market" if "Market" in df.columns else None
        if market_col:
            df = df[df[market_col].isin(["KOSPI", "KOSDAQ"])]

        df = df[df["Symbol"].astype(str).str.fullmatch(r"\d{6}")]

        result = []
        for _, row in df.iterrows():
            code = str(row["Symbol"])
            name = str(row["Name"])
            if self._is_valid_name(name):
                result.append((code, name))

        return result

    def _get_market_tickers_from_latest_results(self):
        """Fallback: use code/name universe from latest momentum_results file."""
        latest_df = None

        if config.GCS_BUCKET_NAME:
            try:
                from google.cloud import storage

                storage_client = storage.Client()
                bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
                blobs = list(bucket.list_blobs(prefix="momentum_results_"))
                if blobs:
                    latest_blob = max(blobs, key=lambda b: b.updated)
                    uri = f"gs://{config.GCS_BUCKET_NAME}/{latest_blob.name}"
                    latest_df = pd.read_excel(uri)
                    print(f"fallback 기준 파일(GCS): {latest_blob.name}")
            except Exception as e:
                print(f"fallback GCS 로드 실패: {e}")

        if latest_df is None:
            try:
                import glob
                import os

                files = glob.glob(os.path.join(os.path.dirname(__file__), "momentum_results_*.xlsx"))
                if files:
                    latest_file = max(files, key=os.path.getmtime)
                    latest_df = pd.read_excel(latest_file)
                    print(f"fallback 기준 파일(local): {latest_file}")
            except Exception as e:
                print(f"fallback local 로드 실패: {e}")

        if latest_df is None or latest_df.empty:
            return []

        required = {"Code", "Name"}
        if not required.issubset(set(latest_df.columns)):
            return []

        latest_df = latest_df[["Code", "Name"]].dropna().drop_duplicates()
        latest_df["Code"] = latest_df["Code"].astype(str).str.zfill(6)
        latest_df = latest_df.sort_values("Code").reset_index(drop=True)
        return list(latest_df.itertuples(index=False, name=None))

    def get_market_tickers(self):
        print("국내 시장 전체 티커 다운로드 중...")

        tickers = []
        try:
            tickers = self._get_market_tickers_pykrx()
        except Exception as e:
            print(f"pykrx 조회 실패: {e}")

        if not tickers:
            print("pykrx 결과가 비어 FDR(KRX)로 대체 조회합니다.")
            try:
                tickers = self._get_market_tickers_fdr()
            except Exception as e:
                print(f"FDR 조회 실패: {e}")

        if not tickers:
            print("FDR도 실패하여 최신 결과 파일 기준으로 티커를 복구합니다.")
            tickers = self._get_market_tickers_from_latest_results()

        print(f"전체 종목 수: {len(tickers)}개")
        return tickers

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
