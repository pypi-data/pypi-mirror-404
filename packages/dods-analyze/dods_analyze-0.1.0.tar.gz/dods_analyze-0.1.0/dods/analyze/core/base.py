# dods/analyze/core/base.py
"""
Minimal base class providing logging and threshold definitions.
Used by all analyzers (e.g., DataAnalyzer, TargetAnalyzer).
"""

import logging
from typing import Any, Dict


class AnalyzerBase:
    """Generic foundation for analyzers (no data logic, only config)."""

    def __init__(self) -> None:
        # --- Logger setup ---
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
                "%H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        self.thresholds_by_type = {
            "numeric": {
                "missing_pct":   ("high",  [(95.0, 1), (80.0, 2)]),   # je höher, desto schlechter → "low" = gut ist hoch
                "outlier_ratio": ("high", [(1.0, 1), (5.0, 2)]),
                "skew":          ("abs",  [(1.0, 1), (3.0, 2)]),
                "cv":            ("abs",  [(0.5, 1), (1.0, 2)]),
                "cv_robust":     ("abs",  [(0.5, 1), (1.0, 2)]),
                "unique_pct":    ("low", [(50.0, 1), (10.0, 2)]),
            },
            "categorical": {
                "missing_pct":   ("high", [(5.0, 1), (20.0, 2)]),     # hier klassisch: viel Missing = schlecht
                "dominance":     ("high", [(0.60, 1), (0.90, 2)]),
                "entropy":       ("low",  [(2.0, 1), (1.0, 2)]),
                "unique_pct":    ("high", [(95.0, 1), (99.0, 2)]),
            },
            "datetime": {
                "missing_pct":   ("high", [(5.0, 1), (20.0, 2)]),
            },
        }
