from dataclasses import dataclass, field
from typing import List, Union

import pandas as pd

from .plotter import (
    Plotter,
    SeriesPlot,
    ChartType,
    Color,
)
from ..core import OHLCVData


def infer_offdays_from_index(idx: pd.DatetimeIndex) -> List[pd.Timestamp]:
    """Infer offdays from DatetimeIndex by finding gaps larger than 1 day."""
    dates = idx.normalize().unique()
    all_days = pd.date_range(start=dates.min(), end=dates.max(), freq="D")
    offdays = all_days.difference(dates)
    return list(offdays)


@dataclass
class PlotlyPlotter(Plotter):
    """
    Plotter implementation using Plotly.
    """

    backend_name: str = field(default="plotly")
    height: int = field(default=700)

    def _render(
        self,
        ohlcv: OHLCVData,
        series_plots: List[SeriesPlot],
        title: Union[str, None] = None,
        show: bool = True,
        **kwargs,
    ) -> None:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        panels = max((p.panel for p in series_plots), default=0) + 1

        # Set normalized row heights
        row_heights = [0.7, 0.3] + [0.2] * (panels - 2) if panels > 1 else [1.0]
        total = sum(row_heights)
        row_heights = [h / total for h in row_heights]

        # Set subplot specs
        specs = [[{}] for _ in range(panels)]
        for i, sp in enumerate(series_plots):
            if specs[sp.panel][0].get("secondary_y") is not None:
                continue
            secondary_y = sp.params.get("secondary_y", None)
            if secondary_y is not None:
                specs[sp.panel][0]["secondary_y"] = True

        fig = make_subplots(
            rows=panels,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.01,
            row_heights=row_heights,
            specs=specs,
        )

        # Add OHLCV data
        fig.add_trace(
            go.Candlestick(
                x=ohlcv.index,
                open=ohlcv["open"],
                high=ohlcv["high"],
                low=ohlcv["low"],
                close=ohlcv["close"],
                name="Price",
            ),
            row=1,
            col=1,
        )

        if "volume" in ohlcv.columns:
            up = ohlcv["close"] >= ohlcv["open"]
            down = ~up

            fig.add_trace(
                go.Bar(
                    x=ohlcv.index[up],
                    y=ohlcv["volume"][up],
                    name="Volume",
                    legendgroup="volume",
                    legendgrouptitle=dict(text="Volume"),
                    marker_color=Color.GREEN.value,
                ),
                row=2,
                col=1,
            )

            fig.add_trace(
                go.Bar(
                    x=ohlcv.index[down],
                    y=ohlcv["volume"][down],
                    name="Volume",
                    legendgroup="volume",
                    marker_color=Color.RED.value,
                ),
                row=2,
                col=1,
            )

        # Add series plots
        for p in series_plots:
            trace_extras = {
                "secondary_y": p.params.get("secondary_y", None),
            }
            # Remove None values
            trace_extras = {k: v for k, v in trace_extras.items() if v is not None}

            if p.type == ChartType.BAR:
                fig.add_trace(
                    go.Bar(
                        x=p.series.index,
                        y=p.series.values,
                        name=p.label,
                        marker_color=p.params.get("marker_color", p.color.value),
                    ),
                    row=p.panel + 1,
                    col=1,
                    **trace_extras,
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=p.series.index,
                        y=p.series.values,
                        mode="lines" if p.type == ChartType.LINE else "bars",
                        name=p.label,
                        line=dict(color=p.color.value),
                    ),
                    row=p.panel + 1,
                    col=1,
                    **trace_extras,
                )

        fig.update_layout(
            title_text=title,
            title_x=0.5,
            xaxis_rangeslider_visible=False,
            height=self.height,
            hovermode="x unified",
            **kwargs,
        )

        rangebreaks = []
        rangebreaks.append(dict(values=infer_offdays_from_index(ohlcv.index)))  # type: ignore
        if rangebreaks:
            fig.update_xaxes(rangebreaks=rangebreaks)

        self.fig = fig

        if show:
            fig.show()
