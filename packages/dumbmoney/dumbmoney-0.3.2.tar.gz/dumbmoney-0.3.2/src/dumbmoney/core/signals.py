from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pandas as pd

from .data import OHLCVData


class SignalType(str, Enum):
    FLAT = "flat"
    LONG = "long"
    SHORT = "short"  # For short selling, if supported


@dataclass
class SignalFrame:
    """
    Wrapper of strategy output signals.
    """

    signals: (
        pd.DataFrame
    )  # DataFrame with DatetimeIndex and 'signal_type' (SignalType) column
    meta: Optional[dict] = None

    @classmethod
    def empty_like(cls, ohlcv: OHLCVData) -> "SignalFrame":
        s = pd.DataFrame(index=ohlcv.index)
        s["signal_type"] = SignalType.FLAT
        s["strength"] = 0.0  # the confidence level of the signal, 0.0 to 1.0
        return cls(signals=s, meta={})
