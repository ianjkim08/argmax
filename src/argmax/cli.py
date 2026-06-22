"""Command-line interface for configuration-driven backtests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

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


def _load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError("Configuration root must be a mapping")
    return config


def run_config(path: str | Path) -> int:
    """Run a YAML-configured backtest and print its metrics."""
    config = _load_config(Path(path))
    data_config = config.get("data", {})
    strategy_config = config.get("strategy", {})
    name = strategy_config.get("name")
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy {name!r}; choose from {sorted(STRATEGIES)}")
    data = get_data(
        ticker=data_config["ticker"],
        start=data_config.get("start"),
        end=data_config.get("end"),
        refresh=bool(data_config.get("refresh", False)),
    )
    strategy = STRATEGIES[name](**strategy_config.get("parameters", {}))
    result = Backtest(strategy=strategy, data=data, **config.get("backtest", {})).run()
    print(result.summary().to_string(float_format=lambda value: f"{value:.4f}"))
    output = config.get("output", {})
    if output.get("metrics"):
        metrics_path = Path(output["metrics"])
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(result.metrics.to_dict(), indent=2), encoding="utf-8")
    if output.get("equity_plot"):
        from argmax.plots import plot_equity

        plot_path = Path(output["equity_plot"])
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        figure = plot_equity(result).figure
        figure.savefig(plot_path, dpi=150, bbox_inches="tight")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="argmax", description="Argmax backtesting CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    backtest = subparsers.add_parser("backtest", help="run a YAML-configured backtest")
    backtest.add_argument("config", help="path to a YAML configuration")
    serve = subparsers.add_parser("serve", help="launch the local Argmax web dashboard")
    serve.add_argument("--host", default="127.0.0.1", help="server host (default: 127.0.0.1)")
    serve.add_argument("--port", default=8000, type=int, help="server port (default: 8000)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    arguments = build_parser().parse_args(argv)
    if arguments.command == "backtest":
        return run_config(arguments.config)
    if arguments.command == "serve":
        from argmax.web import serve

        serve(arguments.host, arguments.port)
        return 0
    return 1  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
