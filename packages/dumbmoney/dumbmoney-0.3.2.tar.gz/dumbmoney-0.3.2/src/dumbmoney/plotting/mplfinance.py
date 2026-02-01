from dataclasses import dataclass, field
from typing import List, Union

from .plotter import (
    Plotter,
    SeriesPlot,
    ChartType,
    Color,
    DEFAULT_PALETTE,
    indicator_to_seriesplots,
)
from ..core import OHLCVData
from ..indicators import (
    Indicator,
    MovingAverage,
    MACD,
)


@dataclass
class MPLFinancePlotter(Plotter):
    """
    Plotter implementation using mplfinance.
    """

    backend_name: str = field(default="mpl")
    style: str = field(default="yahoo")

    def _render(
        self,
        ohlcv: OHLCVData,
        series_plots: List[SeriesPlot],
        title: Union[str, None] = None,
        show: bool = True,
        **kwargs,
    ) -> None:
        import matplotlib.pyplot as plt
        import mplfinance as mpf

        if self._fig is not None:
            plt.close(self._fig)

        has_volume = "volume" in ohlcv.columns
        panel_ratios = [6, 4] if has_volume else [6]

        mpf_kwargs = {
            "type": "candle",
            "style": self.style,
            "title": title,
            "volume": has_volume,
            "returnfig": True,
            "panel_ratios": panel_ratios,
        }
        mpf_kwargs.update(kwargs)

        if series_plots:
            max_panel = max(plot.panel for plot in series_plots)
            panel_ratios = panel_ratios + [3] * (max_panel - 1)

            addplots = []
            fill_between = []
            for p in series_plots:
                s = p.series.reindex(ohlcv.index)
                ap = mpf.make_addplot(
                    s,
                    panel=p.panel,
                    type=p.type,
                    color=p.color.value,
                    label=p.label,
                )
                addplots.append(ap)
                if "fill_between" in p.params:
                    fill_between.extend(p.params["fill_between"])

            mpf_kwargs["addplot"] = addplots
            mpf_kwargs["panel_ratios"] = panel_ratios
            if fill_between:
                mpf_kwargs["fill_between"] = fill_between

        self.fig, _ = mpf.plot(ohlcv, **mpf_kwargs)

        if show:
            plt.show()

    def create_series_plots(self, indicators: List[Indicator]) -> List[SeriesPlot]:
        """Create SeriesPlot configurations for the given indicators."""
        series_plots: List[SeriesPlot] = []

        ma_indicators: List[MovingAverage] = []
        vol_ma_indicators: List[MovingAverage] = []

        panel = 2
        for indicator in indicators:
            if isinstance(indicator, MovingAverage):
                if indicator.inputs[0] == "volume":
                    vol_ma_indicators.append(indicator)
                else:
                    ma_indicators.append(indicator)
                continue

            if isinstance(indicator, MACD):
                plts = self._macd_to_seriesplots(indicator, panel=panel)
                series_plots.extend(plts)
                panel += 1
                continue

            plts = indicator_to_seriesplots(indicator, panel=panel)
            series_plots.extend(plts)
            panel += 1

        # Add Price MA indicators to the main panel (panel 0)
        series_plots.extend(self._ma_indicators_to_seriesplots(ma_indicators, panel=0))

        # Add Volume MA indicators to the main panel (panel 1)
        series_plots.extend(
            self._ma_indicators_to_seriesplots(vol_ma_indicators, panel=1)
        )

        # Sort series plots by panel
        series_plots.sort(key=lambda sp: sp.panel)

        return series_plots

    def _ma_indicators_to_seriesplots(
        self, ma_indicators: List[MovingAverage], panel: int = 0
    ) -> List[SeriesPlot]:
        """Convert MA indicators to SeriesPlot configurations."""
        if not ma_indicators:
            return []

        """Check for consistency among MA indicators."""
        input_cols = {ma.inputs[0] for ma in ma_indicators}
        if len(input_cols) > 1:
            raise ValueError("All MA indicators must have the same input column.")

        windows = {ma.params["window"] for ma in ma_indicators}
        if len(windows) != len(ma_indicators):
            raise ValueError("Duplicate MA windows found.")

        ma_indicators.sort(key=lambda ma: ma.params["window"])

        series_plots: List[SeriesPlot] = []
        for i, ma in enumerate(ma_indicators):
            plts = indicator_to_seriesplots(
                ma,
                panel=panel,
                palette=[DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]],
                type=[ChartType.LINE],
            )
            series_plots.extend(plts)

        return series_plots

    def _macd_to_seriesplots(
        self, macd_indicator: MACD, panel: int = 0
    ) -> List[SeriesPlot]:
        """Convert MACD indicator to SeriesPlot configurations."""
        if not isinstance(macd_indicator, MACD):
            raise ValueError("Provided indicator is not a MACD instance.")

        series_plots: List[SeriesPlot] = []
        df = macd_indicator.values

        if len(df.columns) != 3:
            raise ValueError("MACD indicator must have exactly three output columns.")

        # Histogram, assuming the third column is Histogram
        hist = df[df.columns[2]]
        fb_positive = dict(
            y1=hist.values,
            y2=0,
            where=hist > 0,
            color=Color.GREEN,
            alpha=0.6,
            interpolate=True,
            panel=panel,
        )
        fb_negative = dict(
            y1=hist.values,
            y2=0,
            where=hist < 0,
            color=Color.RED,
            alpha=0.6,
            interpolate=True,
            panel=panel,
        )
        histogram = SeriesPlot(
            series=hist,
            panel=panel,
            label="MACD",
            type=ChartType.BAR,
            color=Color.WHITE,
            params=dict(secondary_y=False, fill_between=[fb_positive, fb_negative]),
        )
        series_plots.append(histogram)

        # MACD Line, assuming the first column is MACD Line
        macd_line = SeriesPlot(
            series=df[df.columns[0]],
            label="DIF",
            panel=panel,
            type=ChartType.LINE,
            color=Color.BLUE,
            params={"secondary_y": True},
        )
        series_plots.append(macd_line)

        # Signal Line, assuming the second column is Signal Line
        signal_line = SeriesPlot(
            series=df[df.columns[1]],
            label="DEA",
            panel=panel,
            type=ChartType.LINE,
            color=Color.ORANGE,
            params={"secondary_y": True},
        )
        series_plots.append(signal_line)

        return series_plots
