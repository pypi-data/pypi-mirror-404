import logging
from typing import Dict, Any
from ..feature_stats import FeatureStats


class ThresholdEngine:
    """
    Applies type-specific threshold rules to all FeatureStats in meta.
    Each threshold defines (compare_mode, [(bound, level), ...]).
    """

    def __init__(self, thresholds_by_type: Dict[str, Dict[str, tuple[str, list[tuple[float, int]]]]]):
        """
        Example:
            self.thresholds_by_type = {
                "numeric": {
                    "missing_pct": ("low", [(95.0, 1), (80.0, 2)]),
                    "skew": ("abs", [(1.0, 1), (3.0, 2)]),
                },
                "categorical": {
                    "missing_pct": ("high", [(5.0, 1), (20.0, 2)]),
                    "dominance": ("high", [(0.6, 1), (0.9, 2)]),
                },
            }
        """
        self.thresholds_by_type = thresholds_by_type
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            fmt = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
            handler.setFormatter(logging.Formatter(fmt, "%H:%M:%S"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    # ----------------------------------------------------------------------
    # Main entry points
    # ----------------------------------------------------------------------
    def apply_to_meta(self, meta: Dict[str, FeatureStats]) -> None:
        """Applies thresholds to all FeatureStats in meta."""
        self.logger.info(f"Applying thresholds to {len(meta)} features...")
        for fs in meta.values():
            self.apply_to_feature(fs)
        self.logger.info("Threshold evaluation completed.")

    def apply_to_feature(self, fs: FeatureStats) -> None:
        """Evaluates thresholds for one feature, type-specific."""
        fs.flag = {}

        # --- Select type-specific threshold set ---
        if fs.is_numeric:
            thresholds = self.thresholds_by_type.get("numeric", {})
            type_label = "numeric"
        elif fs.is_categorical:
            thresholds = self.thresholds_by_type.get("categorical", {})
            type_label = "categorical"
        elif fs.is_datetime:
            thresholds = self.thresholds_by_type.get("datetime", {})
            type_label = "datetime"
        else:
            thresholds = {}
            type_label = "unknown"

        if not thresholds:
            self.logger.debug(f"{fs.name}: no thresholds defined for type '{type_label}'")
            return

        # --- Apply all thresholds relevant for this type ---
        for key, params in thresholds.items():
            try:
                compare, levels = params[:2]  # allow flexible tuples
            except Exception:
                self.logger.warning(f"Invalid threshold format for '{key}': {params}")
                continue

            value = getattr(fs, key, None)
            if value is None:
                continue

            level = self._evaluate(value, compare, levels)
            if level > 0:
                fs.flag[key] = level
                self.logger.debug(
                    f"{fs.name:<25} | {key:<15} = {value:>10.3f} → level {level}"
                )

        if not fs.flag:
            self.logger.debug(f"{fs.name}: no flags triggered ({type_label})")

    # ----------------------------------------------------------------------
    # Core logic
    # ----------------------------------------------------------------------
    def _evaluate(self, value: float, compare: str, levels: list[tuple[float, int]]) -> int:
        """Evaluates value against ordered bounds and returns intensity level."""
        triggered = 0
        for bound, level in levels:
            if self._check_condition(value, bound, compare):
                triggered = max(triggered, level)
        return triggered

    @staticmethod
    def _check_condition(value: float, bound: float, compare: str) -> bool:
        """Helper for condition check."""
        if compare == "high":
            return value >= bound
        elif compare == "low":
            return value <= bound
        elif compare == "abs":
            return abs(value) >= bound
        else:
            raise ValueError(f"Invalid compare mode: {compare}")
