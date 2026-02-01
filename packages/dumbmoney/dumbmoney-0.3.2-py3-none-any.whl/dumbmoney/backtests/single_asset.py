from typing import List

import pandas as pd

from ..core import (
    OHLCVData,
    Side,
    Trade,
    SingleAssetPortfolioState,
    BacktestMetrics,
    BacktestResult,
)
from ..strategies import Strategy
from ..policies import PositionPolicy, DecisionContext


class SingleAssetBacktester:
    def __init__(
        self,
        initial_cash: float = 100_000.0,
        risk_free_rate: float = 0.0,
    ):
        self.initial_cash = initial_cash
        self.risk_free_rate = risk_free_rate

    def run(
        self,
        symbol: str,
        ohlcv: OHLCVData,
        strategy: Strategy,
        policy: PositionPolicy,
    ) -> BacktestResult:
        """
        Calculate target position percentages using the provided policy and strategy signals.

        """
        # Generate signals using the strategy
        signal_frame = strategy.generate_signals(ohlcv)
        signals = signal_frame.signals

        # Initialize portfolio state
        cash = self.initial_cash
        position_qty = 0  # number of shares held
        trades: List[Trade] = []
        equity_records: List[tuple[pd.Timestamp, float]] = []

        for ts, bar in ohlcv.iterrows():
            price = float(bar["close"])

            portfolio_state = SingleAssetPortfolioState(
                timestamp=ts,  # type: ignore
                cash=cash,
                position_qty=position_qty,
                price=price,
            )

            signal_row = signals.loc[ts] if ts in signals.index else pd.Series()

            decision_ctx = DecisionContext(
                symbol=symbol,
                timestamp=ts,  # type: ignore
                price=price,
                signal_row=signal_row,  # type: ignore
                portfolio=portfolio_state,
                strategy_config=strategy.config,
            )

            target_pct = policy.target_position_pct(decision_ctx)

            # Execute trades to adjust position
            total_value = portfolio_state.total_value
            target_value = total_value * target_pct
            target_qty = target_value / price if price > 0 else 0
            delta_qty = target_qty - position_qty

            if abs(delta_qty) > 1e-6:  # threshold to avoid tiny trades
                side: Side = "buy" if delta_qty > 0 else "sell"
                trade_qty = int(abs(delta_qty))  # assume we trade whole shares
                trade_cach = trade_qty * price

                if side == "buy":
                    if trade_cach > cash + 1e-6:
                        trade_qty = int(cash / price)  # adjust to max affordable
                        trade_cach = trade_qty * price
                    cash -= trade_cach
                    position_qty += trade_qty
                    pnl = 0.0  # TODO: calculate PnL properly
                else:  # sell
                    cash += trade_cach
                    position_qty -= trade_qty
                    pnl = 0.0  # TODO: calculate PnL properly

                trade = Trade(
                    timestamp=ts,  # type: ignore
                    side=side,
                    quantity=trade_qty,
                    price=price,
                    pnl=pnl,
                )
                trades.append(trade)

            # Record equity
            portfolio_state = SingleAssetPortfolioState(
                timestamp=ts,  # type: ignore
                cash=cash,
                position_qty=position_qty,
                price=price,
            )
            equity_records.append((ts, portfolio_state.total_value))  # type: ignore

        equity_curve = pd.Series(
            data=[val for _, val in equity_records],
            index=[ts for ts, _ in equity_records],
            name="equity_curve",
        )

        metrics = self._compute_metrics(equity_curve, trades)

        return BacktestResult(
            symbol=symbol,
            timeframe=strategy.config.timeframe,
            equity_curve=equity_curve,
            trades=trades,
            metrics=metrics,
            config=strategy.config.to_dict(),
        )

    def _compute_metrics(
        self,
        equity_curve: pd.Series,
        trades: List[Trade],
    ) -> BacktestMetrics:
        if len(equity_curve) < 2:
            return BacktestMetrics(
                total_return=0.0,
                annualized_return=0.0,
                max_drawdown=0.0,
                num_trades=len(trades),
                sharpe_ratio=None,
                win_rate=None,
            )

        returns = equity_curve.pct_change().fillna(0.0)
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1.0

        ann_return = (
            (1 + total_return) ** (252 / len(equity_curve))
        ) - 1.0  # assuming daily bars and 252 trading days

        running_max = equity_curve.cummax()
        drawdowns = (equity_curve - running_max) / running_max
        max_drawdown = float(drawdowns.min())

        if returns.std() > 1e-6:
            sharpe_ratio = (
                (returns.mean() - self.risk_free_rate / 252)
                / returns.std()
                * (252**0.5)
            )
        else:
            sharpe_ratio = None

        win_trades = [t for t in trades if t.pnl > 0]
        win_rate = len(win_trades) / len(trades) if trades else None

        return BacktestMetrics(
            total_return=total_return,
            annualized_return=ann_return,
            max_drawdown=max_drawdown,
            num_trades=len(trades),
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
        )
