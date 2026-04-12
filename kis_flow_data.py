import glob
import os
from io import BytesIO
from typing import Dict, List, Tuple

import pandas as pd


FLOW_COLUMNS = [
    "date",
    "institution_net_volume",
    "foreign_net_volume",
    "foreign_shares",
    "foreign_ratio",
]


def list_flow_files(base: str, market: str = "stock") -> List[str]:
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
    for col in FLOW_COLUMNS:
        if col not in out.columns:
            out[col] = 0.0 if col != "date" else pd.NaT
    out = out[FLOW_COLUMNS].copy()
    for col in FLOW_COLUMNS[1:]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    return out.dropna(subset=["date"]).drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)


def read_flow_file(path: str) -> pd.DataFrame:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            bucket_name, blob_name = parse_gs_path(path)
            client = storage.Client()
            blob = client.bucket(bucket_name).blob(blob_name)
            if not blob.exists(client):
                return pd.DataFrame(columns=FLOW_COLUMNS)
            raw = blob.download_as_bytes()
            df = pd.read_csv(BytesIO(raw), compression="gzip", parse_dates=["date"])
        else:
            df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
    except Exception:
        return pd.DataFrame(columns=FLOW_COLUMNS)
    return _coerce_schema(df)


def write_flow_file(path: str, df: pd.DataFrame) -> None:
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


def merge_flow_frames(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if old.empty:
        return _coerce_schema(new)
    if new.empty:
        return _coerce_schema(old)
    out = pd.concat([old, new], ignore_index=True)
    return _coerce_schema(out)


def build_flow_matrices(base: str, market: str = "stock", max_files: int = 0) -> Dict[str, pd.DataFrame]:
    files = sorted(list_flow_files(base, market))
    if max_files > 0:
        files = files[:max_files]

    rows = []
    prefix = "S_" if market == "stock" else "E_"
    for path in files:
        code = os.path.basename(path).replace(".csv.gz", "")
        df = read_flow_file(path)
        if df.empty:
            continue
        df["ticker"] = prefix + code.zfill(6)
        rows.append(df)

    if not rows:
        empty = pd.DataFrame()
        return {col: empty for col in FLOW_COLUMNS[1:]}

    long_df = pd.concat(rows, ignore_index=True)
    out: Dict[str, pd.DataFrame] = {}
    for col in FLOW_COLUMNS[1:]:
        out[col] = long_df.pivot(index="date", columns="ticker", values=col).sort_index()
    return out
