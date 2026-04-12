from __future__ import annotations


def get_single_asset_candidates() -> list[dict]:
    return [
        {
            "candidate_id": "krw_btc_1h_bb20_rsi14_mr_v1",
            "symbol": "KRW-BTC",
            "interval": "1h",
            "strategy_module": "app.single_asset.strategies.krw_btc_bb_rsi_mean_reversion",
            "candidate_alpha": "Hourly oversold snapback after volatility expansion in KRW-BTC.",
            "included": True,
        }
    ]

