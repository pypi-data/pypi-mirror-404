from typing import List, Optional

import pandas as pd


_REQUIRED_COLS = ("open", "high", "low", "close", "volume")


class OHLCVData(pd.DataFrame):
    """
    Wrapper around pd.DataFrame to represent OHLCV data.
    Ensures required columns are present and a DatetimeIndex is used.
    """

    # this is just for type readability - no extra functionality
    pass


def normalize_ohlcv(
    data: pd.DataFrame, fields: Optional[List[str]] = None
) -> OHLCVData:
    """
    Ensure DataFrame has required OHLC columns and a DatetimeIndex.

    Args:
      data: pd.DataFrame containing OHLCV data.
      fields: Optional list of fields to include. If None, include all.
    """
    df = data.copy()
    df.columns = [col.lower() for col in df.columns]

    # Ensure required columns are present
    missing_cols = [col for col in _REQUIRED_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"DataFrame is missing required columns: {missing_cols}")

    # Promote 'date' column to index if present
    if not isinstance(df.index, pd.DatetimeIndex):
        for col in df.columns:
            if col.lower() in ("date", "datetime", "trade_date"):
                df[col] = pd.to_datetime(df[col])
                df = df.set_index(col)
                break

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(
            "DataFrame must have a DatetimeIndex or a 'date'/'datetime'/'trade_date' column."
        )

    df = df.sort_index()

    # Enforce column order
    cols = [col for col in _REQUIRED_COLS if col in df.columns]
    other_cols = [col for col in df.columns if col not in cols]
    if fields is not None:
        other_cols = [col for col in other_cols if col in fields]
    df = df[cols + other_cols]

    return pd.DataFrame(df)  # type: ignore
