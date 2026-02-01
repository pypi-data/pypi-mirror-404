# dods/analyze/core/analyzer/utils/plot_utils.py
"""
Utility helpers for adaptive plot configuration.

These functions are *pure helpers* that make automatic decisions
based on data characteristics — they do **not** render or style plots.
"""

import numpy as np
from typing import Optional, Tuple, Sequence
import logging

logger = logging.getLogger(__name__)


# === Histogram bin calculation ===
def auto_bins(n: int, skew: Optional[float] = None) -> int:
    """
    Determine an appropriate number of histogram bins.

    Parameters
    ----------
    n : int
        Number of valid (non-null) samples in the feature.
    skew : float, optional
        Estimated skewness of the distribution. Used to adjust bin count.

    Returns
    -------
    int
        Number of bins, clipped to a reasonable range (10–60).
    """
    if n <= 0:
        return 10

    base = np.sqrt(n)
    if skew is not None and abs(skew) > 1:
        base *= 0.8  # fewer bins for highly skewed data

    bins = int(np.clip(base, 10, 60))
    logger.debug("auto_bins: n=%d, skew=%.2f -> bins=%d", n, skew or 0, bins)
    return bins


# === Range & clipping ===
def compute_xrange(values: Sequence[float], margin: float = 0.05) -> Optional[Tuple[float, float]]:
    """
    Compute a padded x-range for numeric plots.

    Example:
        compute_xrange([10, 20]) → (9.5, 20.5)

    Parameters
    ----------
    values : sequence of floats
        Data values or summary bounds (e.g. min/max).
    margin : float, default=0.05
        Fractional padding to add on both sides.

    Returns
    -------
    (float, float) or None
        Padded lower and upper limits, or None if not computable.
    """
    if not values or len(values) < 2:
        return None

    vmin, vmax = float(min(values)), float(max(values))
    span = vmax - vmin
    if span == 0:
        return (vmin - 1, vmax + 1)

    pad = span * margin
    return (vmin - pad, vmax + pad)


# === Normalization helper ===
def normalize_counts(counts: Sequence[int]) -> np.ndarray:
    """
    Convert absolute counts to relative frequencies (sum to 1).

    Useful for categorical plots with limited cardinality.
    """
    arr = np.array(counts, dtype=float)
    total = arr.sum()
    if total == 0:
        return arr
    normalized = arr / total
    return normalized


# === Color palette generator (basic placeholder) ===
def default_palette(n: int) -> list[str]:
    """
    Return a list of n visually distinct colors (simple fallback).
    """
    base_colors = [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
        "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ab"
    ]
    if n <= len(base_colors):
        return base_colors[:n]
    # repeat and truncate for simplicity
    return (base_colors * ((n // len(base_colors)) + 1))[:n]
