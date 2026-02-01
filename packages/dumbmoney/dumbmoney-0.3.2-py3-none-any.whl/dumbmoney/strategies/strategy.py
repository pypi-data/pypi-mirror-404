from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from ..core import OHLCVData, SignalFrame


@dataclass
class StrategyConfig:
    name: str
    timeframe: str = "1d"
    params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["params"] = d.get("params", {})  # params could be None
        return d


class Strategy(ABC):
    """
    Abstract base class for trading strategies.
    """

    def __init__(self, config: StrategyConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @abstractmethod
    def generate_signals(self, ohlcv: OHLCVData) -> SignalFrame:
        """
        Generate trading signals based on OHLCV data.

        Args:
          ohlcv: DataFrame containing OHLCV data.

        Returns:
          SignalFrame containing generated signals.
        """
        raise NotImplementedError
