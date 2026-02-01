# dods/analyze/core/analyzer/relations/classifier.py
import pandas as pd
import logging
from typing import Any, Dict, List

from .config import RelationParams


class RelationClassifier:
    """Classify feature pair relationships based on correlation and MI values.

    Produces qualitative types like:
        - "strong linear"
        - "weak linear"
        - "monotone nonlinear"
        - "complex nonlinear"
        - "independent"

    Also adds flags based on feature distributions (CONST, OUT, SKEW, IDX).
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def classify_pairs(
        self,
        pearson: pd.DataFrame,
        spearman: pd.DataFrame,
        mi: pd.DataFrame,
        distribution: Dict[str, Dict[str, Any]],
        params: RelationParams,
    ) -> List[Dict[str, Any]]:
        """
        Classify all feature pairs based on Pearson, Spearman, and MI matrices.

        Args:
            pearson: Pearson correlation matrix
            spearman: Spearman correlation matrix
            mi: Mutual Information matrix (normalized)
            distribution: Column-level metrics (skew, outlier_ratio, etc.)
            params: RelationParams thresholds

        Returns:
            List of dicts:
            [
                {
                    "a": "feature_1",
                    "b": "feature_2",
                    "pearson": 0.83,
                    "spearman": 0.79,
                    "mi": 0.12,
                    "type": "strong linear",
                    "flags": ["SKEW"]
                },
                ...
            ]
        """
        self.logger.info("Classifying feature pair relationships...")
        feats = pearson.index.tolist() if not pearson.empty else mi.index.tolist()
        pairs: List[Dict[str, Any]] = []

        for i, a in enumerate(feats):
            for b in feats[i + 1 :]:
                r = self._safe_get(pearson, a, b)
                rho = self._safe_get(spearman, a, b)
                mival = self._safe_get(mi, a, b)

                relation_type = self._classify_relation(r, rho, mival, params)
                flags = self._detect_flags(a, b, distribution, params)

                pairs.append(
                    dict(
                        a=a,
                        b=b,
                        pearson=r,
                        spearman=rho,
                        mi=mival,
                        type=relation_type,
                        flags=flags,
                    )
                )

        self.logger.info(f"Classified {len(pairs)} feature pairs.")
        return pairs

    # ==================================================================
    # Internal helpers
    # ==================================================================
    @staticmethod
    def _safe_get(df: pd.DataFrame, a: str, b: str) -> float:
        try:
            return float(df.at[a, b])
        except Exception:
            return float("nan")

    def _classify_relation(
        self, r: float | None, rho: float | None, mi: float | None, p: RelationParams
    ) -> str:
        """Decide qualitative relation type based on thresholds."""
        r_abs = abs(r) if pd.notna(r) else 0.0
        rho_abs = abs(rho) if pd.notna(rho) else 0.0
        mi_val = mi if pd.notna(mi) else 0.0

        if r_abs >= p.classify_linear_strong:
            return "strong linear"
        elif r_abs >= p.classify_linear_weak:
            return "weak linear"
        elif r_abs < p.classify_low_pearson_monotone and rho_abs >= p.classify_spearman_monotone:
            return "monotone nonlinear"
        elif r_abs < p.classify_low_pearson_nonlinear and mi_val > p.classify_mi_complex:
            return "complex nonlinear"
        else:
            return "independent"

    def _detect_flags(
        self, a: str, b: str, distribution: Dict[str, Dict[str, Any]], p: RelationParams
    ) -> List[str]:
        """Detect distribution-based flags for each feature."""
        flags: List[str] = []
        for f in (a, b):
            d = distribution.get(f, {})
            if not d:
                continue
            if d.get("is_index_like"):
                flags.append("IDX")
            if d.get("is_constant"):
                flags.append("CONST")
            if d.get("skew", 0) > p.skew_flag_threshold:
                flags.append("SKEW")
            if d.get("outlier_ratio", 0) > p.outlier_flag_threshold:
                flags.append("OUT")
        return sorted(set(flags))
