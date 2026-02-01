from dataclasses import dataclass
from typing import Literal

import pandas as pd


Side = Literal["buy", "sell"]


@dataclass
class SingleAssetPortfolioState:
    # Single asset portfolio for now
    timestamp: pd.Timestamp
    cash: float
    position_qty: float
    price: float

    @property
    def position_value(self) -> float:
        return self.position_qty * self.price

    @property
    def total_value(self) -> float:
        return self.cash + self.position_value


@dataclass
class Order:
    timestamp: pd.Timestamp
    side: Side
    quantity: float
    price: float


@dataclass
class Trade:
    timestamp: pd.Timestamp
    side: Side
    quantity: float
    price: float
    pnl: float  # profit and loss from this trade
