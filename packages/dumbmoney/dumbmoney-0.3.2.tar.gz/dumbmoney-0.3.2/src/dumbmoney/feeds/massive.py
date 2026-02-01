from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from functools import lru_cache
from typing import List, Optional, Literal, Union

import os
import pandas as pd

from dumbmoney.core import StockDetails

from .feed import AdjustType, BaseFeed, StockMarket
from ..core import OHLCVData, normalize_ohlcv
from ..logger import logger

from massive import RESTClient
from massive.rest.models.tickers import TickerDetails


@lru_cache(maxsize=1, typed=True)
def get_massive_client(api_key: Optional[str] = None) -> RESTClient:
    if not api_key:
        raise ValueError(
            "MASSIVE_KEY is not found. Set it either in environment variable or pass it explicitly."
        )
    return RESTClient(api_key)


@dataclass
class MassiveFeed(BaseFeed):
    """Data feed backed by Massive."""

    name: str = "Massive"

    api_key: Optional[str] = field(default_factory=lambda: os.getenv("MASSIVE_KEY"))
    massive_client: RESTClient = field(init=False)

    def __post_init__(self):
        self.massive_client = get_massive_client(self.api_key)
        logger.debug("MassiveFeed initialized.")

    @classmethod
    def markets(cls) -> Union[List[StockMarket], Literal["*"]]:
        return [StockMarket.US]

    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        adjust: AdjustType = "forward",
        fields: Optional[List[str]] = None,
    ) -> OHLCVData:
        code, _ = self.check_symbol(symbol)

        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        logger.debug(
            f"Massive: fetching {symbol} from {start_str} to {end_str} with adjust={adjust}"
        )

        aggs = []
        for a in self.massive_client.list_aggs(
            code,
            1,
            "day",
            start_str,
            end_str,
            adjusted=(adjust != "none"),
        ):
            aggs.append(a)

        df = pd.DataFrame([asdict(a) for a in aggs])

        df["date"] = pd.to_datetime(
            df["timestamp"].apply(lambda ts: datetime.fromtimestamp(ts / 1000).date())
        )

        # filter df by date range
        df = df[
            (df["date"] >= pd.to_datetime(start)) & (df["date"] <= pd.to_datetime(end))
        ]

        return normalize_ohlcv(pd.DataFrame(df), fields=fields)

    def get_stock_details(self, symbol: str) -> Union[StockDetails, None]:
        try:
            code, market = self.check_symbol(symbol)
        except Exception:
            return None

        if market not in [StockMarket.US]:
            return None

        logger.debug(f"Massive: fetching stock details for {symbol}")

        details = self.massive_client.get_ticker_details(code)

        if not isinstance(details, TickerDetails):
            return None

        listing_date = (
            datetime.strptime(details.list_date, "%Y-%m-%d").date()
            if details.list_date
            else None
        )

        return StockDetails(
            symbol=code,
            name=details.name or "",
            market="US",
            exchange="NYSE"
            if details.primary_exchange == "XNYS"
            else ("NASDAQ" if details.primary_exchange == "XNAS" else None),
            listing_date=listing_date,
            total_shares=details.share_class_shares_outstanding or None,
            float_shares=None,
            is_etf=details.type == "ETF",
            tags=[details.sic_description.strip()] if details.sic_description else [],
        )
