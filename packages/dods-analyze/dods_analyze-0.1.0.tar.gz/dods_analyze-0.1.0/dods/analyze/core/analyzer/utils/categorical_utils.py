# dods/analyze/core/analyzer/utils/categorical_utils.py
"""
Utility functions for categorical feature analysis.
Provides metrics like entropy, dominance, and top-k value extraction.
"""

import numpy as np
import pandas as pd
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


def compute_top_values(series: pd.Series, top_n: int = 5) -> Dict[str, int]:
    """
    Return the top-N value counts for a categorical series.

    Parameters
    ----------
    series : pd.Series
        The categorical or string-like column.
    top_n : int
        Maximum number of top categories to return.

    Returns
    -------
    dict
        Mapping of category → count (for top N categories).
    """
    s = series.dropna().astype(str)
    if s.empty:
        return {}
    top = s.value_counts().head(top_n).to_dict()
    logger.debug("Top values for %s: %s", series.name, list(top.keys()))
    return top


def compute_entropy(series: pd.Series) -> Optional[float]:
    """
    Compute Shannon entropy (information measure) of category distribution.

    High entropy → evenly distributed categories.
    Low entropy  → dominated by a few categories.
    """
    s = series.dropna().astype(str)
    if s.empty:
        return None
    counts = s.value_counts(normalize=True)
    entropy = float(-(counts * np.log2(counts)).sum())
    logger.debug("Entropy for %s: %.3f", series.name, entropy)
    return entropy


def compute_dominance(series: pd.Series) -> Optional[float]:
    """
    Compute the dominance ratio (share of most frequent category).
    """
    s = series.dropna().astype(str)
    if s.empty:
        return None
    counts = s.value_counts(normalize=True)
    dominance = float(counts.iloc[0])
    logger.debug("Dominance for %s: %.2f%%", series.name, dominance * 100)
    return dominance


def compute_cardinality(series: pd.Series) -> int:
    """
    Return the number of distinct non-null categories.
    """
    s = series.dropna().astype(str)
    n = int(s.nunique())
    logger.debug("Cardinality for %s: %d", series.name, n)
    return n
