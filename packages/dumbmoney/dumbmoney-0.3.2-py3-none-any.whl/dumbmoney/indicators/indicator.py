from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import pandas as pd

from ..core import OHLCVData


@dataclass(frozen=True)
class Indicator(ABC):
    """
    Base class for all indicators.
    """

    name: str
    inputs: List[str] = field(
        default_factory=list
    )  # names of columns used to compute the indicator values, e.g. ['close', 'volume']
    params: Dict[str, Any] = field(
        default_factory=dict
    )  # hyper-parameters, e.g. {'window': 14}
    output_names: Optional[List[str]] = field(
        default=None
    )  # names of output columns, e.g. ['ma20']

    ohlcv_data: Optional[OHLCVData] = field(init=False, default=None)
    indicator_values: Optional[pd.DataFrame] = field(init=False, default=None)

    def __post_init__(self) -> None:
        # default: single output with the same name as the indicator
        if self.output_names is None:
            object.__setattr__(self, "output_names", [self.name.lower()])

    @property
    def values(self) -> pd.DataFrame:
        """
        Get the computed indicator values.

        Returns:
          Optional[List[pd.Series]]: List of Series with indicator values if computed, else None.
        """
        if self.indicator_values is None:
            raise ValueError(
                "Indicator values have not been computed yet. Call compute() first."
            )
        return self.indicator_values

    def compute(self, ohlcv: OHLCVData) -> pd.DataFrame:
        """
        Compute indicator values given OHLCV data.

        Args:
          ohlcv (OHLCVData): OHLCVData used to compute the indicator.

        Returns:
          pd.DataFrame: DataFrame indexed like `ohlcv` with indicator values.
        """
        indicator_values = self._compute(ohlcv)

        # Rename columns if multiple outputs
        if isinstance(self.output_names, list) and len(self.output_names) == len(
            indicator_values.columns
        ):
            indicator_values.columns = self.output_names

        # Store the computed values and input data
        object.__setattr__(self, "ohlcv_data", ohlcv)
        object.__setattr__(self, "indicator_values", indicator_values)
        return self.values

    @abstractmethod
    def _compute(self, ohlcv: OHLCVData) -> pd.DataFrame:
        """
        Compute indicator values given OHLCV data. This is the actual method to be implemented by subclasses.

        Args:
          ohlcv (OHLCVData): OHLCVData used to compute the indicator.

        Returns:
          pd.DataFrame: DataFrame indexed like `ohlcv` with indicator values.
        """
        raise NotImplementedError
