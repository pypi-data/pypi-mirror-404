from dataclasses import dataclass
from typing import Union

import pandas as pd

from .indicator import Indicator
from ..core import OHLCVData


@dataclass(frozen=True)
class RSI(Indicator):
    """
    Compute the Relative Strength Index (RSI) on a column ("close" by default) of OHLCV data over a specified window.
    """

    def __init__(
        self,
        name: Union[str, None] = None,
        window: int = 14,
        input_col: str = "close",
    ):
        super().__init__(
            name=name or "RSI",
            inputs=[input_col],
            params={"window": window},
        )

    def _compute(self, ohlcv: OHLCVData) -> pd.DataFrame:
        # Use Wilder's smoothing method for average gain and loss
        col_data = ohlcv[self.inputs[0]]

        delta = col_data.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)

        period = self.params["window"]

        # 1) Calculate the initial average gain and loss
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        # Create full-length arrays for smoothed values
        avg_gain_w = avg_gain.copy()
        avg_loss_w = avg_loss.copy()

        # 2) Apply Wilder's smoothing method
        for i in range(period + 1, len(col_data)):
            # previous smoothed value
            prev_avg_gain = avg_gain_w.iat[i - 1]
            prev_avg_loss = avg_loss_w.iat[i - 1]

            current_gain = gain.iat[i]
            current_loss = loss.iat[i]

            avg_gain_w.iat[i] = (prev_avg_gain * (period - 1) + current_gain) / period
            avg_loss_w.iat[i] = (prev_avg_loss * (period - 1) + current_loss) / period

        # 3) Calculate RSI
        rs = avg_gain_w / avg_loss_w
        rsi = 100 - (100 / (1 + rs))

        # Handle edge cases where avg_loss is zero
        rsi = rsi.where(avg_loss_w != 0)
        rsi = rsi.mask((avg_loss_w == 0) & (avg_gain_w > 0), 100.0)
        rsi = rsi.mask((avg_loss_w == 0) & (avg_gain_w == 0), 50.0)

        return pd.DataFrame(rsi)
