# dods/analyze/core/utils/common_flags.py

"""
Common flag utilities for feature summaries (numeric, categorical, datetime).

Provides:
- get_flag_symbols(type): returns mapping {flag: short symbol}
- render_flag_legend(console, type): prints legend above tables
- format_flags(flags, type): renders compact inline string of symbols
"""

from rich.panel import Panel
from rich.text import Text
from typing import Dict

# ---------------------------------------------------------------------
# Flag symbol sets
# ---------------------------------------------------------------------
NUMERIC_FLAGS = {
    "missing_pct": "M",
    "skew": "S",
    "outlier_ratio": "O",
    "cv": "V",
    "cv_robust": "R",
}

CATEGORICAL_FLAGS = {
    "missing_pct": "M",
    "dominance": "D",
    "entropy": "E",
    "unique_pct": "U",
}

DATETIME_FLAGS = {
    "missing_pct": "M",
}

# ---------------------------------------------------------------------
def get_flag_symbols(feature_type: str) -> Dict[str, str]:
    """Return mapping of flag→symbol depending on feature type."""
    if feature_type == "numeric":
        return NUMERIC_FLAGS
    if feature_type == "categorical":
        return CATEGORICAL_FLAGS
    if feature_type == "datetime":
        return DATETIME_FLAGS
    return {}

# ---------------------------------------------------------------------
def render_flag_legend(console, feature_type: str):
    """Print compact legend panel above tables."""
    mapping = get_flag_symbols(feature_type)
    if not mapping:
        return
    text = Text()
    for k, v in mapping.items():
        text.append(f"{v} ", style="bold cyan")
        text.append(f"{k}   ", style="dim")
    console.print(Panel(text, title="Legend", border_style="dim", expand=False))

# ---------------------------------------------------------------------
def format_flags(flag_dict: Dict[str, int] | None, feature_type: str) -> str:
    """Render flags as compact symbol string (e.g., 'M S O')."""
    if not flag_dict:
        return "–"
    mapping = get_flag_symbols(feature_type)
    out = []
    for k in flag_dict.keys():
        sym = mapping.get(k, k[:1].upper())
        out.append(sym)
    return " ".join(out)
