from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from argmax.data import clear_cache, get_data, yahoo


def raw_frame() -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=3, tz="UTC")
    return pd.DataFrame(
        {
            "Open": [1, 2, 3],
            "High": [2, 3, 4],
            "Low": [0, 1, 2],
            "Close": [1.5, 2.5, 3.5],
            "Volume": [10, 20, 30],
        },
        index=index,
    )


def test_get_data_caches_single_ticker(monkeypatch, tmp_path) -> None:
    calls = 0

    def fake_download(ticker, start, end):
        nonlocal calls
        calls += 1
        return yahoo._clean(raw_frame(), ticker)

    monkeypatch.setattr(yahoo, "_download", fake_download)
    first = get_data("spy", "2024-01-01", "2024-02-01", cache_dir=tmp_path)
    second = get_data("SPY", "2024-01-01", "2024-02-01", cache_dir=tmp_path)
    assert calls == 1
    assert first.equals(second)
    assert first.index.tz is None
    assert list(first.columns) == list(yahoo.REQUIRED_COLUMNS)
    assert clear_cache(tmp_path) == 1
    assert clear_cache(tmp_path) == 0


def test_get_data_combines_multiple_tickers(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(yahoo, "_download", lambda ticker, start, end: raw_frame())
    data = get_data(["SPY", "QQQ"], cache=False, cache_dir=tmp_path)
    assert data.columns.names == ["Ticker", "Field"]
    assert set(data.columns.get_level_values("Ticker")) == {"SPY", "QQQ"}


def test_data_validation(tmp_path) -> None:
    with pytest.raises(ValueError, match="At least one"):
        get_data([], cache_dir=tmp_path)
    with pytest.raises(ValueError, match="cannot be empty"):
        get_data(["  "], cache_dir=tmp_path)
    with pytest.raises(ValueError, match="No data"):
        yahoo._clean(pd.DataFrame(), "BAD")
    incomplete = pd.DataFrame({"Close": np.arange(3)}, index=pd.date_range("2024-01-01", periods=3))
    with pytest.raises(ValueError, match="missing columns"):
        yahoo._clean(incomplete, "BAD")
