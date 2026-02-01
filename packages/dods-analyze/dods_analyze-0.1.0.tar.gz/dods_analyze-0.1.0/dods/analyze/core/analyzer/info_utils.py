# dods/analyze/core/analyzer/info_utils.py
"""
Shared utilities for dataset-level info aggregation and flag summarization.
Used by AnalyzerBase and its subclasses.
"""

from typing import Any, Dict, Tuple
import numpy as np
import logging


def summarize_flags(
    meta: Dict[str, Any],
    thresholds_by_type: Dict[str, Dict[str, Any]],
    logger: logging.Logger,
):
    """Aggregate counts and affected features per metric flag."""
    # --- Collect all metric names across all types ---
    all_metrics = set()
    for tdict in thresholds_by_type.values():
        all_metrics.update(tdict.keys())

    # --- Initialize result structure ---
    flag_counts: Dict[str, Dict[str, Any]] = {
        metric: {"count": 0, "features": []} for metric in all_metrics
    }

    levels = []
    for fs in meta.values():
        if not fs.flag:
            continue
        for metric, level in fs.flag.items():
            if metric not in flag_counts:
                flag_counts[metric] = {"count": 0, "features": []}
            flag_counts[metric]["count"] += 1
            flag_counts[metric]["features"].append(fs.name)
            levels.append(level)

    n_flagged_features = sum(1 for fs in meta.values() if fs.flag)
    avg_intensity = float(np.mean(levels)) if levels else 0.0

    logger.info(
        "Flag summary: %d flagged features, avg intensity %.2f",
        n_flagged_features, avg_intensity,
    )
    return flag_counts, n_flagged_features, avg_intensity


def update_info(
    meta: Dict[str, Any],
    df: Any,
    thresholds_by_type: Dict[str, Any],
    logger: logging.Logger,
):
    """Recompute global dataset summary information."""
    if not meta:
        logger.warning("update_info called without metadata.")
        return {}

    if df is not None:
        n_rows, n_cols = df.shape
        mem_mb = float(df.memory_usage(deep=True).sum() / 1e6)
    else:
        n_cols = len(meta)
        first = next(iter(meta.values()))
        n_rows = getattr(first, "n_non_null", 0)
        mem_mb = sum((getattr(fs, "memory_usage_mb", 0.0) or 0.0) for fs in meta.values())

    n_numeric = sum(1 for fs in meta.values() if fs.is_numeric)
    n_categorical = sum(1 for fs in meta.values() if fs.is_categorical)
    n_datetime = sum(1 for fs in meta.values() if fs.is_datetime)

    missing_total = sum(
        ((fs.missing_pct or 0.0) / 100) * n_rows for fs in meta.values()
    )
    avg_missing_pct = float(
        np.mean([fs.missing_pct for fs in meta.values() if fs.missing_pct is not None])
    )

    flag_counts, n_flagged_features, avg_intensity = summarize_flags(
        meta, thresholds_by_type, logger
    )

    info = {
        "n_rows": int(n_rows),
        "n_columns": int(n_cols),
        "n_numeric": int(n_numeric),
        "n_categorical": int(n_categorical),
        "n_datetime": int(n_datetime),
        "missing_total": int(missing_total),
        "missing_pct": avg_missing_pct,
        "memory_usage_mb": mem_mb,
        "flag_counts": flag_counts,
        "n_flagged_features": n_flagged_features,
        "flag_intensity_avg": avg_intensity,
    }

    logger.info(
        "Dataset summary: %d rows, %d columns (%d num / %d cat / %d dt)",
        n_rows, n_cols, n_numeric, n_categorical, n_datetime,
    )
    return info
