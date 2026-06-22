from __future__ import annotations

import json
import threading
from contextlib import closing
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from argmax import web


def payload() -> dict[str, object]:
    return {
        "ticker": "SPY",
        "start": "2023-01-01",
        "end": "2024-01-01",
        "strategy": "moving_average_cross",
        "parameters": {"fast": 10, "slow": 30},
        "capital": 100_000,
        "commission": 0.001,
        "slippage": 0.0005,
        "position_size": 1,
    }


def test_web_backtest_serializes_results(monkeypatch, market_data) -> None:
    monkeypatch.setattr(web, "get_data", lambda *args, **kwargs: market_data)
    result = web.run_web_backtest(payload())
    assert result["ticker"] == "SPY"
    assert result["period"]["sessions"] == 260
    assert len(result["series"]["dates"]) == 260
    assert len(result["series"]["equity"]) == 260
    assert result["trades"]
    assert json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"ticker": "SPY!"}, "Ticker"),
        ({"start": "2025-01-01", "end": "2024-01-01"}, "before"),
        ({"strategy": "crystal_ball"}, "Unknown strategy"),
        ({"capital": 0}, "positive"),
        ({"position_size": 2}, "position_size"),
        ({"parameters": {"fast": 10, "mystery": 2}}, "Unknown strategy parameters"),
    ],
)
def test_web_input_validation(change, message) -> None:
    request = payload() | change
    with pytest.raises(web.WebInputError, match=message):
        web.run_web_backtest(request)


def test_local_dashboard_serves_assets_and_api(monkeypatch, market_data) -> None:
    monkeypatch.setattr(web, "get_data", lambda *args, **kwargs: market_data)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), web.DashboardHandler)
    except PermissionError:
        pytest.skip("Local socket binding is disabled in this sandbox")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with closing(urlopen(f"{base}/", timeout=5)) as response:
            html = response.read().decode()
        assert response.status == 200
        assert "Quantitative research infrastructure" in html
        assert "Find the strategy" in html

        with closing(urlopen(f"{base}/app.html", timeout=5)) as response:
            app_html = response.read().decode()
        assert response.status == 200
        assert "Strategy Research Console" in app_html
        assert "argmax" in app_html

        request = Request(
            f"{base}/api/backtest",
            data=json.dumps(payload()).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with closing(urlopen(request, timeout=5)) as response:
            result = json.loads(response.read())
        assert response.status == 200
        assert result["metrics"]["total_return"] is not None

        with pytest.raises(HTTPError) as error:
            urlopen(f"{base}/missing", timeout=5)
        assert error.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
