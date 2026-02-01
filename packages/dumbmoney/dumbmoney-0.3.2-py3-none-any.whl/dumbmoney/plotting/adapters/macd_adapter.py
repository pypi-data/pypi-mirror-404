from typing import List

from ..plotter import (
    Color,
    ChartType,
    indicator_to_seriesplots,
    PlotContext,
    SeriesPlot,
)
from ...indicators import MACD


@indicator_to_seriesplots.register
def macd_to_seriesplots(indicator: MACD, ctx: PlotContext) -> List[SeriesPlot]:
    """Convert MACD indicator to SeriesPlot configurations."""
    series_plots: List[SeriesPlot] = []

    df = indicator.values
    if len(df.columns) != 3:
        raise ValueError("MACD indicator must have exactly three output columns.")

    # MACD Line, assuming the first column is MACD Line
    dif_plot = SeriesPlot(
        series=df[df.columns[0]],
        label="DIF",
        panel=ctx.panel,
        type=ChartType.LINE,
        color=ctx.palette[0] if ctx.palette else Color.BLUE,
    )

    # Signal Line, assuming the second column is Signal Line
    dea_plot = SeriesPlot(
        series=df[df.columns[1]],
        label="DEA",
        panel=ctx.panel,
        type=ChartType.LINE,
        color=ctx.palette[1] if ctx.palette else Color.ORANGE,
    )

    # Histogram
    hist_plot = SeriesPlot(
        series=df[df.columns[2]],
        label="MACD",
        panel=ctx.panel,
        type=ChartType.BAR,
        color=ctx.palette[2] if ctx.palette else Color.GRAY,
    )

    # Set secondary_y parameter
    hist_plot.params["secondary_y"] = False
    dif_plot.params["secondary_y"] = True
    dea_plot.params["secondary_y"] = True

    if ctx.backend == "mpl":
        # Fill between parameters for histogram
        hist = df[df.columns[2]]
        fb_positive = dict(
            y1=hist.values,
            y2=0,
            where=hist > 0,
            color=Color.GREEN,
            alpha=0.6,
            interpolate=True,
            panel=ctx.panel,
        )
        fb_negative = dict(
            y1=hist.values,
            y2=0,
            where=hist < 0,
            color=Color.RED,
            alpha=0.6,
            interpolate=True,
            panel=ctx.panel,
        )
        hist_plot.params["fill_between"] = [fb_positive, fb_negative]
        object.__setattr__(
            hist_plot, "color", Color.WHITE
        )  # Override color for better visibility
    elif ctx.backend == "plotly":
        # Extra parameters for plotly
        hist_plot.params["marker_color"] = [
            Color.GREEN.value if v >= 0 else Color.RED.value
            for v in hist_plot.series.values
        ]

    series_plots.extend([hist_plot, dif_plot, dea_plot])

    return series_plots
