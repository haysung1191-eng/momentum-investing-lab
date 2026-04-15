from __future__ import annotations

import glob
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import pandas as pd


def is_valid_kr_name(name: str) -> bool:
    exclude_keywords = ["스팩", "리츠", "ETF", "ETN"]
    return not any(kw in str(name) for kw in exclude_keywords)


def filter_krx_listing(df: pd.DataFrame, *, name_validator: Callable[[str], bool] = is_valid_kr_name) -> list[tuple[str, str]]:
    if df is None or df.empty:
        return []

    market_col = "Market" if "Market" in df.columns else None
    if market_col:
        df = df[df[market_col].isin(["KOSPI", "KOSDAQ"])]

    df = df[df["Symbol"].astype(str).str.fullmatch(r"\d{6}")]

    result: list[tuple[str, str]] = []
    for _, row in df.iterrows():
        code = str(row["Symbol"])
        name = str(row["Name"])
        if name_validator(name):
            result.append((code, name))
    return result


def normalize_latest_results_universe(latest_df: pd.DataFrame | None) -> list[tuple[str, str]]:
    if latest_df is None or latest_df.empty:
        return []

    required = {"Code", "Name"}
    if not required.issubset(set(latest_df.columns)):
        return []

    latest_df = latest_df[["Code", "Name"]].dropna().drop_duplicates()
    latest_df["Code"] = latest_df["Code"].astype(str).str.zfill(6)
    latest_df = latest_df.sort_values("Code").reset_index(drop=True)
    return list(latest_df.itertuples(index=False, name=None))


def get_market_tickers_pykrx(
    *,
    now: datetime | None = None,
    sleep_sec: float = 0.3,
    name_validator: Callable[[str], bool] = is_valid_kr_name,
) -> list[tuple[str, str]]:
    from pykrx import stock as pykrx_stock

    tickers: list[tuple[str, str]] = []
    base_dt = now or datetime.today()
    for offset in range(10):
        target_dt = base_dt - timedelta(days=offset)
        target_str = target_dt.strftime("%Y%m%d")
        candidate: list[tuple[str, str]] = []

        for market in ["KOSPI", "KOSDAQ"]:
            codes = pykrx_stock.get_market_ticker_list(target_str, market=market)
            for code in codes:
                name = pykrx_stock.get_market_ticker_name(code)
                if name_validator(name):
                    candidate.append((code, name))
            time.sleep(sleep_sec)

        if candidate:
            print(f"티커 기준일(pykrx): {target_str}")
            tickers = candidate
            break

    return tickers


def get_market_tickers_fdr(
    *,
    name_validator: Callable[[str], bool] = is_valid_kr_name,
) -> list[tuple[str, str]]:
    import FinanceDataReader as fdr

    df = fdr.StockListing("KRX")
    return filter_krx_listing(df, name_validator=name_validator)


def get_market_tickers_from_latest_results(
    *,
    config_module,
    repo_root: Path,
    read_excel: Callable = pd.read_excel,
    print_fn: Callable[[str], None] = print,
) -> list[tuple[str, str]]:
    latest_df = None

    if getattr(config_module, "GCS_BUCKET_NAME", None):
        try:
            from google.cloud import storage

            storage_client = storage.Client()
            bucket = storage_client.bucket(config_module.GCS_BUCKET_NAME)
            blobs = list(bucket.list_blobs(prefix="momentum_results_"))
            if blobs:
                latest_blob = max(blobs, key=lambda b: b.updated)
                uri = f"gs://{config_module.GCS_BUCKET_NAME}/{latest_blob.name}"
                latest_df = read_excel(uri)
                print_fn(f"fallback 기준 파일(GCS): {latest_blob.name}")
        except Exception as e:
            print_fn(f"fallback GCS 로드 실패: {e}")

    if latest_df is None:
        try:
            files = glob.glob(str(repo_root / "momentum_results_*.xlsx"))
            if files:
                latest_file = max(files, key=os.path.getmtime)
                latest_df = read_excel(latest_file)
                print_fn(f"fallback 기준 파일(local): {latest_file}")
        except Exception as e:
            print_fn(f"fallback local 로드 실패: {e}")

    return normalize_latest_results_universe(latest_df)


def resolve_market_tickers(
    *,
    pykrx_loader: Callable[[], list[tuple[str, str]]],
    fdr_loader: Callable[[], list[tuple[str, str]]],
    latest_loader: Callable[[], list[tuple[str, str]]],
    print_fn: Callable[[str], None] = print,
) -> list[tuple[str, str]]:
    tickers: list[tuple[str, str]] = []
    try:
        tickers = pykrx_loader()
    except Exception as e:
        print_fn(f"pykrx 조회 실패: {e}")

    if not tickers:
        print_fn("pykrx 결과가 비어 FDR(KRX)로 대체 조회합니다.")
        try:
            tickers = fdr_loader()
        except Exception as e:
            print_fn(f"FDR 조회 실패: {e}")

    if not tickers:
        print_fn("FDR도 실패하여 최신 결과 파일 기준으로 티커를 복구합니다.")
        tickers = latest_loader()

    print_fn(f"전체 종목 수: {len(tickers)}개")
    return tickers


def get_historical_market_tickers(
    start_yyyymmdd: str,
    end_yyyymmdd: str,
    *,
    step_days: int = 30,
    sleep_sec: float = 0.05,
    name_validator: Callable[[str], bool] = is_valid_kr_name,
    fallback_loader: Callable[[], list[tuple[str, str]]] | None = None,
    print_fn: Callable[[str], None] = print,
) -> list[tuple[str, str]]:
    from pykrx import stock as pykrx_stock

    start_dt = datetime.strptime(start_yyyymmdd, "%Y%m%d")
    end_dt = datetime.strptime(end_yyyymmdd, "%Y%m%d")
    if end_dt < start_dt:
        start_dt, end_dt = end_dt, start_dt

    union: dict[str, str] = {}
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
                if name_validator(name):
                    union[str(code).zfill(6)] = name
            time.sleep(sleep_sec)
        snap_count += 1
        dt += timedelta(days=max(7, step_days))

    if not union:
        print_fn("historical universe 생성 실패, 현재 유니버스로 대체합니다.")
        return fallback_loader() if fallback_loader is not None else []

    out = sorted(union.items(), key=lambda x: x[0])
    print_fn(f"historical universe 스냅샷={snap_count}, 종목수={len(out)}")
    return out


def get_etf_tickers(
    *,
    print_fn: Callable[[str], None] = print,
) -> list[tuple[str, str]]:
    import FinanceDataReader as fdr

    print_fn("국내 ETF 목록 다운로드 중...")
    df = fdr.StockListing("ETF/KR")
    tickers = sorted(list(zip(df["Symbol"], df["Name"])), key=lambda x: str(x[0]))
    print_fn(f"ETF 총 개수: {len(tickers)}개")
    return tickers
