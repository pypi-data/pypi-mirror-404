# dods/analyze/core/analyzer/stats_compute.py
import pandas as pd
import numpy as np
from scipy import stats
import logging
from ..feature_stats import FeatureStats
import warnings

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

def infer_cast_suggestion(series: pd.Series, inferred: str) -> str | None:
    """
    Try to suggest a better dtype for 'object'-like columns.
    Returns one of: 'int64', 'float64', 'datetime64[ns]', 'bool', or None.

    Silently skips noisy parsing warnings (e.g. during to_datetime).
    Logs only truly unexpected issues.
    """
    if not pd.api.types.is_object_dtype(series):
        return None

    s = series.dropna().astype(str)
    if len(s) == 0:
        return None

    # Silence typical pandas conversion warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        warnings.simplefilter("ignore", category=FutureWarning)

        try:
            # --- numeric detection ---
            if s.str.fullmatch(r"[-+]?\d+").mean() > 0.9:
                return "int64"
            if s.str.fullmatch(r"[-+]?\d*\.?\d+").mean() > 0.9:
                return "float64"

            # --- datetime detection ---
            parsed = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
            if parsed.notna().mean() > 0.9:
                return "datetime64[ns]"

            # --- boolean detection ---
            if s.str.lower().isin(["true", "false", "yes", "no", "0", "1"]).mean() > 0.9:
                return "bool"

        except Exception as e:
            logger.debug(f"⚠️ infer_cast_suggestion({series.name}): {type(e).__name__} - {e}")

    return None




def compute_feature_stats(series: pd.Series) -> FeatureStats:
    """
    Compute detailed statistics for a single column.
    Supports numeric, categorical, and datetime types.
    """
    name = series.name
    logger.debug(f"→ Computing stats for '{name}'")

    dtype_str = str(series.dtype)
    inferred = pd.api.types.infer_dtype(series, skipna=True)

    is_num = pd.api.types.is_numeric_dtype(series)
    is_cat = pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series)
    is_dt = pd.api.types.is_datetime64_any_dtype(series)

    n_non_null = int(series.notna().sum())
    missing_pct = float(series.isna().mean() * 100)
    unique_pct = float(series.nunique(dropna=True) / len(series) * 100) if len(series) > 0 else 0.0

    # -----------------------------------------
    # Initialize all optional fields
    # -----------------------------------------
    mean = std = minv = maxv = q25 = median = q75 = variance = iqr = skew = None
    cv = cv_robust = None
    outliers = outlier_ratio = None
    n_categories = top_values = top_ratio = entropy = dominance = None

    # -----------------------------------------
    # Numeric columns
    # -----------------------------------------
    if is_num:
        logger.debug(f"   ↳ Numeric column detected: {name}")
        s = series.dropna()
        if len(s) > 0:
            mean = float(s.mean())
            std = float(s.std())
            minv = float(s.min())
            q25, median, q75 = np.percentile(s, [25, 50, 75])
            maxv = float(s.max())
            variance = float(np.var(s))
            iqr = q75 - q25
            skew = float(stats.skew(s)) if len(s) > 2 else 0.0

            cv = float(std / abs(mean)) if mean and mean != 0 else None
            cv_robust = float(iqr / abs(median)) if median and median != 0 else None

            # Outliers via 1.5*IQR rule
            lower, upper = q25 - 1.5 * iqr, q75 + 1.5 * iqr
            outliers = int(((s < lower) | (s > upper)).sum())
            outlier_ratio = float(outliers / len(s) * 100)

            logger.debug(
                f"   → mean={mean:.3f}, std={std:.3f}, skew={skew:.3f}, outliers={outlier_ratio:.2f}%"
            )

    # -----------------------------------------
    # Categorical columns
    # -----------------------------------------
    elif is_cat:
        logger.debug(f"   ↳ Categorical column detected: {name}")
        s = series.dropna().astype(str)
        if len(s) > 0:
            vc = s.value_counts()
            n_categories = int(len(vc))
            top_values = vc.head(5).to_dict()
            total = len(s)
            top_ratio = float(vc.iloc[0] / total)
            probs = vc / total
            entropy = float(-(probs * np.log2(probs)).sum())
            dominance = float(top_ratio)

            logger.debug(
                f"   → n_cat={n_categories}, top_ratio={top_ratio:.2f}, entropy={entropy:.2f}"
            )

    # -----------------------------------------
    # Datetime columns
    # -----------------------------------------
    elif is_dt:
        logger.debug(f"   ↳ Datetime column detected: {name}")
        s = series.dropna()
        if len(s) > 0:
            minv = s.min()
            maxv = s.max()
            logger.debug(f"   → range: {minv} → {maxv}")

    # -----------------------------------------
    # Cast suggestions for object columns
    # ----------------------------------------
    cast_suggestion = infer_cast_suggestion(series, inferred)


    # -----------------------------------------
    # Create FeatureStats
    # -----------------------------------------
    fs = FeatureStats(
        name=name,
        type=dtype_str,
        dtype_inferred=inferred,
        is_numeric=is_num,
        is_categorical=is_cat,
        is_datetime=is_dt,
        n_non_null=n_non_null,
        missing_pct=missing_pct,
        unique_pct=unique_pct,
        mean=mean,
        std=std,
        min=minv,
        q25=q25,
        median=median,
        q75=q75,
        max=maxv,
        variance=variance,
        iqr=iqr,
        skew=skew,
        cv=cv,
        cv_robust=cv_robust,
        outliers=outliers,
        outlier_ratio=outlier_ratio,
        top_values=top_values,
        top_ratio=top_ratio,
        n_categories=n_categories,
        entropy=entropy,
        dominance=dominance,
        flag={},  # leer – ThresholdEngine füllt das später
        memory_usage_mb=float(series.memory_usage(deep=True) / 1e6),
        cast_suggestion=cast_suggestion,
    )

    logger.debug(f"   ✓ Stats computed for '{name}'")
    return fs


def compute_all_stats(df: pd.DataFrame) -> dict[str, FeatureStats]:
    """Compute feature statistics for all columns in a DataFrame."""
    meta = {}
    logger.info(f"Starting feature stats computation for {len(df.columns)} columns")
    for col in df.columns:
        try:
            meta[col] = compute_feature_stats(df[col])
        except Exception as e:
            logger.warning(f"⚠️ Error computing stats for '{col}': {e}")
    logger.info("Feature stats computation finished")
    return meta
