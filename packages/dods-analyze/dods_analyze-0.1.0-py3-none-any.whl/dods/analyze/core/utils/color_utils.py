# dods/analyze/core/utils/color_utils.py
"""
Color and formatting utilities for numeric feature visualization.

Provides:
- fmt_number(): consistent number formatting
- colorize_dynamic(): value coloring based on AnalyzerBase.thresholds
- optional bar rendering for later heatmap-style displays

Used by: deep_analysis modules (distributions, categoricals, etc.)
"""

from typing import Any, Callable, Dict, Tuple
from rich.console import Console

console = Console(width=140)

# ----------------------------------------------------------------------
# Color scheme (up to 5 levels)
# You can easily extend or adjust these later.
# ----------------------------------------------------------------------
COLOR_LEVELS = {
    0: "white",       # no issue
    1: "yellow",      # mild
    2: "orange3",     # medium
    3: "red",         # strong
    4: "bright_red",  # critical
}

# ----------------------------------------------------------------------
# Unified numeric formatter
# ----------------------------------------------------------------------
def fmt_number(value: Any, digits: int = 3, percent: bool = False) -> str:
    """Consistent formatting for numeric values across all tables."""
    if value is None:
        return "-"
    try:
        if percent:
            return f"{float(value):.{digits}f}%"
        else:
            return f"{float(value):.{digits}g}"
    except Exception:
        return str(value)


# ----------------------------------------------------------------------
# Dynamic colorizer
# ----------------------------------------------------------------------
def colorize_dynamic(
    value: float,
    key: str,
    thresholds: Dict[str, Tuple[str, list[Tuple[float, int]]]],
    fmt_func: Callable[[float], str] = None,
    as_bar: bool = False,
) -> str:
    """
    Colorize a numeric value dynamically based on thresholds.

    Parameters
    ----------
    value : float
        The numeric value to colorize.
    key : str
        The metric key (e.g., "skew", "missing_pct").
    thresholds : dict
        The AnalyzerBase.thresholds structure.
    fmt_func : callable, optional
        Custom formatter for displaying numeric values.
    as_bar : bool, optional
        If True, display a colored bar segment (reserved for heatmaps).

    Returns
    -------
    str
        Rich-formatted string (colored value or bar).
    """
    if value is None or key not in thresholds:
        return fmt_number(value)

    fmt_func = fmt_func or (lambda v: fmt_number(v, digits=3, percent=("pct" in key)))

    mode, levels = thresholds[key]

    # --- Determine level ---
    triggered = 0
    for bound, lvl in levels:
        if mode == "high" and value >= bound:
            triggered = max(triggered, lvl)
        elif mode == "low" and value <= bound:
            triggered = max(triggered, lvl)
        elif mode == "abs" and abs(value) >= bound:
            triggered = max(triggered, lvl)

    color = COLOR_LEVELS.get(triggered, "white")
    formatted_value = fmt_func(value)

    # --- Optional bar display (for later expansion) ---
    if as_bar:
        n_blocks = triggered or 1
        blocks = "█" * n_blocks + "░" * (5 - n_blocks)
        return f"[{color}]{blocks}[/{color}] {formatted_value}"

    # --- Colorized numeric output ---
    if triggered == 0:
        return formatted_value
    elif triggered >= 3:
        return f"[bold {color}]{formatted_value}[/bold {color}]"
    else:
        return f"[{color}]{formatted_value}[/{color}]"
