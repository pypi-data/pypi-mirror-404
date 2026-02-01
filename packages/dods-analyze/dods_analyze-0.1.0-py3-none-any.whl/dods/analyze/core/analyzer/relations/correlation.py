# correlation.py
import pandas as pd
import logging
from typing import Dict
from .config import RelationParams


class CorrelationCalculator:
    """
    Compute Pearson and Spearman correlation matrices for numeric features.

    This component isolates all correlation-related computations,
    ensuring a single responsibility for linear and monotonic relationships.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the correlation calculator with an optional shared logger.

        Args:
            logger: Optional shared logger instance (defaults to a local one).
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def compute(self, df: pd.DataFrame, params: RelationParams) -> Dict[str, pd.DataFrame]:
        """
        Compute Pearson and Spearman correlation matrices for all numeric columns.

        Non-numeric columns are ignored, and resulting matrices are reindexed
        to include all original feature names (with NaN for non-numeric features).

        Args:
            df: Input DataFrame containing mixed feature types.
            params: Relation configuration parameters.

        Returns:
            Dict with:
                - "pearson": Pearson correlation matrix (DataFrame)
                - "spearman": Spearman correlation matrix (DataFrame)
        """
        self.logger.info("Calculating Pearson and Spearman correlations...")

        df_num = df.select_dtypes(include="number")
        all_features = df.columns

        if df_num.empty:
            self.logger.warning("No numeric columns found; returning empty correlation matrices.")
            pearson = pd.DataFrame(index=all_features, columns=all_features, dtype=float)
            spearman = pearson.copy()
        else:
            pearson_num = df_num.corr(method="pearson")
            spearman_num = df_num.corr(method="spearman")

            # Reindex to full feature set for consistency
            pearson = pearson_num.reindex(index=all_features, columns=all_features)
            spearman = spearman_num.reindex(index=all_features, columns=all_features)

        self.logger.info("Correlation matrices computed successfully.")
        return {"pearson": pearson, "spearman": spearman}
