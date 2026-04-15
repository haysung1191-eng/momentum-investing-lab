import pandas as pd

import screener


def test_momentum_screener_run_delegates_to_screening_service(monkeypatch) -> None:
    captured = {}

    class FakeApi:
        pass

    def fake_run_default_screening(**kwargs):
        captured.update(kwargs)
        return pd.DataFrame([{"Code": "005930"}])

    monkeypatch.setattr(screener, "KISApi", FakeApi)
    monkeypatch.setattr(screener, "run_default_screening", fake_run_default_screening)

    runner = screener.MomentumScreener()
    df = runner.run(max_items=123, etf_mode=True)

    assert list(df["Code"]) == ["005930"]
    assert captured["etf_mode"] is True
    assert captured["max_items"] == 123
    assert captured["config_module"] is screener.config
    assert captured["repo_root"] == screener.Path(screener.__file__).resolve().parent
    assert captured["api_factory"]() is runner.api
    assert captured["momentum_calculator"].__self__ is runner
    assert captured["momentum_calculator"].__func__ is runner.calculate_momentum.__func__


def test_momentum_screener_public_helpers_delegate(monkeypatch) -> None:
    captured = {}

    class FakeApi:
        pass

    def fake_market(**kwargs):
        captured["market"] = kwargs
        return [("005930", "삼성전자")]

    def fake_historical(*args, **kwargs):
        captured["historical"] = (args, kwargs)
        return [("000660", "SK하이닉스")]

    monkeypatch.setattr(
        screener,
        "get_current_stock_universe",
        fake_market,
    )
    monkeypatch.setattr(
        screener,
        "get_historical_market_tickers",
        fake_historical,
    )
    monkeypatch.setattr(
        screener,
        "get_etf_tickers",
        lambda: [("069500", "KODEX 200")],
    )
    monkeypatch.setattr(screener, "KISApi", FakeApi)

    runner = screener.MomentumScreener()

    assert runner.get_market_tickers() == [("005930", "삼성전자")]
    assert runner.get_historical_market_tickers("20250101", "20250131") == [("000660", "SK하이닉스")]
    assert runner.get_etf_tickers() == [("069500", "KODEX 200")]
    assert captured["market"]["config_module"] is screener.config
    assert captured["market"]["repo_root"] == screener.Path(screener.__file__).resolve().parent
    assert captured["market"]["name_validator"] is runner._is_valid_name
    assert captured["historical"][0] == ("20250101", "20250131")
