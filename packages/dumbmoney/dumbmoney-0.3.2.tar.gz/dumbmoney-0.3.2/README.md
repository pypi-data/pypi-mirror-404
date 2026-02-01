# dumbmoney

**dumbmoney** is a technical analysis and quantitative trading toolkit designed for retail investors. The current version provides a unified, transparent interface to fetch daily stock prices across A-shares, H-shares, and US markets by abstracting popular data packages like `massive`, `tushare`, `akshare`, and `tigeropen` (optional), hiding their implementation complexity.

*To use the `massive` or `tushare` providers, you must set the required environment variables `MASSIVE_KEY` or `TUSHARE_TOKEN`.*

*`tigeropen` is an optional provider. To use `tigeropen`, you must set the required environment varialbes `TIGER_ID`, `TIGER_ACCOUNT`, `TIGER_LICENSE` and `TIGER_PRIVATE_KEY`. Please refer to [Tiger's GitHub repo](https://github.com/tigerfintech/openapi-python-sdk) for more details.*

## 📦 Installation

Install only the core:

```bash
pip install dumbmoney
```

Install extra `tigeropen` package:

```bash
pip install "dumbmoney[tiger]"
```

## 🚀 Quick Start

### Stock Details

```python
from dumbmoney import get_stock_details

os.environ["TIGER_ID"] = "xxxxxx"
os.environ["TIGER_ACCOUNT"] = "yyyyyy"
os.environ["TIGER_LICENSE"] = "xxxxxx"
os.environ["TIGER_PRIVATE_KEY"] = "yyyyyy"
os.environ["TUSHARE_TOKEN"] = "xxxxxx"
os.environ["MASSIVE_KEY"] = "yyyyyy"

details = get_stock_details('AAPL.US')
print(details)
```

### OHLCV Data & Charts

```python
from dumbmoney import get_ohlcv, plot

os.environ["TUSHARE_TOKEN"] = "xxxxxx"
os.environ["MASSIVE_KEY"] = "yyyyyy"

ohlcv = get_ohlcv("AAPL.US")
print(ohlcv.tail())

from dumbmoney.indicators import MovingAverage, MACD, RSI

ma5 = MovingAverage(name="MA5", window=5, ma_type="SMA")
ma5.compute(ohlcv)

ma20 = MovingAverage(name="MA20", window=20, ma_type="SMA")
ma20.compute(ohlcv)

ma60 = MovingAverage(name="MA60", window=60, ma_type="SMA")
ma60.compute(ohlcv)

vol_ma20 = MovingAverage(name="Vol_MA20", window=20, ma_type="SMA", input_col="volume")
vol_ma20.compute(ohlcv)

macd = MACD()
macd.compute(ohlcv)

rsi = RSI()
rsi.compute(ohlcv)

plot(
  ohlcv,
  indicators=[ma5, ma20, ma60, vol_ma20, macd, rsi],
  panels=[0, 0, 0, 1, 2, 3],
  title="AAPL Stock Price with Indicators (mplfinance)",
  backend="mpl", # available backends: "mpl", "plotly"
)
```

### Strategy, Policy & Backtest

```python
from dumbmoney import get_ohlcv
from dumbmoney.strategies import MACrossParams, MACrossStrategy
from dumbmoney.policies import LongFlatAllInConfig, LongFlatAllInPolicy
from dumbmoney.backtests.single_asset import SingleAssetBacktester

ohlcv = get_ohlcv("AAPL.US")
strategy = MACrossStrategy(MACrossParams(fast_window=20, slow_window=60))
policy = LongFlatAllInPolicy(LongFlatAllInConfig(max_long_pct=1.0, min_strength=0.5))
backtester = SingleAssetBacktester(initial_cash=100_000.0)
result = backtester.run(symbol="AAPL", ohlcv=ohlcv, strategy=strategy, policy=policy)
print(result.metrics)
```

## ✨ Features

- 🔌 One function to fetch ohlcv data: get_ohlcv(symbol, start, end)
- 🌏 Multiple markets supported
  - A-shares (.SH, .SZ)
  - H-shares (.HK)
  - US stocks (.US)
- ⚙️ Automatic provider routing
  - A-shares: TigerOpen → TuShare → AkShare
  - H-shares: TigerOpen → TuShare → AkShare
  - US stocks: TigerOpen → Massive → AkShare
- 📐 Unified normalized output
  - open, high, low, close, volume
- 🔁 Fallback logic
  - If one provider fails, the next takes over
- 🧩 Extensible architecture (plug in new providers)

### Important Notice

- `massive`'s free api key only supports retrieving data of US stocks from the most recent two years.
- `tushare`'s free token only supports retrieving data of A-shares.
- `akshare` is free but depends on third-party data sources that may have variable reliability.

## 🏷️ Symbol Format

`dumbmoney` uses suffix-based symbol conventions:

| Market | Example Symbol |
| ------ | ------ |
| SH | 600519.SH or 600519 |
| SZ | 000001.SZ or 000001 |
| KCB | 688235.SH or 688235 |
| ETF_SH | 513090.SH or 513090, 562500.SH or 562500, 588080.SH or 588080 |
| ETF_SZ | 159652.SZ or 159652 |
| HK | 0700.HK |
| US | AAPL.US |

Suffixes for H-shares and US stocks are required. A-share symbols may omit suffixes; however, if they are present, they must be valid and correct.

## 📘 API Reference

### `get_ohlcv(symbol, start, end, adjust="none")`

Fetch normalized daily OHLCV prices.

- **Parameters**

| Name | Type | Description |
| ------ | ------ | ------ |
| `symbol` | `str` | Stock symbol with suffix (600519.SH, 0700.HK, AAPL.US) |
| `start` | `str` | Start time, e.g. "2025-01-01" |
| `end` | `str` | End time, e.g. "2025-12-01" |
| `adjust` | `str` | Adjustment mode, "none" \| "forward" \| "backward", default is "forward" |

- **Returns**

A `pandas.DataFrame` with:

| Column | Description |
| ------ | ------ |
| `open` | Opening price |
| `high` | High |
| `low` | Low |
| `close` | Close |
| `volume` | Traded volume |

Index is a `DatetimeIndex` named `date`.

### `plot(ohlcv, indicators=None, panels=None, title=None, backend="mpl", **kwargs)`

Plot chart using the provided ohlcv data.

- **Parameters**

| Name | Type | Description |
| ------ | ------ | ------ |
| `ohlcv` | `pandas.DataFrame` | DataFrame containing OHLCV columns (`open`, `high`, `low`, `close`, `volume`) |
| `indicators` | `list` or `None` | List of technical indicators to plot. Default is `None`. |
| `panels` | `list` or `None` | List of panel where the indicators will be plotted on. The ohlcv data will be plotted on the first two panels. |
| `title` | `str` or `None` | Chart title. Default is `None`. |
| `backend` | `str` | Plotting backend to use. Currently support `"mpl"` (mplfinance, default) and `"plotly"` (plotly). |
| `**kwargs` | - | Additional keyword arguments passed to the plotting backend. |

- **Returns**

The plotter object which can be used to get the figure object by `plotter.fig`.
