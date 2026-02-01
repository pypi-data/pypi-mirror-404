# dods/analyze/core/analyzer/plot_config/outliers.py
"""
Configuration builder for outlier visualization.

Outlier plots are typically relevant only for numeric features.
This config defines which features to plot and what parameters to use.
"""

import logging
from typing import Dict, Any
from dods.analyze.core.feature_stats import FeatureStats

logger = logging.getLogger(__name__)


def build_outlier_configs(meta: Dict[str, FeatureStats]) -> Dict[str, Any]:
    """
    Build per-feature plot configuration for outlier analysis.

    Parameters
    ----------
    meta : dict[str, FeatureStats]
        Mapping of feature name → FeatureStats.

    Returns
    -------
    dict[str, Any]
        Mapping of feature name → outlier plot config.
    """
    configs = {}
    logger.info("Building outlier plot configs for numeric features.")

    for name, fs in meta.items():
        if not fs.is_numeric:
            continue
        if fs.outliers is None or fs.outliers == 0:
            continue

        # Limit whisker range to 1.5 * IQR as conventional rule
        configs[name] = {
            "meta": {
                "group": "numeric",
                "kind": "box",
                "title": f"{name} - Outlier distribution",
            },
            "params": {
                "whis": 1.5,
                "showfliers": True,
                "notch": True,
            },
        }

    logger.info("Built %d outlier configs.", len(configs))
    return configs
