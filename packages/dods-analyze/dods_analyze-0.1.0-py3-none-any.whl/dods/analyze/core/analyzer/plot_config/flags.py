# dods/analyze/core/analyzer/plot_config/flags.py
"""
Configuration builder for flag overview plots.
This module visualizes which columns have which data quality issues.
"""

import logging
from typing import Dict, Any
from dods.analyze.core.feature_stats import FeatureStats

logger = logging.getLogger(__name__)


def build_flag_configs(meta: Dict[str, FeatureStats]) -> Dict[str, Any]:
    """
    Build configurations for displaying flag summary per feature.

    Typically visualized as bar charts showing number of flags per feature.
    """
    configs = {}
    logger.info("Building flag overview configs.")

    for name, fs in meta.items():
        if not fs.flag:
            continue

        configs[name] = {
            "meta": {
                "group": "flags",
                "kind": "barh",
                "title": f"{name} - Data quality flags",
            },
            "params": {
                "flags": fs.flag,
                "n_flags": len(fs.flag),
            },
        }

    logger.info("Built %d flag configs.", len(configs))
    return configs
