from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Literal, Optional, Tuple, Union

import re

from ..core import OHLCVData, StockDetails


AdjustType = Literal["none", "forward", "backward"]


class StockMarket(str, Enum):
    SZ = "SZ"
    SH = "SH"
    HK = "HK"
    KCB = "KCB_SH"
    ETF_SZ = "ETF_SZ"
    ETF_SH = "ETF_SH"
    US = "US"
    UNKNOWN = "UNKNOWN"


def infer_stock_market(symbol: str) -> Tuple[str, StockMarket]:
    """
    Helper function to infer market from symbol.

    Args:
      symbol: str, e.g. "000001.SZ", "AAPL.US", "06966.HK", etc. Suffixes are not required for CN_A/CN_KCB/CN_ETF shares. However, if present, they must be valid.

    Returns:
      Tuple[str, StockMarket]: A tuple containing the code and the StockMarket enum value.
    """
    symbol = symbol.strip().upper()

    if "." in symbol:
        code, suffix = symbol.rsplit(".", 1)
    else:
        code = symbol
        suffix = ""

    if suffix == "US" and len(code) <= 5:
        return code, StockMarket.US

    if re.match(r"^\d{4,5}$", code) and suffix == "HK":
        return code, StockMarket.HK

    if re.match(r"^60\d{4}$", code) and suffix in ["SH", ""]:
        return code, StockMarket.SH

    if re.match(r"^(00|30)\d{4}$", code) and suffix in ["SZ", ""]:
        return code, StockMarket.SZ

    if re.match(r"^68\d{4}$", code) and suffix in ["SH", ""]:
        return code, StockMarket.KCB

    if re.match(r"^5[168]\d{4}$", code) and suffix in ["SH", ""]:
        return code, StockMarket.ETF_SH

    if re.match(r"^15\d{4}$", code) and suffix in ["SZ", ""]:
        return code, StockMarket.ETF_SZ

    return code, StockMarket.UNKNOWN


@dataclass
class BaseFeed(ABC):
    """
    Abstract base for all data feeds.
    Returns OHLCV-style time series for a symbol.
    """

    name: str

    @classmethod
    @abstractmethod
    def markets(cls) -> Union[List[StockMarket], Literal["*"]]:
        """Return a list of supported markets."""
        raise NotImplementedError

    @classmethod
    def check_symbol(cls, symbol: str) -> Tuple[str, StockMarket]:
        """
        Check if the feed supports the given symbol. Split the symbol into code and market if it does.

        Args:
          symbol (str): The stock symbol to check.

        Returns:
          Tuple[str, StockMarket]: The normalized code and market if supported.

        Raises:
          ValueError: If the symbol is not supported by this feed.
        """
        code, market = infer_stock_market(symbol)
        supported_markets = cls.markets()
        if supported_markets == "*" or market in supported_markets:
            return code, market
        raise ValueError(f"Symbol {symbol!r} not supported by {cls.__name__}.")

    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        adjust: AdjustType = "forward",
        fields: Optional[List[str]] = None,
    ) -> OHLCVData:
        """
        Return a DataFrame indexed by datetime for a given symbol.

        Expected columns at least: ['open', 'high', 'low', 'close', 'volume']
        but may include more (e.g., 'vwap', 'turnover', etc.)
        """
        raise NotImplementedError

    @abstractmethod
    def get_stock_details(
        self,
        symbol: str,
    ) -> Union[StockDetails, None]:
        """
        Return stock details for a given symbol.
        """
        raise NotImplementedError
