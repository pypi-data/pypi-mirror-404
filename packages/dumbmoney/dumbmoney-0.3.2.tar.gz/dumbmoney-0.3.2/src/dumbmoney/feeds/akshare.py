from dataclasses import dataclass
from datetime import date
from typing import List, Literal, Union, Optional

import pandas as pd

from dumbmoney.core import StockDetails

from .feed import AdjustType, BaseFeed, StockMarket
from ..core import OHLCVData, normalize_ohlcv
from ..logger import logger

import akshare as ak


@dataclass
class AkshareFeed(BaseFeed):
    """Data feed backed by Akshare."""

    name: str = "Akshare"

    rename_map = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
    }

    adjust_map = {
        "none": "",
        "forward": "qfq",
        "backward": "hfq",
    }

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
        code, market = self.check_symbol(symbol)

        start_str = start.strftime("%Y%m%d")
        end_str = end.strftime("%Y%m%d")

        logger.debug(
            f"Akshare: fetching {symbol} from {start_str} to {end_str} with adjust={adjust}"
        )

        if market in [StockMarket.SH, StockMarket.SZ]:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust=self.adjust_map[adjust],
            )
        elif market == StockMarket.HK:
            df = ak.stock_hk_hist(
                symbol=code,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust=self.adjust_map[adjust],
            )
        elif market == StockMarket.KCB:
            df = ak.stock_zh_kcb_daily(
                symbol=f"sh{code}",
                adjust=self.adjust_map[adjust],
            )
        elif market in [StockMarket.ETF_SH, StockMarket.ETF_SZ]:
            df = ak.fund_etf_hist_em(
                symbol=code,
                start_date=start_str,
                end_date=end_str,
                adjust=self.adjust_map[adjust],
            )
        elif market == StockMarket.US:
            df = ak.stock_us_hist(
                symbol=code,
                period="daily",
                start_date=start_str,
                end_date=end_str,
                adjust=self.adjust_map[adjust],
            )

        df = df.rename(columns=self.rename_map)
        df["date"] = pd.to_datetime(df["date"])

        # filter df by date range
        df = df[
            (df["date"] >= pd.to_datetime(start)) & (df["date"] <= pd.to_datetime(end))
        ]

        return normalize_ohlcv(pd.DataFrame(df), fields=fields)

    def get_stock_details(self, symbol: str) -> Union[StockDetails, None]:
        # Not implemented yet
        return None
