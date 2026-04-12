import glob
import os
from io import BytesIO
from typing import Dict, List, Tuple

import pandas as pd


NEWS_COLUMNS = [
    "date",
    "article_count",
    "positive_hits",
    "negative_hits",
    "title_score",
]


def list_news_files(base: str, market: str = "stock") -> List[str]:
    if base.startswith("gs://"):
        from google.cloud import storage

        no_scheme = base.replace("gs://", "", 1)
        bucket_name, prefix = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=f"{prefix}/{market}/")
        return [f"gs://{bucket_name}/{b.name}" for b in blobs if b.name.endswith(".csv.gz")]
    return glob.glob(os.path.join(base, market, "*.csv.gz"))


def parse_gs_path(path: str) -> Tuple[str, str]:
    no_scheme = path.replace("gs://", "", 1)
    if "/" not in no_scheme:
        return no_scheme, ""
    bucket_name, blob_name = no_scheme.split("/", 1)
    return bucket_name, blob_name


def _coerce_schema(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in NEWS_COLUMNS:
        if col not in out.columns:
            out[col] = 0.0 if col != "date" else pd.NaT
    out = out[NEWS_COLUMNS].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    for col in NEWS_COLUMNS[1:]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    return out.dropna(subset=["date"]).drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)


def read_news_file(path: str) -> pd.DataFrame:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            bucket_name, blob_name = parse_gs_path(path)
            client = storage.Client()
            blob = client.bucket(bucket_name).blob(blob_name)
            if not blob.exists(client):
                return pd.DataFrame(columns=NEWS_COLUMNS)
            raw = blob.download_as_bytes()
            df = pd.read_csv(BytesIO(raw), compression="gzip", parse_dates=["date"])
        else:
            df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
    except Exception:
        return pd.DataFrame(columns=NEWS_COLUMNS)
    return _coerce_schema(df)


def write_news_file(path: str, df: pd.DataFrame) -> None:
    out = _coerce_schema(df)
    if path.startswith("gs://"):
        from google.cloud import storage

        bucket_name, blob_name = parse_gs_path(path)
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        buf = BytesIO()
        out.to_csv(buf, index=False, compression="gzip")
        buf.seek(0)
        blob.upload_from_file(buf, content_type="application/gzip")
        return
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    out.to_csv(path, index=False, compression="gzip")


def merge_news_frames(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if old.empty:
        return _coerce_schema(new)
    if new.empty:
        return _coerce_schema(old)
    return _coerce_schema(pd.concat([old, new], ignore_index=True))


def build_news_matrices(base: str, market: str = "stock") -> Dict[str, pd.DataFrame]:
    files = sorted(list_news_files(base, market))
    rows = []
    for path in files:
        symbol = os.path.basename(path).replace(".csv.gz", "")
        df = read_news_file(path)
        if df.empty:
            continue
        df = df.copy()
        df["symbol"] = symbol
        rows.append(df)
    if not rows:
        empty = pd.DataFrame()
        return {col: empty for col in NEWS_COLUMNS[1:]}

    long_df = pd.concat(rows, ignore_index=True)
    out: Dict[str, pd.DataFrame] = {}
    for col in NEWS_COLUMNS[1:]:
        out[col] = long_df.pivot(index="date", columns="symbol", values=col).sort_index()
    return out


def build_coverage_report(base: str, market: str = "stock") -> pd.DataFrame:
    rows = []
    for path in sorted(list_news_files(base, market)):
        symbol = os.path.basename(path).replace(".csv.gz", "")
        df = read_news_file(path)
        if df.empty:
            rows.append(
                {
                    "Symbol": symbol,
                    "RowCount": 0,
                    "FirstDate": "",
                    "LastDate": "",
                    "TotalArticles": 0,
                    "MeanArticleCount": 0.0,
                    "TotalTitleScore": 0.0,
                }
            )
            continue
        rows.append(
            {
                "Symbol": symbol,
                "RowCount": int(len(df)),
                "FirstDate": str(pd.to_datetime(df["date"]).min().date()),
                "LastDate": str(pd.to_datetime(df["date"]).max().date()),
                "TotalArticles": float(pd.to_numeric(df["article_count"], errors="coerce").fillna(0.0).sum()),
                "MeanArticleCount": float(pd.to_numeric(df["article_count"], errors="coerce").fillna(0.0).mean()),
                "TotalTitleScore": float(pd.to_numeric(df["title_score"], errors="coerce").fillna(0.0).sum()),
            }
        )
    return pd.DataFrame(rows)
