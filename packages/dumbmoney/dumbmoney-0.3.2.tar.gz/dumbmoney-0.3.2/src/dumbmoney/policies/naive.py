# Some naive policies

from dataclasses import dataclass

from .policy import DecisionContext, PositionPolicy
from ..core import SignalType


@dataclass
class LongFlatAllInConfig:
    max_long_pct: float = 1.0
    min_strength: float = 0.5  # used to filter out weak signals


class LongFlatAllInPolicy(PositionPolicy):
    """
    A naive policy that goes all-in long on buy signals and fully flat on sell/hold signals.
    """

    def __init__(self, cfg: LongFlatAllInConfig):
        self.cfg = cfg

    def target_position_pct(self, ctx: DecisionContext) -> float:
        sig_type = ctx.signal_row.get("signal_type", SignalType.FLAT)
        strength = ctx.signal_row.get("strength", 0.0)

        if strength < self.cfg.min_strength:
            # too weak to act upon
            return (
                ctx.portfolio.position_value / ctx.portfolio.total_value
            )  # maintain current position

        if sig_type == SignalType.LONG:
            return self.cfg.max_long_pct
        elif sig_type == SignalType.FLAT:
            return 0.0

        return 0.0  # default to flat for any other signal types, SHORT is not supported in this naive policy
