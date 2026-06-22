from __future__ import annotations

import yaml

from argmax import cli


def test_yaml_cli_runs_and_writes_outputs(monkeypatch, tmp_path, market_data, capsys) -> None:
    monkeypatch.setattr(cli, "get_data", lambda **kwargs: market_data)
    config = {
        "data": {"ticker": "TEST"},
        "strategy": {
            "name": "moving_average_cross",
            "parameters": {"fast": 10, "slow": 30},
        },
        "backtest": {"capital": 10_000, "commission": 0},
        "output": {
            "metrics": str(tmp_path / "nested" / "metrics.json"),
            "equity_plot": str(tmp_path / "nested" / "equity.png"),
        },
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    assert cli.main(["backtest", str(path)]) == 0
    assert "sharpe_ratio" in capsys.readouterr().out
    assert (tmp_path / "nested" / "metrics.json").exists()
    assert (tmp_path / "nested" / "equity.png").exists()


def test_cli_exposes_web_server_command() -> None:
    arguments = cli.build_parser().parse_args(["serve", "--host", "0.0.0.0", "--port", "9000"])
    assert arguments.command == "serve"
    assert arguments.host == "0.0.0.0"
    assert arguments.port == 9000
