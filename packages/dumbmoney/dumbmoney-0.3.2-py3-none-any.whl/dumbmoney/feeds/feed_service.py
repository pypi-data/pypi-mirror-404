from datetime import date, datetime
from typing import List, Sequence, Optional, Union

from .feed import AdjustType, BaseFeed
from ..core import OHLCVData, StockDetails
from ..logger import logger


def _normalize_date(d) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return datetime.fromisoformat(d).date()
    raise ValueError(f"Invalid date type: {type(d)}")


class DataFeedService:
    """Service to feed data using multiple providers (potentially)."""

    def __init__(self, feeds: Sequence[BaseFeed]) -> None:
        if not feeds:
            raise ValueError("At least one provider must be provided.")
        self.feeds = list(feeds)

    def get_ohlcv(
        self,
        symbol: str,
        start,
        end,
        adjust: AdjustType = "forward",
        fields: Optional[List[str]] = None,
    ) -> OHLCVData:
        start_date = _normalize_date(start)
        end_date = _normalize_date(end)

        errors: List[str] = []

        for feed in self.feeds:
            try:
                df = feed.get_ohlcv(
                    symbol=symbol,
                    start=start_date,
                    end=end_date,
                    adjust=adjust,
                    fields=fields,
                )
                return df
            except Exception as e:
                errors.append(f"Feed {feed.name} failed: {e}")

        raise RuntimeError(
            f"get_ohlcv: all feeds failed for symbol: {symbol} "
            f"({start_date} → {end_date}): {'; '.join(errors)}"
        )

    def get_stock_details(
        self,
        symbol: str,
    ) -> Union[StockDetails, None]:
        errors: List[str] = []

        details: Union[StockDetails, None] = None

        for feed in self.feeds:
            try:
                new_details = feed.get_stock_details(
                    symbol=symbol,
                )
                if new_details is not None:
                    if details is None:
                        details = new_details
                    else:
                        details = details | new_details
            except Exception as e:
                errors.append(f"Feed {feed.name} failed: {e}")

        if errors:
            logger.warning(
                f"get_stock_details: symbol: {symbol}, errors: {'; '.join(errors)}"
            )

        return details
