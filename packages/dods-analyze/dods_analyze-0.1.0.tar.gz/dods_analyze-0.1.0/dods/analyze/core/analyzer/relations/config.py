# config.py
from dataclasses import dataclass

@dataclass(frozen=True)
class RelationParams:
    """Default configuration for the RelationEngine and its calculators."""
    pearson_threshold: float = 0.5
    group_threshold: float = 0.82
    mi_max_pairs: int = 300
    subsample: int = 10_000
    iso_threshold: float = 0.15

    outlier_iqr_factor: float = 3.0
    outlier_flag_threshold: float = 0.03
    skew_flag_threshold: float = 1.0

    mi_knn_neighbors: int = 5
    mi_n_bins: int = 20
    mi_top_categories: int = 30

    classify_low_pearson_monotone: float = 0.3
    classify_low_pearson_nonlinear: float = 0.2
    classify_spearman_monotone: float = 0.6
    classify_mi_complex: float = 0.05
    classify_linear_weak: float = 0.3
    classify_linear_strong: float = 0.7
