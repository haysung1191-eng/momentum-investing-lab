from __future__ import annotations


def calculate_momentum_metrics(prices: list[dict]) -> dict | None:
    if not prices:
        return None

    try:
        idx_1m, idx_3m, idx_6m, idx_12m = 20, 60, 120, 240
        if len(prices) <= idx_12m:
            return None

        p_cur = float(prices[0]["stck_clpr"])
        p_1m = float(prices[idx_1m]["stck_clpr"])
        p_3m = float(prices[idx_3m]["stck_clpr"])
        p_6m = float(prices[idx_6m]["stck_clpr"])
        p_12m = float(prices[idx_12m]["stck_clpr"])

        mom_1m = (p_cur - p_1m) / p_1m * 100 if p_1m > 0 else 0
        mom_3m = (p_cur - p_3m) / p_3m * 100 if p_3m > 0 else 0
        mom_6m = (p_cur - p_6m) / p_6m * 100 if p_6m > 0 else 0
        mom_12m = (p_cur - p_12m) / p_12m * 100 if p_12m > 0 else 0
        avg_mom = (mom_1m + mom_3m + mom_6m + mom_12m) / 4

        volume_20d_avg = sum(float(p["acml_vol"]) for p in prices[:20]) / 20 if len(prices) >= 20 else 0

        ma_21 = sum(float(prices[i]["stck_clpr"]) for i in range(21)) / 21 if len(prices) >= 21 else p_cur
        ma_200 = sum(float(prices[i]["stck_clpr"]) for i in range(200)) / 200 if len(prices) >= 200 else p_cur
        mrat = ma_21 / ma_200 if ma_200 > 0 else 0
        mad_gap_pct = (ma_21 - ma_200) / ma_200 * 100 if ma_200 > 0 else 0

        return {
            "momentum_1m": round(mom_1m, 2),
            "momentum_3m": round(mom_3m, 2),
            "momentum_6m": round(mom_6m, 2),
            "momentum_12m": round(mom_12m, 2),
            "avg_momentum": round(avg_mom, 2),
            "MA_21": round(ma_21, 0),
            "MA_200": round(ma_200, 0),
            "MRAT": round(mrat, 4),
            "MAD_gap_pct": round(mad_gap_pct, 2),
            "volume_20d_avg": round(volume_20d_avg, 2),
            "current_price": p_cur,
        }
    except Exception:
        return None
