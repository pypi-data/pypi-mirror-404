# dods/analyze/core/analyzer/plot_config/distribution.py
import logging
from dods.analyze.core.analyzer.utils.plot_utils import auto_bins

logger = logging.getLogger(__name__)

def build_distribution_configs(meta, info):
    """
    Build per-feature configuration dictionaries for distribution visualizations.

    Each entry describes *what* to plot (kind, parameters),
    not *how* to plot it (that’s handled later by the renderer).
    """
    configs = {}
    n_rows = info.get("n_rows", 1000)

    for name, fs in meta.items():
        try:
            # === Numeric features ===
            if fs.is_numeric:
                n = fs.n_non_null or n_rows
                bins = auto_bins(n, fs.skew)
                xlim = (fs.min, fs.max) if fs.min is not None and fs.max is not None else None

                configs[name] = {
                    "meta": {
                        "group": "numeric",
                        "kind": "hist",
                        "title": f"{name} distribution",
                    },
                    "params": {
                        "bins": bins,
                        "density": True,
                        "xlim": xlim,
                    },
                }
                logger.debug("Added numeric config for '%s' (bins=%d)", name, bins)

            # === Categorical features ===
            elif fs.is_categorical:
                n_cat = fs.n_categories or 0
                top_n = min(n_cat, 20)
                normalize = n_cat < 30

                configs[name] = {
                    "meta": {
                        "group": "categorical",
                        "kind": "bar",
                        "title": f"{name} frequency",
                    },
                    "params": {
                        "top_n": top_n,
                        "sort": True,
                        "normalize": normalize,
                    },
                }
                logger.debug("Added categorical config for '%s' (n_cat=%d)", name, n_cat)

            # === Datetime features ===
            elif fs.is_datetime:
                if n_rows < 10_000:
                    resample = "D"
                elif n_rows < 100_000:
                    resample = "W"
                else:
                    resample = "M"

                configs[name] = {
                    "meta": {
                        "group": "datetime",
                        "kind": "line",
                        "title": f"{name} over time",
                    },
                    "params": {
                        "resample": resample,
                        "aggregate": "count",
                    },
                }
                logger.debug("Added datetime config for '%s' (resample=%s)", name, resample)

            else:
                logger.info("Skipping column '%s' – unsupported dtype", name)

        except Exception as e:
            logger.exception("Failed to build config for '%s': %s", name, e)

    logger.info("Built %d distribution configs", len(configs))
    return configs
