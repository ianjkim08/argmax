"""Web dashboard serialization and a dependency-free local development server."""

from __future__ import annotations

import json
import math
import mimetypes
import re
from collections.abc import Mapping
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd

from argmax.backtest import Backtest
from argmax.data import get_data
from argmax.strategies import (
    BollingerReversion,
    MomentumStrategy,
    MovingAverageCross,
    RSIMeanReversion,
    Strategy,
)

STRATEGIES: dict[str, type[Strategy]] = {
    "moving_average_cross": MovingAverageCross,
    "rsi_mean_reversion": RSIMeanReversion,
    "bollinger_reversion": BollingerReversion,
    "momentum": MomentumStrategy,
}
TICKER_PATTERN = re.compile(r"^[A-Za-z0-9.^=_-]{1,20}$")
MAX_OBSERVATIONS = 800


class WebInputError(ValueError):
    """A safe validation error that can be returned to a web client."""


def _finite(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def _number(payload: Mapping[str, Any], name: str, default: float) -> float:
    raw = payload.get(name, default)
    if isinstance(raw, bool):
        raise WebInputError(f"{name} must be a number")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise WebInputError(f"{name} must be a number") from exc
    if not math.isfinite(value):
        raise WebInputError(f"{name} must be finite")
    return value


def _downsample(frame: pd.DataFrame, limit: int = MAX_OBSERVATIONS) -> pd.DataFrame:
    if len(frame) <= limit:
        return frame
    positions = np.linspace(0, len(frame) - 1, limit, dtype=int)
    return frame.iloc[np.unique(positions)]


def _strategy(name: str, parameters: Mapping[str, Any]) -> Strategy:
    strategy_type = STRATEGIES.get(name)
    if strategy_type is None:
        raise WebInputError(f"Unknown strategy: {name}")
    allowed = {
        "moving_average_cross": {"fast", "slow"},
        "rsi_mean_reversion": {"period", "oversold", "exit_level"},
        "bollinger_reversion": {"period", "std_dev"},
        "momentum": {"lookback", "threshold"},
    }[name]
    unknown = set(parameters).difference(allowed)
    if unknown:
        raise WebInputError(f"Unknown strategy parameters: {', '.join(sorted(unknown))}")
    try:
        return strategy_type(**dict(parameters))
    except (TypeError, ValueError) as exc:
        raise WebInputError(str(exc)) from exc


def run_web_backtest(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a browser request, run a backtest, and return JSON-compatible data."""
    ticker = str(payload.get("ticker", "SPY")).strip().upper()
    if not TICKER_PATTERN.fullmatch(ticker):
        raise WebInputError("Ticker must contain 1-20 letters, numbers, or . ^ = _ -")
    start = str(payload.get("start", "2018-01-01"))
    end = str(payload.get("end", pd.Timestamp.now().date()))
    try:
        start_date, end_date = pd.Timestamp(start), pd.Timestamp(end)
    except ValueError as exc:
        raise WebInputError("Start and end must be valid dates") from exc
    if start_date >= end_date:
        raise WebInputError("Start date must be before end date")
    if (end_date - start_date).days > 365 * 30:
        raise WebInputError("Date range cannot exceed 30 years")

    name = str(payload.get("strategy", "moving_average_cross"))
    parameters = payload.get("parameters", {})
    if not isinstance(parameters, Mapping):
        raise WebInputError("parameters must be an object")
    strategy = _strategy(name, parameters)
    capital = _number(payload, "capital", 100_000)
    commission = _number(payload, "commission", 0.001)
    slippage = _number(payload, "slippage", 0.0005)
    position_size = _number(payload, "position_size", 1.0)
    if capital <= 0:
        raise WebInputError("capital must be positive")
    if commission < 0 or slippage < 0:
        raise WebInputError("commission and slippage cannot be negative")
    if not 0 < position_size <= 1:
        raise WebInputError("position_size must be in (0, 1]")

    try:
        data = get_data(ticker, start, end, cache=False)
        result = Backtest(
            strategy,
            data,
            capital=capital,
            commission=commission,
            slippage=slippage,
            position_size=position_size,
        ).run()
    except WebInputError:
        raise
    except (ValueError, RuntimeError) as exc:
        raise WebInputError(str(exc)) from exc

    chart = pd.DataFrame(
        {
            "close": result.data["Close"],
            "equity": result.equity,
            "drawdown": result.drawdown,
        }
    )
    sampled = _downsample(chart)
    metrics = {key: _finite(value) for key, value in result.metrics.to_dict().items()}
    trades = [
        {
            "entry_date": pd.Timestamp(row.entry_date).strftime("%Y-%m-%d"),
            "entry_price": round(float(row.entry_price), 4),
            "exit_date": pd.Timestamp(row.exit_date).strftime("%Y-%m-%d"),
            "exit_price": round(float(row.exit_price), 4),
            "shares": int(row.shares),
            "pnl": round(float(row.pnl), 2),
            "return_pct": round(float(row.return_pct), 6),
        }
        for row in result.trades.itertuples(index=False)
    ]
    return {
        "ticker": ticker,
        "strategy": name,
        "period": {
            "start": result.data.index[0].strftime("%Y-%m-%d"),
            "end": result.data.index[-1].strftime("%Y-%m-%d"),
            "sessions": len(result.data),
        },
        "metrics": metrics,
        "series": {
            "dates": [date.strftime("%Y-%m-%d") for date in sampled.index],
            "close": [round(float(value), 4) for value in sampled["close"]],
            "equity": [round(float(value), 2) for value in sampled["equity"]],
            "drawdown": [round(float(value), 6) for value in sampled["drawdown"]],
        },
        "trades": trades,
    }


def _public_dir() -> Path:
    candidates = [Path.cwd() / "public", Path(__file__).resolve().parents[2] / "public"]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Could not locate the public dashboard assets")


class DashboardHandler(BaseHTTPRequestHandler):
    """Serve the dashboard and API for local development."""

    server_version = "Argmax/0.2"

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: HTTPStatus, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, allow_nan=False).encode()
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(HTTPStatus.OK, {"status": "ok"})
            return
        relative = "index.html" if path == "/" else path.lstrip("/")
        root = _public_dir().resolve()
        asset = (root / relative).resolve()
        if root not in asset.parents or not asset.is_file():
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
        self._send(HTTPStatus.OK, asset.read_bytes(), f"{content_type}; charset=utf-8")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/backtest":
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 32_768:
                raise WebInputError("Request body must be between 1 byte and 32 KB")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, Mapping):
                raise WebInputError("Request body must be a JSON object")
            self._json(HTTPStatus.OK, run_web_backtest(payload))
        except (json.JSONDecodeError, WebInputError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception:  # pragma: no cover - last-resort HTTP boundary
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Backtest failed"})

    def log_message(self, format: str, *args: object) -> None:
        print(f"[argmax] {format % args}")


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the local dashboard server until interrupted."""
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Argmax dashboard running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Argmax dashboard")
    finally:
        server.server_close()
