from typing import List, Literal, Optional, Sequence

from ..core import OHLCVData
from ..indicators import Indicator
from . import adapters  # noqa: F401 Ensure adapters are registered
from .plotter import Plotter

PlotterBackend = Literal["mpl", "plotly"]


def plot(
    ohlcv: OHLCVData,
    title: Optional[str] = None,
    indicators: Optional[Sequence[Indicator]] = None,
    panels: Optional[List[int]] = None,
    backend: PlotterBackend = "mpl",
    show: bool = True,
    **kwargs,
) -> Plotter:
    """Plot OHLCV data with indicators using the specified backend."""

    if backend == "mpl":
        from .mplfinance import MPLFinancePlotter

        plotter = MPLFinancePlotter()
    elif backend == "plotly":
        from .plotly import PlotlyPlotter

        plotter = PlotlyPlotter()
    else:
        raise ValueError(f"Unsupported plotter backend: {backend}")

    # series_plots = create_series_plots(indicators)

    plotter.plot(
        ohlcv, title=title, indicators=indicators, panels=panels, show=show, **kwargs
    )

    return plotter
