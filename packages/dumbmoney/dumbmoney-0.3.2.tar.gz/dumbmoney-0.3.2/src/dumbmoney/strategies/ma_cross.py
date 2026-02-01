from dataclasses import dataclass

from ..core import OHLCVData, SignalType, SignalFrame
from ..indicators import MovingAverage
from .strategy import Strategy, StrategyConfig


@dataclass
class MACrossParams:
    fast_window: int = 5
    slow_window: int = 20
    min_cross_strength: float = (
        0.0  # minimum difference between MAs to consider a valid cross
    )


class MACrossStrategy(Strategy):
    """
    Moving Average Crossover Strategy.

    Generates LONG signals when the fast MA crosses above the slow MA,
    and SHORT signals when the fast MA crosses below the slow MA.
    """

    def __init__(self, params: MACrossParams, timeframe: str = "1d"):
        cfg = StrategyConfig(
            name=f"MA_Cross_{params.fast_window}_{params.slow_window}",
            timeframe=timeframe,
            params=params.__dict__,
        )
        super().__init__(cfg)
        self.params = params

    def generate_signals(self, ohlcv: OHLCVData) -> SignalFrame:
        ma_fast = MovingAverage(
            window=self.params.fast_window,
        )
        ma_fast.compute(ohlcv)
        ma_slow = MovingAverage(
            window=self.params.slow_window,
        )
        ma_slow.compute(ohlcv)

        fast = ma_fast.values
        fast = fast[fast.columns[0]]
        slow = ma_slow.values
        slow = slow[slow.columns[0]]

        cross_up = (fast > slow) & (fast.shift(1) <= slow.shift(1))
        cross_down = (fast < slow) & (fast.shift(1) >= slow.shift(1))

        sig_frame = SignalFrame.empty_like(ohlcv)

        # Generate LONG signals
        sig_frame.signals.loc[cross_up, "signal_type"] = SignalType.LONG
        sig_frame.signals.loc[cross_up, "strength"] = (
            1.0  # could be refined based on cross magnitude
        )

        # Generate FLAT signals
        sig_frame.signals.loc[cross_down, "signal_type"] = SignalType.FLAT
        sig_frame.signals.loc[cross_down, "strength"] = (
            1.0  # could be refined based on cross magnitude
        )

        sig_frame.meta = {"config": self.config.to_dict()}
        return sig_frame
