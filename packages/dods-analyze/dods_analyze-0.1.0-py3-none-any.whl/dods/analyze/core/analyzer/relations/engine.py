# dods/analyze/core/analyzer/relations/engine.py
"""
RelationEngine v4 — modular, testable, production-ready.

Pipeline overview:
    1️⃣ Distribution analysis (numeric)
    2️⃣ Correlation (Pearson & Spearman)
    3️⃣ Mutual Information (hybrid num–cat)
    4️⃣ Grouping (Pearson + MI)
    5️⃣ Classification (pair types + flags)
    6️⃣ Summary & isolation detection
"""

from __future__ import annotations
import pandas as pd
import numpy as np
import logging
from typing import Any, Dict, List

from .config import RelationParams
from .distribution import DistributionCalculator
from .correlation import CorrelationCalculator
from .mutual_info_calculator import MutualInfoCalculator
from .grouping import GroupingCalculator
from .classifier import RelationClassifier


class RelationEngine:
    """Main orchestration layer for feature relationship analysis."""

    def __init__(self, params: RelationParams | None = None, logger: logging.Logger | None = None):
        self.params = params or RelationParams()
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        self.results: Dict[str, Any] = {}
        self.summary: Dict[str, Any] = {}
        self.isolated: List[str] = []

        # Subcomponents
        self._distribution = DistributionCalculator(self.logger)
        self._correlation = CorrelationCalculator(self.logger)
        self._mi = MutualInfoCalculator(self.logger)
        self._grouping = GroupingCalculator(self.logger)
        self._classifier = RelationClassifier(self.logger)

    # ==================================================================
    # Public API
    # ==================================================================
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run the full relationship analysis pipeline."""
        self.logger.info("🚀 Starting feature relation analysis...")

        if df.empty:
            self.logger.warning("Empty DataFrame provided.")
            return {}

        all_features = df.columns
        df_num = df.select_dtypes(include="number")

        # 1️⃣ Distribution (numeric only)
        self.logger.info("Step 1/6: Distribution analysis")
        self.distribution = self._distribution.compute(df, self.params)

        # 2️⃣ Correlation matrices
        self.logger.info("Step 2/6: Correlation (Pearson & Spearman)")
        corr = self._correlation.compute(df, self.params)
        pearson, spearman = corr["pearson"], corr["spearman"]

        # 3️⃣ Hybrid Mutual Information
        self.logger.info("Step 3/6: Mutual Information (hybrid)")
        mi = self._mi.compute(df, self.params)

        # 4️⃣ Grouping (Pearson & MI)
        self.logger.info("Step 4/6: Grouping (Pearson & MI)")
        self.groups = {
            "pearson": self._grouping.compute(pearson, self.params),
            "mi": self._grouping.compute(mi, self.params),
        }

        # 5️⃣ Classification
        self.logger.info("Step 5/6: Pair classification")
        self.pairs = self._classifier.classify_pairs(
            pearson=pearson,
            spearman=spearman,
            mi=mi,
            distribution=self.distribution,
            params=self.params,
        )

        # 6️⃣ Summary & isolated features
        self.logger.info("Step 6/6: Summary & isolation detection")
        self.isolated = self._find_isolated(pearson)
        self.summary = self._build_summary(pearson)

        # Bundle all results
        self.results = {
            "pearson": pearson,
            "spearman": spearman,
            "mi": mi,
            "distribution": self.distribution,
            "pairs": self.pairs,
            "groups": self.groups,
            "isolated": self.isolated,
            "summary": self.summary,
        }

        self.logger.info("✅ Relation analysis completed successfully.")
        return self.results

    # ==================================================================
    # Helpers
    # ==================================================================
    def _find_isolated(self, pearson: pd.DataFrame) -> List[str]:
        """Return features with no correlation above iso_threshold."""
        iso: List[str] = []
        if pearson is None or pearson.empty:
            return iso

        for col in pearson.columns:
            col_series = pearson[col].abs().drop(labels=[col], errors="ignore")
            max_abs = col_series.max() if not col_series.empty else 0.0
            if pd.isna(max_abs) or max_abs < self.params.iso_threshold:
                iso.append(col)
        return iso

    def _build_summary(self, pearson: pd.DataFrame) -> Dict[str, Any]:
        """Compute global summary statistics."""
        if pearson is None or pearson.empty:
            return {
                "n_features": 0,
                "n_groups": 0,
                "n_isolated": len(self.isolated),
                "avg_abs_corr": 0.0,
                "strong_rel_density": 0.0,
            }

        abs_corr = pearson.abs()
        tri = abs_corr.where(np.triu(np.ones(abs_corr.shape), 1).astype(bool))
        vals = tri.stack()
        avg_abs_corr = float(vals.mean()) if not vals.empty else 0.0
        strong_density = float((vals > self.params.pearson_threshold).mean()) if not vals.empty else 0.0

        n_features_valid = int((~pearson.isna().all()).sum())
        n_features_total = pearson.shape[1]

        return {
            "n_features": n_features_valid,        # legacy alias
            "n_features_total": n_features_total,  # all numeric features
            "n_features_valid": n_features_valid,  # valid correlation features
            "n_groups_pearson": len(self.groups.get("pearson", [])),
            "n_groups_mi": len(self.groups.get("mi", [])),
            "n_isolated": len(self.isolated),
            "avg_abs_corr": avg_abs_corr,
            "strong_rel_density": strong_density,
        }