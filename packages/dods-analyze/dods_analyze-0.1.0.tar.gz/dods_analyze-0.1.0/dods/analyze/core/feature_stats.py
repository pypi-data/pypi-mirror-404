# dods/analyze/core/feature_stats.py
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any


@dataclass
class FeatureStats:
    """
    Container for detailed per-feature statistics.
    Covers numeric, categorical, and datetime columns.
    """

    # --- Core metadata ---
    name: str
    type: str
    dtype_inferred: str
    is_numeric: bool
    is_categorical: bool
    is_datetime: bool

    n_non_null: int
    missing_pct: float
    unique_pct: float

    # --- Numeric statistics ---
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    q25: Optional[float] = None
    median: Optional[float] = None
    q75: Optional[float] = None
    max: Optional[float] = None
    variance: Optional[float] = None
    iqr: Optional[float] = None
    skew: Optional[float] = None

    cv: Optional[float] = None
    cv_robust: Optional[float] = None
    outliers: Optional[int] = None
    outlier_ratio: Optional[float] = None

    # --- Categorical statistics ---
    top_values: Optional[Dict[str, int]] = None
    top_ratio: Optional[float] = None
    n_categories: Optional[int] = None
    entropy: Optional[float] = None
    dominance: Optional[float] = None

    # --- Correlation & grouping ---
    corr_top: Optional[Dict[str, float]] = None
    corr_group: Optional[int] = None

    # --- Meta / quality flags ---
    flag: Dict[str, int] = field(default_factory=dict)
    """Dictionary mapping metric_name → severity_level (e.g. {'skew': 2, 'outlier_ratio': 1})"""

    cast_suggestion: Optional[str] = None
    memory_usage_mb: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert dataclass to a serializable dictionary."""
        return asdict(self)
