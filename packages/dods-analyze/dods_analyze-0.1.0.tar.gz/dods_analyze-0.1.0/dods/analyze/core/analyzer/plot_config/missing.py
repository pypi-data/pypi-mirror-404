# dods/analyze/core/analyzer/plot_config/missing.py
"""
Configuration builder for missing value visualization.
Creates simple heatmaps or bar plots for missingness by feature.
"""

import logging
from typing import Dict, Any
from dods.analyze.core.feature_stats import FeatureStats

logger = logging.getLogger(__name__)


def build_missing_configs(meta: Dict[str, FeatureStats]) -> Dict[str, Any]:
    """
    Build per-feature configuration for missing value plots.

    Parameters
    ----------
    meta : dict[str, FeatureStats]

    Returns
    -------
    dict[str, Any]
    """
    configs = {}
    logger.info("Building missing value plot configs.")

    for name, fs in meta.items():
        if fs.missing_pct <= 0:
            continue

        kind = "bar" if fs.missing_pct < 50 else "heatmap"

        configs[name] = {
            "meta": {
                "group": "missing",
                "kind": kind,
                "title": f"{name} - Missing pattern",
            },
            "params": {
                "missing_pct": fs.missing_pct,
                "threshold": 20,
            },
        }

    logger.info("Built %d missing configs.", len(configs))
    return configs
