from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import singledispatch
from typing import Any, List, Mapping, Optional, Sequence, Union

import pandas as pd

from ..core import OHLCVData
from ..indicators import Indicator


class Color(str, Enum):
    RED = "#ef5350"
    GREEN = "#26a69a"
    BLUE = "#42a5f5"
    NAVY = "#0A1172"
    ORANGE = "#ffa726"
    PURPLE = "#ab47bc"
    BLACK = "#000000"
    WHITE = "#ffffff"
    YELLOW = "#ffff00"
    CYAN = "#00ffff"
    MAGENTA = "#ff00ff"
    GRAY = "#9e9e9e"


DEFAULT_PALETTE = (
    Color.BLUE,
    Color.PURPLE,
    Color.ORANGE,
    Color.NAVY,
    Color.MAGENTA,
    Color.CYAN,
)


class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"


@dataclass(frozen=True)
class SeriesPlot:
    """
    Represents a plot configuration for a series.
    """

    series: pd.Series
    label: Optional[str] = field(default=None)
    color: Color = field(default=Color.BLUE)
    type: ChartType = field(default=ChartType.LINE)
    panel: int = field(default=0)
    params: dict = field(default_factory=dict)


@dataclass
class PlotContext:
    """Context for plotting, including panel index, color palette, chart types, and extra parameters."""

    panel: int = 0
    palette: Optional[List[Color]] = None
    types: Optional[List[ChartType]] = None
    backend: Optional[str] = None  # e.g., 'mpl', 'plotly', etc.
    extra: dict = field(default_factory=dict)


@singledispatch
def indicator_to_seriesplots(
    indicator: Indicator,
    ctx: PlotContext,
) -> List[SeriesPlot]:
    """
    Helper function to convert an Indicator to SeriesPlot configurations.

    Args:
      indicator (Indicator): The indicator to convert.
      panel (int): The panel index to plot on.
      palette (Optional[List[Color]]): List of colors to use for the plots.
      types (Optional[List[ChartType]]): List of chart types for each series.
      **kwargs: Additional parameters to pass to each SeriesPlot.

    Returns:
      List[SeriesPlot]: List of SeriesPlot configurations.
    """
    palette = ctx.palette or DEFAULT_PALETTE
    types = ctx.types or [ChartType.LINE] * len(indicator.values.columns)

    plots: List[SeriesPlot] = []
    df = indicator.values
    for i, col in enumerate(df.columns):
        plot = SeriesPlot(
            series=df[col],
            label=col,
            panel=ctx.panel,
            type=types[i] if i < len(types) else ChartType.LINE,
            color=palette[i % len(palette)],
            params=ctx.extra,
        )
        plots.append(plot)

    return plots


@dataclass
class Plotter(ABC):
    """
    Base class for all plot backends.
    """

    backend_name: str
    _fig: Optional[Any] = field(init=False, default=None)

    @property
    def fig(self) -> Any:
        """Get the underlying figure object."""
        if self._fig is None:
            raise ValueError("No figure has been created yet.")
        return self._fig

    @fig.setter
    def fig(self, value: Any) -> None:
        self._fig = value

    def plot(
        self,
        ohlcv: OHLCVData,
        title: Optional[str] = None,
        indicators: Optional[Sequence[Indicator]] = None,
        panels: Optional[List[int]] = None,
        palette: Optional[List[Color]] = None,
        **kwargs,
    ) -> None:
        """
        Plot the given data.
        Args:
          data (pd.DataFrame): Data to plot.
          chart (ChartType): Type of chart to plot.
          **kwargs: Additional keyword arguments for plotting.
        """
        # 1) Convert indicators to SeriesPlot configurations
        series_plots: List[SeriesPlot] = []

        if indicators:
            if not panels or len(panels) < len(indicators):
                raise ValueError(
                    "Length of panels list must match length of indicators list."
                )

            palette = palette or list(DEFAULT_PALETTE)
            palettes: Mapping[int, List[Color]] = {}

            for i, ind in enumerate(indicators):
                panel = panels[i]
                palettes.setdefault(panel, [] + palette)
                ctx = PlotContext(
                    panel=panel,
                    palette=palettes[panel],
                    backend=self.backend_name,
                    extra=kwargs,
                )
                # Rotate palette for next use
                palettes[panel] = (
                    palettes[panel][ind.values.shape[1] :]
                    + palettes[panel][: ind.values.shape[1]]
                )
                plots = indicator_to_seriesplots(ind, ctx)
                series_plots.extend(plots)

        # 2) Delegate to backend-specific plotting implementation
        self._render(ohlcv, series_plots, title, **kwargs)

    @abstractmethod
    def _render(
        self,
        ohlcv: OHLCVData,
        series_plots: List[SeriesPlot],
        title: Union[str, None] = None,
        **kwargs,
    ) -> None:
        """
        Backend-specific rendering implementation.

        Args:
          ohlcv (OHLCVData): OHLCV data to plot.
          series_plots (List[SeriesPlot]): List of SeriesPlot configurations.
          title (Union[str, None]): Title of the plot.
          **kwargs: Additional keyword arguments for plotting.
        """
        raise NotImplementedError
