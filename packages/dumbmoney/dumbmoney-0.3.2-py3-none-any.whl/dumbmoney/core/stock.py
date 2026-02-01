from datetime import date
from pydantic import BaseModel, Field
from typing import Literal, List, Optional


class StockDetails(BaseModel):
    symbol: str = Field(..., description="The stock ticker symbol")
    name: str = Field(..., description="The stock name")
    market: Literal["CN", "HK", "US"] = Field(..., description="The stock market")
    exchange: Optional[Literal["NYSE", "NASDAQ", "HKEX", "SSE", "SZSE"]] = Field(
        None, description="The stock exchange"
    )
    listing_date: Optional[date] = Field(
        None, description="The date when the stock was listed"
    )
    total_shares: Optional[int] = Field(
        None, description="Total number of shares outstanding"
    )
    float_shares: Optional[int] = Field(
        None, description="Number of shares available for trading"
    )
    is_etf: bool = Field(..., description="Indicates if the stock is an ETF")
    tags: List[str] = Field(
        default_factory=list, description="List of tags associated with the stock"
    )

    def merge(self, other: "StockDetails") -> "StockDetails":
        """
        Merge two StockDetails objects, preferring non-null values from self.
        """
        return StockDetails(
            symbol=self.symbol or other.symbol,
            name=self.name or other.name,
            market=self.market or other.market,
            exchange=self.exchange or other.exchange,
            listing_date=self.listing_date or other.listing_date,
            total_shares=self.total_shares or other.total_shares,
            float_shares=self.float_shares or other.float_shares,
            is_etf=self.is_etf if self.is_etf is not None else other.is_etf,
            tags=list(set(self.tags + other.tags)),
        )

    def __or__(self, other: "StockDetails") -> "StockDetails":
        return self.merge(other)
