import json
import os
from datetime import datetime, timedelta

import requests

import config


class KISApi:
    TOKEN_FILE = os.path.join(os.path.dirname(__file__), ".token_cache.json")

    def __init__(self):
        self.base_url = config.BASE_URL
        self.app_key = config.APP_KEY
        self.app_secret = config.APP_SECRET
        self.access_token = None
        self._load_or_refresh_token()

    def _read_local_cache(self):
        if not os.path.exists(self.TOKEN_FILE):
            return {}
        try:
            with open(self.TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_local_cache(self, cache_data):
        with open(self.TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

    def _read_gcs_cache(self):
        from google.cloud import storage

        storage_client = storage.Client()
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        blob = bucket.blob(".token_cache.json")
        if not blob.exists():
            return {}
        return json.loads(blob.download_as_string())

    def _write_gcs_cache(self, cache_data):
        from google.cloud import storage

        storage_client = storage.Client()
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        blob = bucket.blob(".token_cache.json")
        blob.upload_from_string(json.dumps(cache_data))

    def _load_or_refresh_token(self):
        import time

        use_gcs = bool(getattr(config, "GCS_BUCKET_NAME", None))
        cache = {}

        if use_gcs:
            try:
                cache = self._read_gcs_cache()
                if cache:
                    print("토큰 캐시 로드 완료 (GCS)")
            except Exception as e:
                print(f"GCS 토큰 캐시 로드 실패, 로컬 캐시로 전환: {e}")
                cache = self._read_local_cache()
        else:
            cache = self._read_local_cache()

        if cache and time.time() - cache.get("timestamp", 0) < 86400:
            self.access_token = cache.get("token")
            if self.access_token:
                print("캐시된 토큰 로드 완료")
                return

        self._request_token()

    def _request_token(self):
        import time

        print("토큰 발급 중...")
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=15)
        if res.status_code != 200:
            print("토큰 발급 실패:", res.status_code, res.text)
            raise Exception("Access Token Error")

        self.access_token = res.json().get("access_token")
        cache_data = {"token": self.access_token, "timestamp": time.time()}

        use_gcs = bool(getattr(config, "GCS_BUCKET_NAME", None))
        if use_gcs:
            try:
                self._write_gcs_cache(cache_data)
                print("토큰 발급 완료 (GCS 캐시 저장)")
                return
            except Exception as e:
                print(f"GCS 토큰 캐시 저장 실패, 로컬 캐시로 전환: {e}")

        self._write_local_cache(cache_data)
        print("토큰 발급 완료 (로컬 캐시 저장)")

    def get_headers(self, tr_id):
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }

    def get_historical_prices(self, symbol, start_date, end_date, period="D", max_records=260):
        import time

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        all_prices = []
        current_end = end_date

        while len(all_prices) < max_records:
            headers = self.get_headers("FHKST03010100")
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": current_end,
                "FID_PERIOD_DIV_CODE": period,
                # Use adjusted price to reduce split/rights-induced return spikes.
                "FID_ORG_ADJ_PRC": "1",
            }

            res = None
            for attempt in range(3):
                try:
                    res = requests.get(url, headers=headers, params=params, timeout=10)
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    if attempt < 2:
                        time.sleep(2 ** (attempt + 1))
                    else:
                        print(f"[WARN] price request network fail symbol={symbol} end={current_end}")
                        return all_prices

            if res is None or res.status_code != 200:
                status = None if res is None else res.status_code
                text = "" if res is None else res.text[:240]
                print(f"[WARN] price request bad response symbol={symbol} status={status} body={text}")
                break

            body = res.json()
            data = body.get("output2", [])
            if not data:
                msg_cd = body.get("msg_cd", "")
                msg1 = body.get("msg1", "")
                rt_cd = body.get("rt_cd", "")
                if msg_cd or msg1 or rt_cd:
                    print(f"[WARN] empty price data symbol={symbol} rt_cd={rt_cd} msg_cd={msg_cd} msg={msg1}")
                break

            all_prices.extend(data)

            last_date = data[-1].get("stck_bsop_date", "")
            if not last_date or last_date <= start_date:
                break

            last_dt = datetime.strptime(last_date, "%Y%m%d")
            current_end = (last_dt - timedelta(days=1)).strftime("%Y%m%d")
            if current_end < start_date:
                break

            time.sleep(0.06)

        return all_prices[:max_records]


if __name__ == "__main__":
    api = KISApi()
    print("API 객체 생성 완료")
