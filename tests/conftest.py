from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def market_data() -> pd.DataFrame:
    index = pd.date_range("2023-01-02", periods=260, freq="B")
    close = pd.Series(
        100 + np.linspace(0, 30, len(index)) + np.sin(np.arange(len(index)) / 5) * 3, index=index
    )
    return pd.DataFrame(
        {
            "Open": close.shift(1).fillna(close.iloc[0]) + 0.2,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": 1_000_000,
        },
        index=index,
    )
