# dods/analyze/core/analyzer/utils/numeric_utils.py
"""
Utility functions for numeric feature analysis and quality metrics.
Used by the analyzer to compute robust statistics such as outlier counts,
skewness, and interquartile ranges.
"""

import numpy as np
import pandas as pd
from scipy import stats
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


def compute_basic_stats(series: pd.Series) -> Dict[str, Optional[float]]:
    """
    Compute key numeric statistics: mean, std, min, quartiles, max, variance, IQR, skew.

    Returns
    -------
    dict
        Dictionary of numeric summaries.
    """
    s = series.dropna()
    if s.empty:
        return {}

    q25, median, q75 = np.percentile(s, [25, 50, 75])
    stats_dict = {
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "q25": float(q25),
        "median": float(median),
        "q75": float(q75),
        "max": float(s.max()),
        "variance": float(np.var(s)),
        "iqr": float(q75 - q25),
        "skew": float(stats.skew(s)) if len(s) > 2 else 0.0,
    }

    logger.debug("Computed basic stats for %s", series.name)
    return stats_dict


def detect_outliers(series: pd.Series, iqr: Optional[float] = None) -> Dict[str, Optional[float]]:
    """
    Detect outliers using the 1.5*IQR rule.

    Returns
    -------
    dict with keys:
        - outliers (int)
        - outlier_ratio (float)
        - lower_bound (float)
        - upper_bound (float)
    """
    s = series.dropna()
    if s.empty:
        return {"outliers": 0, "outlier_ratio": 0.0}

    if iqr is None:
        q25, q75 = np.percentile(s, [25, 75])
        iqr = q75 - q25
    else:
        q25, q75 = np.percentile(s, [25, 75])

    lower = q25 - 1.5 * iqr
    upper = q75 + 1.5 * iqr
    mask = (s < lower) | (s > upper)
    outliers = int(mask.sum())
    ratio = float(outliers / len(s) * 100)

    logger.debug(
        "Detected %d outliers in %s (ratio=%.2f%%, bounds=[%.2f, %.2f])",
        outliers, series.name, ratio, lower, upper,
    )

    return {
        "outliers": outliers,
        "outlier_ratio": ratio,
        "lower_bound": float(lower),
        "upper_bound": float(upper),
    }
