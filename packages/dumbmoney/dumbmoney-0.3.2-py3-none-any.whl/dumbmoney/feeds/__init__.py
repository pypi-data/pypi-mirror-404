from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional, Any, List, Union

import pandas as pd

from .feed import AdjustType, BaseFeed
from .feed_service import DataFeedService
from ..core import OHLCVData, normalize_ohlcv, StockDetails


@lru_cache(maxsize=1)
def default_feed_service() -> DataFeedService:
    from .akshare import AkshareFeed
    from .tushare import TushareFeed
    from .massive import MassiveFeed

    feeds: List[BaseFeed] = [AkshareFeed()]

    try:
        tushare_feed = TushareFeed()
        feeds.insert(0, tushare_feed)
    except Exception:
        pass

    try:
        massive_feed = MassiveFeed()
        feeds.insert(0, massive_feed)
    except Exception:
        pass

    try:
        from .tiger import TigerFeed, TigerConfig
        import os

        tiger_config = TigerConfig(
            private_key=os.getenv("TIGER_PRIVATE_KEY", ""),
            tiger_id=os.getenv("TIGER_ID", ""),
            account=os.getenv("TIGER_ACCOUNT", ""),
            license=os.getenv("TIGER_LICENSE", ""),
        )
        tiger_feed = TigerFeed(config=tiger_config)
        feeds.insert(0, tiger_feed)
    except Exception:
        pass

    return DataFeedService(feeds=feeds)


def get_ohlcv(
    symbol: str,
    start: Optional[Any] = None,
    end: Optional[Any] = None,
    adjust: AdjustType = "forward",
    fields: Optional[List[str]] = None,
) -> OHLCVData:
    end_date: date = end or date.today()
    start_date = start or date(end_date.year - 1, end_date.month, end_date.day)
    service = default_feed_service()
    return service.get_ohlcv(
        symbol=symbol,
        start=start_date,
        end=end_date,
        adjust=adjust,
        fields=fields,
    )


def load_ohlcv_from_csv(
    filepath: str,
) -> OHLCVData:
    if not Path(filepath).is_file():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    df = pd.read_csv(filepath, parse_dates=["date"], index_col="date")
    ohlcv = normalize_ohlcv(df, fields=[])
    return ohlcv


def export_ohlcv_to_csv(
    ohlcv: OHLCVData,
    filepath: str,
) -> None:
    ohlcv.to_csv(filepath, index=True)


def get_stock_details(
    symbol: str,
) -> Union[StockDetails, None]:
    service = default_feed_service()
    return service.get_stock_details(symbol=symbol)
