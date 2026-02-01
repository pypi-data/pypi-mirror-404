from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from ..core import SingleAssetPortfolioState
from ..strategies import StrategyConfig


@dataclass
class DecisionContext:
    """
    Context information passed to policy decision methods.
    """

    symbol: str
    timestamp: pd.Timestamp
    price: float
    signal_row: pd.Series  # A single row from SignalFrame.signals, e.g. {'signal_type': SignalType, 'strength': float}
    portfolio: SingleAssetPortfolioState
    strategy_config: StrategyConfig


class PositionPolicy(ABC):
    """
    Abstract base class for position management policies.
    """

    @abstractmethod
    def target_position_pct(self, ctx: DecisionContext) -> float:
        """
        Determine the target position percentage based on the decision context.

        Args:
          ctx: DecisionContext containing relevant information for decision making.

        Returns:
          Target position percentage (between 0.0 and 1.0 for long positions; -1.0 to 0.0 for short positions).
        """
        raise NotImplementedError
