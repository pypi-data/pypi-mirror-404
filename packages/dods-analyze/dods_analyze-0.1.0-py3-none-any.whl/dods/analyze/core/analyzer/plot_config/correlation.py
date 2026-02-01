# dods/analyze/core/analyzer/plot_config/correlation.py
"""
Configuration builder for correlation visualizations.

This module defines what correlation plots should be generated:
- Heatmaps for numeric–numeric relationships
- Cramér’s V or Theil’s U for categorical–categorical
- Point-biserial or ANOVA-style comparisons for mixed types
"""

import logging
from typing import Dict, Any
import pandas as pd
from dods.analyze.core.feature_stats import FeatureStats

logger = logging.getLogger(__name__)


def build_correlation_configs(meta: Dict[str, FeatureStats], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build configuration for correlation analysis plots.

    Parameters
    ----------
    meta : dict[str, FeatureStats]
        Mapping of feature name → FeatureStats object
    df : pandas.DataFrame
        Full dataset (needed to compute correlations later)

    Returns
    -------
    dict[str, Any]
        Plot configuration for correlation-related visuals.
    """
    configs = {}
    logger.info("Building correlation plot configs.")

    # --- Separate numeric and categorical columns
    num_cols = [n for n, fs in meta.items() if fs.is_numeric]
    cat_cols = [n for n, fs in meta.items() if fs.is_categorical]

    if len(num_cols) >= 2:
        configs["numeric_corr"] = {
            "meta": {
                "group": "correlation",
                "kind": "heatmap",
                "title": "Numeric feature correlation matrix",
            },
            "params": {
                "method": "pearson",
                "columns": num_cols,
                "vmin": -1.0,
                "vmax": 1.0,
                "annot": False,
            },
        }

    if len(cat_cols) >= 2:
        configs["categorical_corr"] = {
            "meta": {
                "group": "correlation",
                "kind": "heatmap",
                "title": "Categorical association matrix (Cramér's V)",
            },
            "params": {
                "method": "cramers_v",
                "columns": cat_cols,
                "vmin": 0.0,
                "vmax": 1.0,
                "annot": False,
            },
        }

    if len(num_cols) >= 1 and len(cat_cols) >= 1:
        configs["mixed_corr"] = {
            "meta": {
                "group": "correlation",
                "kind": "heatmap",
                "title": "Mixed correlation (numeric ↔ categorical)",
            },
            "params": {
                "method": "anova_f",
                "num_cols": num_cols,
                "cat_cols": cat_cols,
                "vmin": 0.0,
                "vmax": 1.0,
                "annot": False,
            },
        }

    logger.info("Built %d correlation configs.", len(configs))
    return configs
