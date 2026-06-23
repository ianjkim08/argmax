<div align="center">

# Argmax

### Bias-Aware Quantitative Strategy Research

[![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![pytest](https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)

**Test systematic trading ideas with explicit execution rules, realistic costs, and inspectable evidence.**

Built for quantitative traders, students, and researchers who want to understand every assumption between a signal and its result.

<a href="https://argmax-gamma.vercel.app/">
  <img src="https://img.shields.io/badge/Open_Live_Console-B8E85C?style=for-the-badge&logo=vercel&logoColor=11150D" alt="Open Live Console"/>
</a>

[Features](#features) · [Strategies](#built-in-strategies) · [Architecture](#architecture) · [Getting Started](#getting-started)

</div>

---

## The Idea

A backtest can look convincing while quietly benefiting from future information, impossible fills, fractional positions, or ignored trading costs. Those shortcuts make a strategy easier to believe and harder to trust.

**Argmax turns a trading hypothesis into an explicit, reproducible accounting path.**

Signals observed at a market close execute at the next open. The engine tracks integer shares, cash, commissions, slippage, trades, equity, drawdown, and risk metrics so users can inspect what happened instead of relying on a single performance number.

> Argmax is educational research software, not investment advice or a live-trading system. Backtests do not guarantee future results.

---

## Features

**Bias-Aware Execution** - A signal observed at today's close executes at the next market open, reducing accidental look-ahead bias.

**Transaction-Aware Accounting** - Model integer shares, proportional commissions, adverse slippage, partial capital allocation, and optional final liquidation.

**Interactive Research Console** - Configure markets, strategies, portfolio assumptions, and costs from a responsive browser interface.

**Inspectable Results** - Review account history, raw and shifted signals, realized trades, source data, drawdown, and performance metrics.

**Interactive Charts** - Switch between portfolio equity, peak-to-trough drawdown, and adjusted market price.

**Extensible Strategy Interface** - Add custom strategies by implementing one typed `generate_signals` method.

**Technical Indicators** - Use SMA, EMA, RSI, MACD, Bollinger Bands, and ATR as vectorized pandas operations.

**Parameter Optimization** - Compare parameter grids or run deterministic random searches with ranked outputs.

**YAML-Driven CLI** - Reproduce research runs from configuration files and export JSON metrics and charts.

**Local and Cloud Deployment** - Run the same tested engine locally or through a Vercel-hosted Python API.

---

## Built-In Strategies

| Strategy | Core Idea | Main Parameters |
|----------|-----------|-----------------|
| Moving Average Crossover | Follow trends when a fast average crosses a slow average | `fast`, `slow` |
| RSI Mean Reversion | Enter below an oversold level and exit after recovery | `period`, `oversold`, `exit_level` |
| Bollinger Reversion | Enter below the lower volatility band and revert toward the mean | `period`, `std_dev` |
| Price Momentum | Hold when trailing return exceeds a threshold | `lookback`, `threshold` |

Custom strategies return a target-exposure Series where `1` means invested and `0` means cash. Argmax validates the Series and shifts it one bar before execution.

```python
import pandas as pd

from argmax.indicators import EMA
from argmax.strategies import Strategy


class TrendStrategy(Strategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        close = data["Close"]
        return (close > EMA(close, period=50)).astype(float)
```

---

## Research Model

Argmax makes the following assumptions explicit:

- Signals are generated from historical OHLCV data available at the current close.
- Target exposure is shifted one bar before the portfolio acts.
- Trades execute at the next available open with adverse slippage.
- Positions use integer shares and cannot spend more cash than the portfolio holds.
- Commissions reduce cash on entries and exits.
- Performance is calculated from the resulting account history, not an idealized signal curve.

Yahoo Finance data may be adjusted, delayed, revised, incomplete, or temporarily unavailable. Research results should be validated against another data source before being used for consequential decisions.

---

## Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│                        Argmax Interfaces                       │
│                                                                │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐   │
│  │ Web Console  │  │ YAML-Driven CLI │  │ Python Package   │   │
│  └──────┬───────┘  └────────┬────────┘  └─────────┬────────┘   │
└─────────┼───────────────────┼─────────────────────┼────────────┘
          └───────────────────┼─────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │ Data + Indicators │
                    │ Yahoo Finance     │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │ Strategy Signals  │
                    │ + One-Bar Shift   │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │ Backtest Engine   │
                    │ + Portfolio       │
                    └─────────┬─────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
   ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐
   │ Risk Metrics│     │ Trade Ledger│     │ Charts + JSON│
   └─────────────┘     └─────────────┘     └─────────────┘
```

- **Engine:** Typed Python backtester with next-bar execution
- **Data:** Yahoo Finance retrieval with cleaning, validation, and local caching
- **Research:** Vectorized pandas indicators, strategies, and parameter optimization
- **Portfolio:** Cash, positions, integer shares, costs, and realized trades
- **Frontend:** Dependency-free HTML, CSS, and JavaScript with bundled GSAP motion
- **API:** Python `BaseHTTPRequestHandler` for local and Vercel backtests
- **Quality:** pytest, Ruff, coverage reporting, and GitHub Actions
- **Deployment:** Vercel static hosting plus a Python function

See [the architecture notes](docs/architecture.md) and [API examples](docs/api_examples.md) for accounting conventions and extension points.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| Data and Numerics | pandas, NumPy, Yahoo Finance |
| Visualization | Matplotlib, browser-native SVG charts |
| Frontend | HTML, CSS, JavaScript |
| Motion | GSAP and ScrollTrigger |
| API | Python HTTP handlers |
| Testing | pytest, pytest-cov |
| Code Quality | Ruff, type hints, `src/` package layout |
| Automation | GitHub Actions |
| Deployment | Vercel |

---

## Getting Started

Argmax requires Python 3.12 or newer.

```bash
# Clone the repository
git clone https://github.com/ianjkim08/argmax.git
cd argmax

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Argmax and development tools
python -m pip install -e ".[dev]"

# Run the test suite
pytest

# Start the complete web application
argmax serve
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
argmax serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the landing page or [http://127.0.0.1:8000/app.html](http://127.0.0.1:8000/app.html) for the research console.

Use `argmax serve`, not a static file server. The research console requires the Python `/api/backtest` endpoint.

### Environment Variables

No environment variables are required for the current application. Market data is downloaded from Yahoo Finance when a backtest runs.

---

## Quick Start

```python
from argmax.backtest import Backtest
from argmax.data import get_data
from argmax.plots import plot_equity, plot_trades
from argmax.strategies import MovingAverageCross

data = get_data("SPY", start="2015-01-01", end="2025-01-01")
strategy = MovingAverageCross(fast=20, slow=100)

result = Backtest(
    strategy=strategy,
    data=data,
    capital=100_000,
    commission=0.001,
    slippage=0.0005,
).run()

print(result.summary())
print(f"Sharpe: {result.sharpe_ratio:.2f}")
plot_equity(result)
plot_trades(result)
```

For several symbols, `get_data(["SPY", "QQQ"], ...)` returns a DataFrame with `(Ticker, Field)` column levels. Backtests intentionally accept one asset at a time, so select a ticker with `data["SPY"]`.

---

## Project Structure

```text
argmax/
├── api/
│   └── backtest.py               # Vercel Python API and health route
├── docs/
│   ├── api_examples.md           # Extended package examples
│   └── architecture.md           # Accounting and module design
├── examples/
│   ├── config.yaml               # CLI backtest configuration
│   └── custom_strategy.py        # Strategy extension example
├── public/
│   ├── assets/                   # Generated visual assets
│   ├── vendor/                   # Bundled GSAP runtime
│   ├── index.html                # Product landing page
│   ├── app.html                  # Research console
│   ├── landing.css               # Landing-page design system
│   ├── styles.css                # Console design system
│   ├── landing.js                # Marketing interactions and chart
│   └── app.js                    # Backtest controls and result rendering
├── src/argmax/
│   ├── analytics/                # Performance and risk metrics
│   ├── backtest/                 # Simulation engine and result model
│   ├── data/                     # Yahoo Finance retrieval and caching
│   ├── indicators/               # Vectorized technical indicators
│   ├── optimization/             # Grid and random parameter search
│   ├── plots/                    # Equity and trade visualizations
│   ├── portfolio/                # Cash, positions, and trade accounting
│   ├── strategies/               # Base interface and built-in models
│   ├── cli.py                    # Command-line interface
│   └── web.py                    # Local dashboard server and API logic
├── tests/                        # Unit, integration, CLI, and web tests
├── pyproject.toml                # Package, tooling, and Vercel configuration
└── vercel.json                   # Routes and security headers
```

---

## Indicators

```python
from argmax.indicators import ATR, EMA, MACD, RSI, SMA, BollingerBands

rsi = RSI(data["Close"], period=14)
macd, signal, histogram = MACD(data["Close"])
middle, upper, lower = BollingerBands(data["Close"])
atr = ATR(data, period=14)
```

Each output is a pandas Series aligned to the input index. Warm-up periods are represented by `NaN`, preventing premature signals.

---

## Optimization

```python
from argmax.optimization import GridSearch
from argmax.strategies import MovingAverageCross

optimizer = GridSearch(
    strategy_class=MovingAverageCross,
    param_grid={"fast": [10, 20, 30], "slow": [50, 100, 200]},
)

ranking = optimizer.run(data, capital=100_000, commission=0.001)
print(optimizer.best_params)
print(ranking.head())
```

`RandomSearch` accepts the same parameter grid plus `n_iter` and `random_state`. Optimization can overfit one historical sample, so evaluate selected parameters on held-out or walk-forward data.

---

## Metrics

| Metric | Definition |
|--------|------------|
| Total Return | Ending equity divided by starting equity, minus one |
| Annualized Return | Geometrically annualized return using 252 sessions |
| Volatility | Annualized standard deviation of daily returns |
| Sharpe Ratio | Annualized excess mean return divided by standard deviation |
| Sortino Ratio | Annualized excess mean return divided by downside deviation |
| Max Drawdown | Largest peak-to-trough equity decline |
| Win Rate | Fraction of completed trades with positive net P&L |
| Profit Factor | Gross realized profit divided by gross realized loss |

Ratios return `0` when variability is absent and the value is undefined. Profit factor is infinite when profitable trades exist without a losing trade.

---

## CLI

Copy or edit `examples/config.yaml`, then run:

```bash
argmax backtest examples/config.yaml
```

The CLI downloads data, builds the configured strategy, runs the portfolio forward, prints metrics, and optionally writes JSON results and an equity chart.

---

## Deployment

Argmax is deployed on Vercel at [argmax-gamma.vercel.app](https://argmax-gamma.vercel.app/).

The repository includes static assets in `public/`, a Python entrypoint in `api/backtest.py`, project configuration in `pyproject.toml`, and security headers in `vercel.json`. No environment variables or frontend build command are required.

To deploy your own fork:

1. Push the repository to GitHub.
2. Import the repository into Vercel.
3. Keep the detected Python settings and deploy.
4. Push future changes to `main` for automatic production deployments.

The hosted API downloads market data per request because serverless filesystems are ephemeral. A higher-traffic deployment should use a persistent market-data store and request-level rate limiting.

---

## Development Commands

```bash
argmax serve                                  # Start the local website and API
argmax backtest examples/config.yaml          # Run a configured CLI backtest
ruff check .                                  # Run lint checks
ruff format --check .                         # Validate Python formatting
pytest                                        # Run the test suite
pytest --cov=argmax --cov-report=term-missing # Run tests with coverage
node --check public/landing.js                # Validate landing-page JavaScript
node --check public/app.js                    # Validate console JavaScript
```

---

## Roadmap

- Walk-forward and rolling out-of-sample evaluation
- Multi-asset portfolio backtesting
- Persistent cloud market-data caching
- Benchmark and factor-model comparisons
- Saved research configurations and shareable runs
- Parameter-surface visualizations
- Additional order and position-sizing models
- Expanded data-provider integrations
- Stronger API rate limiting and observability

---

## Contributing

Contributions are welcome, especially in the following areas:

- Execution and portfolio-accounting edge cases
- Additional tested indicators and strategies
- Walk-forward and out-of-sample research tools
- Data quality and provider integrations
- Accessibility and responsive interface improvements
- Documentation, examples, and educational material

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Behavioral changes should include tests, and frontend changes should include desktop and mobile verification.

---

## License

This project is licensed under the [MIT License](LICENSE).

</div>
