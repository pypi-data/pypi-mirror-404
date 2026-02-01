# dods/analyze/core/analyzer/relations/grouping.py
import numpy as np
import pandas as pd
import logging
from scipy.cluster.hierarchy import linkage, fcluster
from typing import List, Dict, Any

from .config import RelationParams


class GroupingCalculator:
    """Cluster correlated features into groups based on |correlation| or MI matrices.

    Uses hierarchical clustering (average linkage) on (1 - |corr|).
    Returns groups with summary statistics (avg, min, max correlation).
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def compute(self, corr_df: pd.DataFrame, params: RelationParams) -> List[Dict[str, Any]]:
        """
        Compute redundancy groups from correlation or MI matrix.

        Args:
            corr_df: symmetric matrix (e.g., Pearson or MI)
            params: RelationParams with group_threshold

        Returns:
            List of dicts with group members and summary stats:
            [
                {
                    "features": ["f1", "f2", "f3"],
                    "avg_corr": 0.84,
                    "min_corr": 0.79,
                    "max_corr": 0.92,
                },
                ...
            ]
        """
        if corr_df is None or corr_df.empty or corr_df.shape[0] < 2:
            self.logger.debug("Grouping skipped (empty or single-column matrix).")
            return []

        self.logger.info("Building feature groups from correlation matrix...")
        dist = 1 - corr_df.abs()
        dist = dist.dropna(axis=0, how="all").dropna(axis=1, how="all")

        if dist.empty or not np.isfinite(dist.values).any():
            self.logger.debug("Skipping grouping: no valid correlation values.")
            return []

        # All-zero matrix → no structure
        if np.allclose(np.nan_to_num(dist.values), 0):
            self.logger.debug("Skipping grouping: matrix nearly zero.")
            return []

        np.fill_diagonal(dist.values, 0.0)

        try:
            Z = linkage(dist, method="average")
            labels = fcluster(Z, t=(1 - params.group_threshold), criterion="distance")
        except ValueError as e:
            self.logger.warning(f"Skipping grouping (degenerate matrix): {e}")
            return []

        groups: List[Dict[str, Any]] = []
        cols = dist.columns.to_numpy()
        for lbl in np.unique(labels):
            members = cols[labels == lbl].tolist()
            if len(members) <= 1:
                continue

            vals = []
            for i, a in enumerate(members):
                for b in members[i + 1:]:
                    try:
                        v = abs(corr_df.at[a, b])
                        if pd.notna(v):
                            vals.append(v)
                    except Exception:
                        continue

            if not vals:
                continue

            groups.append(
                {
                    "features": members,
                    "avg_corr": float(np.mean(vals)),
                    "min_corr": float(np.min(vals)),
                    "max_corr": float(np.max(vals)),
                }
            )

        groups.sort(key=lambda g: g["avg_corr"], reverse=True)
        self.logger.info(f"Created {len(groups)} feature groups.")
        return groups
