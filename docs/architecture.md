# Architecture and execution model

Argmax separates data acquisition, signal generation, order execution, account
state, and reporting. Strategies therefore have no access to future orders or cash
accounting, and analytics do not influence simulation.

## Session timeline

For session `t`, the strategy observes all data through the close of `t`. Its target
is shifted and executed at the open of `t+1`. The account is marked at the close of
`t+1`. When `liquidate_at_end=True`, any open position is sold at the last close with
the configured transaction costs.

## Accounting assumptions

- One asset and one long position per backtest
- Integer shares and no leverage
- Position size is a fraction of currently available cash
- Commission is a fraction of traded notional on each side
- Slippage raises buy fills and lowers sell fills
- Cash earns no interest; dividends and splits are incorporated through Yahoo's
  adjusted prices

Multi-asset data is supported at the acquisition layer. This deliberate boundary
keeps the current ledger easy to audit and leaves a clean extension point for a
future portfolio-level allocation engine.

## Web deployment

The browser interface in `public/` calls `POST /api/backtest`. Locally, `argmax serve`
provides static files and the JSON endpoint with Python's threaded HTTP server. On Vercel,
static assets are served from its CDN and `api/backtest.py` adapts the same
`run_web_backtest` application service to a Python Function. Both paths execute the exact
same strategy, portfolio, analytics, and serialization code.

## Extension points

- Add a strategy by subclassing `Strategy`.
- Add an indicator as a pure pandas transformation.
- Add a data provider beside `argmax.data.yahoo`, preserving the OHLCV contract.
- Add a metric to the immutable `Metrics` record and result properties.
- Build plots from `BacktestResult`; plotting never mutates a simulation.
