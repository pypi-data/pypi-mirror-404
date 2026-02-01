from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from typing import Optional, List, Union, Literal

import pandas as pd

from tigeropen.common.consts import (
    Language,
    BarPeriod,
    QuoteRight,
    Market,
)
from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.quote.quote_client import QuoteClient

from .feed import AdjustType, BaseFeed, StockMarket
from ..core import OHLCVData, StockDetails, normalize_ohlcv
from ..logger import logger


@dataclass
class TigerConfig:
    private_key: str
    tiger_id: str
    account: str
    license: str
    secret_key: Optional[str] = None
    language: Language = Language.en_US
    timezone: str = "US/Eastern"


@lru_cache(maxsize=1, typed=True)
def get_tiger_client(
    private_key: str,
    tiger_id: str,
    account: str,
    license: str,
    secret_key: Optional[str] = None,
    language: Language = Language.en_US,
    timezone: str = "US/Eastern",
) -> QuoteClient:
    tiger_config = TigerOpenClientConfig()
    tiger_config.private_key = private_key
    tiger_config.tiger_id = tiger_id
    tiger_config.account = account
    tiger_config.license = license
    tiger_config.secret_key = secret_key
    tiger_config.language = language
    tiger_config.timezone = timezone
    return QuoteClient(tiger_config)


@dataclass
class TigerFeed(BaseFeed):
    """Data feed backed by Tiger Brokers."""

    config: Optional[TigerConfig] = field(default=None)

    name: str = "Tiger"

    tiger_client: QuoteClient = field(init=False)

    rename_map = {
        "time": "date",
    }

    adjust_map = {
        "none": QuoteRight.NR,
        "forward": None,
        "backward": QuoteRight.BR,
    }

    def __post_init__(self):
        if self.config is None:
            raise ValueError("TigerConfig must be provided for TigerFeed.")
        self.tiger_client = get_tiger_client(
            self.config.private_key,
            self.config.tiger_id,
            self.config.account,
            self.config.license,
            self.config.secret_key,
            self.config.language,
            self.config.timezone,
        )
        logger.debug("TigerFeed initialized.")

    @classmethod
    def markets(cls) -> Union[List[StockMarket], Literal["*"]]:
        return "*"

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
            f"Tiger: fetching {symbol} from {start_str} to {end_str} with adjust={adjust}"
        )

        bars = self.tiger_client.get_bars(
            symbols=code,
            period=BarPeriod.DAY,
            begin_time=start_str,
            end_time=end_str,
            right=self.adjust_map[adjust],
        )

        df = bars.rename(columns=self.rename_map)
        df["date"] = pd.to_datetime(df["date"], unit="ms")

        if df["next_page_token"].notnull().any():
            logger.warning(
                f"Data for {symbol} from Tiger has more pages. Only the first page is fetched."
            )

        return normalize_ohlcv(pd.DataFrame(df), fields=fields)

    def get_stock_details(self, symbol: str) -> Union[StockDetails, None]:
        try:
            code, market = self.check_symbol(symbol)
        except Exception:
            return None

        if market in [StockMarket.US, StockMarket.UNKNOWN]:
            return None

        lang = "zh_CN"

        logger.debug(f"Tiger: fetching stock details for {symbol}")

        details = self.tiger_client.get_stock_details([code], lang=lang)

        if details is None:
            return None

        dict_details = details.to_dict(orient="records")[0]

        listing_date = dict_details.get("listing_date")
        if listing_date is not None:
            listing_date = date.fromtimestamp(listing_date / 1000.0)

        stock_industries = self.tiger_client.get_stock_industry(
            code, market=Market.CN if market != StockMarket.HK else Market.HK
        )

        tags = (
            []
            if stock_industries is None
            else [ind.get("name_cn") for ind in stock_industries]
            + [ind.get("name_en") for ind in stock_industries]
        )

        tags = list(set([tag.strip() for tag in tags if tag]))

        return StockDetails(
            symbol=code,
            name=dict_details.get("name", ""),
            market="HK" if market == StockMarket.HK else "CN",
            exchange="SSE"
            if market in [StockMarket.SH, StockMarket.ETF_SH, StockMarket.KCB]
            else (
                "SZSE"
                if market in [StockMarket.SZ, StockMarket.ETF_SZ]
                else ("HKEX" if market == StockMarket.HK else None)
            ),
            listing_date=listing_date,
            total_shares=dict_details.get("shares"),
            float_shares=dict_details.get("float_shares"),
            is_etf=dict_details.get("etf", 0) != 0,
            tags=tags,
        )
