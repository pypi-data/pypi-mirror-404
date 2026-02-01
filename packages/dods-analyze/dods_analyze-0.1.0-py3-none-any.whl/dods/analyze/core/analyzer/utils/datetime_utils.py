# dods/analyze/core/analyzer/utils/datetime_utils.py
"""
Helper functions for analyzing and configuring datetime features.
These utilities provide automatic heuristics for time-based visualizations.
"""

import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# === Determine resampling frequency ===
def suggest_resample_freq(series: pd.Series, n_rows: Optional[int] = None) -> str:
    """
    Suggest an appropriate resampling frequency for a datetime series.

    Logic:
    - < 10k rows → daily ("D")
    - < 100k rows → weekly ("W")
    - < 1M rows → monthly ("M")
    - >= 1M → quarterly ("Q")

    Parameters
    ----------
    series : pd.Series
        Datetime-like column (dtype datetime64).
    n_rows : int, optional
        Number of rows in the dataset (used as hint).

    Returns
    -------
    str
        Resampling frequency string (e.g. "D", "W", "M", "Q").
    """
    n = n_rows or len(series)
    if n < 10_000:
        freq = "D"
    elif n < 100_000:
        freq = "W"
    elif n < 1_000_000:
        freq = "M"
    else:
        freq = "Q"

    logger.debug("suggest_resample_freq: n=%d -> %s", n, freq)
    return freq


# === Compute date range and span ===
def compute_date_range(series: pd.Series) -> Optional[tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Compute the min and max timestamp of a datetime series.
    Returns None if the series is empty or invalid.
    """
    if series.empty or not pd.api.types.is_datetime64_any_dtype(series):
        return None
    s = series.dropna()
    if s.empty:
        return None

    start, end = s.min(), s.max()
    logger.debug("compute_date_range: %s -> %s", start, end)
    return start, end


# === Detect if a feature contains future dates ===
def contains_future_dates(series: pd.Series) -> bool:
    """
    Check whether the series contains dates in the future (relative to now).
    """
    if not pd.api.types.is_datetime64_any_dtype(series):
        return False
    now = pd.Timestamp.now()
    s = series.dropna()
    if s.empty:
        return False

    future = (s > now).any()
    logger.debug("contains_future_dates: future_found=%s", future)
    return bool(future)
