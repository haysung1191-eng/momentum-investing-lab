from typing import Dict, List

import numpy as np
import pandas as pd


def zscore_row(df: pd.DataFrame) -> pd.DataFrame:
    mean = df.mean(axis=1)
    std = df.std(axis=1, ddof=0).replace(0.0, np.nan)
    return df.sub(mean, axis=0).div(std, axis=0)


def compute_flow_score(
    close_s: pd.DataFrame,
    value_s: pd.DataFrame,
    flow_mats: Dict[str, pd.DataFrame],
    foreign_ratio_cap: float = 40.0,
    foreign_ratio_penalty: float = 0.50,
) -> pd.DataFrame:
    foreign = flow_mats.get("foreign_net_volume", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    foreign = foreign.reindex(index=close_s.index, columns=close_s.columns).fillna(0.0)
    inst = flow_mats.get("institution_net_volume", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    inst = inst.reindex(index=close_s.index, columns=close_s.columns).fillna(0.0)
    foreign_ratio = flow_mats.get("foreign_ratio", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    foreign_ratio = foreign_ratio.reindex(index=close_s.index, columns=close_s.columns)

    traded_value_20 = value_s.rolling(20, min_periods=20).sum().replace(0.0, np.nan)
    traded_value_60 = value_s.rolling(60, min_periods=60).sum().replace(0.0, np.nan)

    foreign_20 = (foreign * close_s).rolling(20, min_periods=20).sum() / traded_value_20
    foreign_60 = (foreign * close_s).rolling(60, min_periods=60).sum() / traded_value_60
    inst_20 = (inst * close_s).rolling(20, min_periods=20).sum() / traded_value_20
    crowd_penalty = zscore_row(foreign_ratio.where(foreign_ratio >= foreign_ratio_cap))

    score = zscore_row(foreign_20) + 0.75 * zscore_row(foreign_60) + 0.20 * zscore_row(inst_20)
    if foreign_ratio_penalty > 0:
        score = score - foreign_ratio_penalty * crowd_penalty.fillna(0.0)
    return score.replace([np.inf, -np.inf], np.nan)


def compute_flow_score_v3(
    close_s: pd.DataFrame,
    value_s: pd.DataFrame,
    flow_mats: Dict[str, pd.DataFrame],
    foreign_ratio_cap: float = 40.0,
    foreign_ratio_penalty: float = 0.50,
) -> pd.DataFrame:
    foreign = flow_mats.get("foreign_net_volume", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    foreign = foreign.reindex(index=close_s.index, columns=close_s.columns).fillna(0.0)
    inst = flow_mats.get("institution_net_volume", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    inst = inst.reindex(index=close_s.index, columns=close_s.columns).fillna(0.0)
    foreign_shares = flow_mats.get("foreign_shares", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    foreign_shares = foreign_shares.reindex(index=close_s.index, columns=close_s.columns)
    foreign_ratio = flow_mats.get("foreign_ratio", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    foreign_ratio = foreign_ratio.reindex(index=close_s.index, columns=close_s.columns)

    ratio_frac = (foreign_ratio / 100.0).replace(0.0, np.nan)
    inferred_shares_out = (foreign_shares / ratio_frac).replace([np.inf, -np.inf], np.nan)
    market_cap = (inferred_shares_out * close_s).replace([np.inf, -np.inf], np.nan)

    foreign_notional = foreign * close_s
    inst_notional = inst * close_s

    cap_20 = market_cap.rolling(20, min_periods=20).mean() * 20.0
    cap_60 = market_cap.rolling(60, min_periods=60).mean() * 60.0
    fallback_value_20 = value_s.rolling(20, min_periods=20).sum().replace(0.0, np.nan)
    fallback_value_60 = value_s.rolling(60, min_periods=60).sum().replace(0.0, np.nan)
    denom_20 = cap_20.combine_first(fallback_value_20)
    denom_60 = cap_60.combine_first(fallback_value_60)

    foreign_20 = foreign_notional.rolling(20, min_periods=20).sum() / denom_20
    foreign_60 = foreign_notional.rolling(60, min_periods=60).sum() / denom_60
    inst_20 = inst_notional.rolling(20, min_periods=20).sum() / denom_20
    foreign_ratio_delta_20 = foreign_ratio - foreign_ratio.shift(20)

    ratio_crowd = zscore_row(foreign_ratio.where(foreign_ratio >= foreign_ratio_cap))
    delta_crowd = zscore_row(foreign_ratio_delta_20.where(foreign_ratio_delta_20 >= 2.0))

    score = (
        1.00 * zscore_row(foreign_20)
        + 0.75 * zscore_row(foreign_60)
        + 0.20 * zscore_row(inst_20)
        + 0.25 * zscore_row(foreign_ratio_delta_20)
    )
    if foreign_ratio_penalty > 0:
        score = score - foreign_ratio_penalty * ratio_crowd.fillna(0.0) - 0.25 * delta_crowd.fillna(0.0)
    return score.replace([np.inf, -np.inf], np.nan)


def rank_flow_at(
    feat: Dict[str, pd.DataFrame],
    flow_score: pd.DataFrame,
    close_s: pd.DataFrame,
    dt: pd.Timestamp,
    eligible_mask: pd.DataFrame | None,
    trend_ma: int,
    prev_holds: List[str],
    top_k: int,
    hold_buffer: int,
) -> pd.DataFrame:
    cols = [name for name in feat.keys() if dt in feat[name].index]
    if not cols:
        return pd.DataFrame()
    df = pd.concat([feat[name].loc[dt].rename(name) for name in cols], axis=1)
    if df.empty or dt not in flow_score.index or dt not in close_s.index:
        return df.iloc[0:0]

    df = df.copy()
    df["flow_score"] = flow_score.loc[dt].reindex(df.index)
    df = df.dropna(subset=["flow_score"])
    if df.empty:
        return df

    if eligible_mask is not None and dt in eligible_mask.index:
        eligible = eligible_mask.loc[dt].fillna(False)
        df = df.loc[df.index.intersection(eligible[eligible].index)]
        if df.empty:
            return df

    if trend_ma > 0:
        ma = close_s.rolling(trend_ma, min_periods=trend_ma).mean()
        if dt in ma.index:
            trend_ok = close_s.loc[dt] > ma.loc[dt]
            trend_names = trend_ok[trend_ok.fillna(False)].index
            df = df.loc[df.index.intersection(trend_names)]
            if df.empty:
                return df

    ranked = df.sort_values(["flow_score", "avg_mom"], ascending=[False, False])
    buffer_limit = max(1, int(top_k)) + max(0, int(hold_buffer))
    entry = list(ranked.head(max(1, int(top_k))).index)
    survivors = [ticker for ticker in prev_holds if ticker in set(ranked.head(buffer_limit).index)]
    picks = list(dict.fromkeys(entry + survivors))
    out = ranked.loc[ranked.index.intersection(picks)].copy()
    out["buy_score"] = out["flow_score"]
    out["mad_gap"] = 0.0
    return out.sort_values(["flow_score", "avg_mom"], ascending=[False, False]).head(buffer_limit)
