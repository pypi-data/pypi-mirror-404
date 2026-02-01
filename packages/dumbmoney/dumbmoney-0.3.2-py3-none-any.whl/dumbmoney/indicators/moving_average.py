from dataclasses import dataclass
from typing import Literal, Union

import pandas as pd

from .indicator import Indicator
from ..core import OHLCVData


@dataclass(frozen=True)
class MovingAverage(Indicator):
    """
    Compute the Moving Average (MA) on a column ("close" by default) of OHLCV data over a specified window.
    """

    def __init__(
        self,
        name: Union[str, None] = None,
        window: int = 20,
        ma_type: Literal["SMA", "EMA"] = "SMA",
        input_col: str = "close",
    ):
        super().__init__(
            name=name or f"{ma_type.upper()}{window}",
            inputs=[input_col],
            params={"window": window, "ma_type": ma_type},
        )

    def _compute(self, ohlcv: OHLCVData) -> pd.DataFrame:
        col_data = ohlcv[self.inputs[0]]

        if self.params["ma_type"] == "SMA":
            series = col_data.rolling(window=self.params["window"]).mean()
        elif self.params["ma_type"] == "EMA":
            series = col_data.ewm(span=self.params["window"], adjust=False).mean()
        else:
            raise ValueError(f"Unsupported MA type: {self.params['ma_type']}")

        return pd.DataFrame(series)
