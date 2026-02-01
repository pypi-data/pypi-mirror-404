from dataclasses import dataclass
from typing import Optional

import pandas as pd

from ..core.portfolio import Trade


@dataclass
class BacktestMetrics:
    total_return: float
    annualized_return: float
    max_drawdown: float
    num_trades: int
    sharpe_ratio: Optional[float] = None
    win_rate: Optional[float] = None


@dataclass
class BacktestResult:
    symbol: str
    timeframe: str
    equity_curve: pd.Series  # index: timestamp, values: total portfolio value
    trades: list[Trade]
    metrics: BacktestMetrics
    config: dict
