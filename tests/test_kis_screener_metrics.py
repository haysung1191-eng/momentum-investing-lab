from live_core.kis_screener_metrics import calculate_momentum_metrics


def _build_price_rows(length: int = 241) -> list[dict]:
    return [
        {
            "stck_clpr": str(1000 + (length - idx - 1) * 10),
            "acml_vol": str(10000 + idx * 100),
        }
        for idx in range(length)
    ]


def test_calculate_momentum_metrics_returns_expected_fields() -> None:
    metrics = calculate_momentum_metrics(_build_price_rows())

    assert metrics is not None
    assert metrics["current_price"] == 3400.0
    assert metrics["momentum_1m"] == 6.25
    assert metrics["momentum_3m"] == 21.43
    assert metrics["momentum_6m"] == 54.55
    assert metrics["momentum_12m"] == 240.0
    assert metrics["avg_momentum"] == 80.56
    assert metrics["MA_21"] == 3300.0
    assert metrics["MA_200"] == 2405.0
    assert metrics["MRAT"] == 1.3721
    assert metrics["MAD_gap_pct"] == 37.21
    assert metrics["volume_20d_avg"] == 10950.0


def test_calculate_momentum_metrics_requires_full_lookback() -> None:
    assert calculate_momentum_metrics(_build_price_rows(240)) is None
