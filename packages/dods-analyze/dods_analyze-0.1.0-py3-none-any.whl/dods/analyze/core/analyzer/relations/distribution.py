# distribution.py
import numpy as np
import pandas as pd
import logging
from scipy.stats import skew
from typing import Any, Dict

from .config import RelationParams


class DistributionCalculator:
    """Compute descriptive statistics for numeric features (skewness, outliers, uniqueness, etc.)."""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def compute(self, df: pd.DataFrame, params: RelationParams) -> Dict[str, Dict[str, Any]]:
        """
        Compute distribution metrics for each numeric column.

        Args:
            df: Input DataFrame (may contain numeric and non-numeric columns)
            params: RelationParams dataclass with thresholds (e.g. IQR factor)

        Returns:
            A mapping from column name to metrics dict, e.g.:
            {
                "col1": {
                    "skew": 0.12,
                    "outlier_ratio": 0.03,
                    "nunique": 120,
                    "is_index_like": False,
                    "is_constant": False
                },
                ...
            }
        """
        self.logger.info("Calculating column distributions...")

        df_num = df.select_dtypes(include="number")
        if df_num.empty:
            self.logger.warning("No numeric columns found for distribution analysis.")
            return {}

        out: Dict[str, Dict[str, Any]] = {}
        n = len(df_num)

        for col in df_num.columns:
            vals = df_num[col].dropna().to_numpy()
            if len(vals) < 3:
                continue

            q1, q3 = np.percentile(vals, [25, 75])
            iqr = q3 - q1
            factor = params.outlier_iqr_factor
            lower, upper = q1 - factor * iqr, q3 + factor * iqr

            outlier_ratio = float(np.mean((vals < lower) | (vals > upper)))
            nunique = int(len(np.unique(vals)))
            unique_ratio = nunique / n if n else 0.0

            # Heuristic: detect index-like columns (almost unique, monotonic, dense range)
            diffs = np.diff(vals)
            is_monotonic_seq = bool(np.all(diffs >= 0) or np.all(diffs <= 0))
            vmin, vmax = np.min(vals), np.max(vals)
            span = (vmax - vmin) if vmax != vmin else 1.0
            range_density = nunique / span
            is_index_like = bool(unique_ratio > 0.9 and is_monotonic_seq and range_density > 0.5)

            out[col] = {
                "skew": float(skew(vals)),
                "outlier_ratio": outlier_ratio,
                "nunique": nunique,
                "is_index_like": is_index_like,
                "is_constant": bool(nunique == 1),
            }

        self.logger.info("Distribution metrics computed successfully.")
        return out
