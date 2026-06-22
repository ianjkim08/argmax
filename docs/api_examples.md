# API examples

## Data caching

```python
from argmax.data import clear_cache, get_data

spy = get_data("SPY", start="2020-01-01", end="2024-01-01")
fresh_spy = get_data("SPY", start="2020-01-01", end="2024-01-01", refresh=True)
removed_files = clear_cache()
```

Set `cache_dir` to isolate datasets for a research project. The cache key includes
symbol and exact requested date range.

## Comparing strategies

```python
from argmax import Backtest
from argmax.analytics import compare_results
from argmax.strategies import MomentumStrategy, MovingAverageCross

strategies = {
    "trend": MovingAverageCross(fast=20, slow=100),
    "momentum": MomentumStrategy(lookback=126),
}
results = {name: Backtest(strategy, data).run() for name, strategy in strategies.items()}
comparison = compare_results(results)
print(comparison)
```

## Four-panel research chart

```python
import matplotlib.pyplot as plt

from argmax.plots import plot_drawdown, plot_equity, plot_rolling_sharpe, plot_trades

figure, axes = plt.subplots(2, 2, figsize=(14, 8))
plot_equity(result, axes[0, 0])
plot_drawdown(result, axes[0, 1])
plot_trades(result, axes[1, 0])
plot_rolling_sharpe(result, window=63, ax=axes[1, 1])
figure.tight_layout()
```
