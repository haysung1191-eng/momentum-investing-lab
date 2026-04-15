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
