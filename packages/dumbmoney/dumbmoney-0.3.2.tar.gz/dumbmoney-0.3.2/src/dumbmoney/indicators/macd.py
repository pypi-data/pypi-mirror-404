from dataclasses import dataclass
from typing import List, Union

import pandas as pd

from .indicator import Indicator
from ..core import OHLCVData


@dataclass(frozen=True)
class MACD(Indicator):
    """
    Compute MACD on a column ("close" by default) of OHLCV data over a specified window.
    """

    def __init__(
        self,
        name: Union[str, None] = None,
        short: int = 12,
        long: int = 26,
        signal: int = 9,
        input_col: str = "close",
        output_names: List[str] = ["macd", "signal", "histogram"],
    ):
        name = name or "MACD"
        super().__init__(
            name=name,
            inputs=[input_col],
            params={"short": short, "long": long, "signal": signal},
            output_names=output_names,
        )

    def _compute(self, ohlcv: OHLCVData) -> pd.DataFrame:
        col_data = ohlcv[self.inputs[0]]

        ema_short = col_data.ewm(span=self.params["short"], adjust=False).mean()
        ema_long = col_data.ewm(span=self.params["long"], adjust=False).mean()
        macd_line = ema_short - ema_long
        signal_line = macd_line.ewm(span=self.params["signal"], adjust=False).mean()
        histogram = macd_line - signal_line

        output_names = self.output_names
        if not output_names or len(output_names) != 3:
            output_names = ["macd", "signal", "histogram"]

        return pd.DataFrame(
            {
                output_names[0]: macd_line,
                output_names[1]: signal_line,
                output_names[2]: histogram,
            }
        )
