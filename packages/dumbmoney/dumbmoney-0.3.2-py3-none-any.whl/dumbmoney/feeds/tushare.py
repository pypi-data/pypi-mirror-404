from dataclasses import dataclass, field
from datetime import date, datetime
from functools import lru_cache
from typing import List, Optional, Literal, Union

import os
import pandas as pd

from .feed import AdjustType, BaseFeed, StockMarket
from ..core import OHLCVData, StockDetails, normalize_ohlcv
from ..logger import logger

import tushare as ts
from tushare.pro.client import DataApi


@lru_cache(maxsize=1, typed=True)
def get_tushare_pro(api_token: Optional[str] = None) -> DataApi:
    if not api_token:
        raise ValueError(
            "TUSHARE_TOKEN is not found. Set it either in environment variable or pass it explicitly."
        )
    ts.set_token(api_token)
    return ts.pro_api()


@dataclass
class TushareFeed(BaseFeed):
    """Data feed backed by Tushare."""

    name: str = "Tushare"

    api_token: Optional[str] = field(default_factory=lambda: os.getenv("TUSHARE_TOKEN"))
    pro: DataApi = field(init=False)

    rename_map = {
        "trade_date": "date",
        "vol": "volume",
    }

    adjust_map = {
        "none": "",
        "forward": "qfq",
        "backward": "hfq",
    }

    def __post_init__(self):
        self.pro = get_tushare_pro(self.api_token)
        logger.debug("TushareFeed initialized.")

    @classmethod
    def markets(cls) -> Union[List[StockMarket], Literal["*"]]:
        return [
            StockMarket.SH,
            StockMarket.SZ,
            StockMarket.KCB,
            StockMarket.HK,
            StockMarket.ETF_SH,
            StockMarket.ETF_SZ,
        ]

    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        adjust: AdjustType = "forward",
        fields: Optional[List[str]] = None,
    ) -> OHLCVData:
        code, market = self.check_symbol(symbol)

        start_str = start.strftime("%Y%m%d")
        end_str = end.strftime("%Y%m%d")

        logger.debug(
            f"Tushare: fetching {symbol} from {start_str} to {end_str} with adjust={adjust}"
        )

        if market in [StockMarket.SH, StockMarket.SZ, StockMarket.KCB]:
            df = ts.pro_bar(
                ts_code=f"{code}.{market.value.split('_')[-1]}",
                adj=self.adjust_map[adjust],
                start_date=start_str,
                end_date=end_str,
            )
        elif market == StockMarket.HK:
            # Only forward adjusted data is supported in Tushare for HK stocks
            df = self.pro.hk_daily_adj(
                ts_code=f"{code}.HK",
                start_date=start_str,
                end_date=end_str,
            )
        elif market in [StockMarket.ETF_SH, StockMarket.ETF_SZ]:
            df = self.pro.fund_daily(
                ts_code=f"{code}.{market.value.split('_')[-1]}",
                start_date=start_str,
                end_date=end_str,
            )

        df = df.rename(columns=self.rename_map)
        df["date"] = pd.to_datetime(df["date"])

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

        if market in [StockMarket.HK, StockMarket.US, StockMarket.UNKNOWN]:
            return None

        logger.debug(f"Tushare: fetching stock details for {symbol}")

        df = None

        if market in [StockMarket.SH, StockMarket.SZ, StockMarket.KCB]:
            df = self.pro.stock_basic(
                ts_code=f"{code}.{market.value.split('_')[-1]}",
                fields="name,industry,exchange,list_date",
            )

        if df is None or df.empty:
            return None

        listing_date = (
            datetime.strptime(df.iloc[0]["list_date"], "%Y%m%d").date()
            if "list_date" in df.columns and pd.notna(df.iloc[0]["list_date"])
            else None
        )

        return StockDetails(
            symbol=code,
            name=df.iloc[0]["name"],
            market="CN",
            exchange=df.iloc[0]["exchange"],
            listing_date=listing_date,
            total_shares=None,
            float_shares=None,
            is_etf=False,
            tags=[df.iloc[0]["industry"].strip()]
            if pd.notna(df.iloc[0]["industry"])
            else [],
        )
