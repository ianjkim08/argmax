"""Yahoo Finance data provider with transparent local caching."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "argmax"


def _cache_path(ticker: str, start: str | None, end: str | None, cache_dir: Path) -> Path:
    key = f"{ticker.upper()}|{start or ''}|{end or ''}"
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return cache_dir / f"{ticker.upper()}-{digest}.pkl"


def _clean(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if frame.empty:
        raise ValueError(f"No data returned for ticker {ticker!r}")
    data = frame.copy()
    if isinstance(data.columns, pd.MultiIndex):
        # yfinance changed its column shape across releases; accept both layouts.
        if ticker in data.columns.get_level_values(-1):
            data = data.xs(ticker, axis=1, level=-1, drop_level=True)
        elif ticker in data.columns.get_level_values(0):
            data = data.xs(ticker, axis=1, level=0, drop_level=True)
        else:
            data.columns = data.columns.get_level_values(0)
    if "Adj Close" in data and "Close" not in data:
        data = data.rename(columns={"Adj Close": "Close"})
    missing = set(REQUIRED_COLUMNS).difference(data.columns)
    if missing:
        raise ValueError(f"Data for {ticker!r} is missing columns: {sorted(missing)}")
    data = data.loc[:, list(REQUIRED_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    data.index = pd.to_datetime(data.index).tz_localize(None)
    data.index.name = "Date"
    return data.sort_index().loc[~data.index.duplicated()].dropna(subset=list(REQUIRED_COLUMNS))


def _download(ticker: str, start: str | None, end: str | None) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - dependency metadata protects this path
        raise ImportError("Install argmax with its data dependencies to use Yahoo Finance") from exc
    frame = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        actions=False,
        threads=False,
    )
    return _clean(frame, ticker)


def get_data(
    ticker: str | Sequence[str],
    start: str | None = None,
    end: str | None = None,
    *,
    cache: bool = True,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Return clean adjusted OHLCV data for one or more tickers.

    A single ticker returns ordinary OHLCV columns. Multiple tickers return columns
    with ``(Ticker, Field)`` levels. Yahoo's ``end`` date is exclusive.
    """
    tickers = [ticker] if isinstance(ticker, str) else list(ticker)
    if not tickers:
        raise ValueError("At least one ticker is required")
    root = Path(cache_dir).expanduser() if cache_dir else DEFAULT_CACHE_DIR
    frames: dict[str, pd.DataFrame] = {}
    for raw in tickers:
        symbol = raw.strip().upper()
        if not symbol:
            raise ValueError("Ticker symbols cannot be empty")
        path = _cache_path(symbol, start, end, root)
        if cache and path.exists() and not refresh:
            frames[symbol] = _clean(pd.read_pickle(path), symbol)
        else:
            frames[symbol] = _download(symbol, start, end)
            if cache:
                root.mkdir(parents=True, exist_ok=True)
                frames[symbol].to_pickle(path)
    if len(frames) == 1:
        return next(iter(frames.values()))
    combined = pd.concat(frames, axis=1)
    combined.columns.names = ["Ticker", "Field"]
    return combined.sort_index()


def clear_cache(cache_dir: str | Path | None = None) -> int:
    """Delete Argmax cache files and return the number removed."""
    root = Path(cache_dir).expanduser() if cache_dir else DEFAULT_CACHE_DIR
    if not root.exists():
        return 0
    paths = list(root.glob("*.pkl"))
    for path in paths:
        path.unlink()
    return len(paths)
