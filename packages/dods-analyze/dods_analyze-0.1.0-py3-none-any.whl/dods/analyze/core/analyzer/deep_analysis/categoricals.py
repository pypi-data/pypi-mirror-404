# dods/analyze/core/analyzer/deep_analysis/categoricals.py
"""
Visual exploration of categorical feature distributions.

Integrates with DataAnalyzer:
- Uses analyzer.meta, analyzer.thresholds_by_type, analyzer.info
- Uses dods.core.utils.color_utils for dynamic colorization and formatting
"""

import os
import seaborn as sns
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

from dods.analyze.core.utils.color_utils import fmt_number, colorize_dynamic

console = Console(width=160)


# ----------------------------------------------------------------------
# Helper: qualitative entropy rank
# ----------------------------------------------------------------------
def entropy_rank(entropy_value):
    """Return color-coded textual entropy classification."""
    if entropy_value is None:
        return "-"
    e = entropy_value
    if e < 0.5:
        return "[bold red]1–Skewed[/bold red]"
    elif e < 1.0:
        return "[red]2–Skewed[/red]"
    elif e < 1.5:
        return "[yellow]3–Mod[/yellow]"
    elif e < 2.0:
        return "[green]4–Bal[/green]"
    else:
        return "[bold green]5–Uniform[/bold green]"


# ----------------------------------------------------------------------
# Main analysis
# ----------------------------------------------------------------------
def analyze_categoricals(analyzer, limit=None, columns=None, plots=True, order="dominance"):
    console.print(f"\n[bold bright_black]Source: {__file__}[/bold bright_black]\n")

    if not hasattr(analyzer, "meta") or not hasattr(analyzer, "thresholds_by_type"):
        console.print("[red]⚠️ Analyzer not initialized. Run .analyze() first.[/red]")
        return

    info = analyzer.info or {}
    thresholds = analyzer.thresholds_by_type.get("categorical", {})

    # --- Basic dataset summary ---
    console.print(
        f"[bold cyan]📊 Data Summary[/bold cyan]\n"
        f"Rows: [white]{info.get('n_rows', '?')}[/white] | "
        f"Columns: [white]{info.get('n_columns', '?')}[/white] | "
        f"Numeric: [white]{info.get('n_numeric', '?')}[/white] | "
        f"Categorical: [white]{info.get('n_categorical', '?')}[/white] | "
        f"Datetime: [white]{info.get('n_datetime', '?')}[/white]\n"
        f"Missing total: [white]{info.get('missing_total', '?')}[/white] "
        f"({info.get('missing_pct', 0.0):.2f}%) | "
        f"Memory: [white]{info.get('memory_usage_mb', 0.0):.2f} MB[/white]\n"
    )

    # --- Feature selection ---
    if columns:
        features = [c for c in columns if c in analyzer.meta and analyzer.meta[c].is_categorical]
    else:
        features = [f for f, fs in analyzer.meta.items() if fs.is_categorical]

    if not features:
        console.print("[yellow]No categorical features found.[/yellow]")
        return

    # --- Sort order ---
    if order == "dominance":
        features.sort(key=lambda f: analyzer.meta[f].dominance or 0, reverse=True)
    elif order == "unique":
        features.sort(key=lambda f: analyzer.meta[f].n_categories or 0, reverse=True)
    elif order == "entropy":
        features.sort(key=lambda f: analyzer.meta[f].entropy or 0, reverse=True)
    else:
        features.sort()

    if limit:
        features = features[:limit]

    os.makedirs("_tmp_plots", exist_ok=True)

    # === Overview Table (3g) ===
    table = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False, padding=(0, 0))
    table.add_column("Feature", style="bold white", min_width=25, overflow="fold")
    table.add_column("Categories", justify="left", min_width=9)
    table.add_column("Top Value", justify="left", min_width=23, max_width=30, overflow="fold")
    table.add_column("Least", justify="left", min_width=20, max_width=28, overflow="fold")
    table.add_column("Entropy", justify="right", min_width=9)
    table.add_column("Rank", justify="center", min_width=11)
    table.add_column("Dominance", justify="right", min_width=11)
    table.add_column("NaN%", justify="right", min_width=8)

    for f in features:
        fs = analyzer.meta[f]
        cats = int(fs.n_categories) if fs.n_categories is not None else 0

        top_display, least_display = "-", "-"
        if getattr(fs, "top_values", None):
            if isinstance(fs.top_values, dict):
                items = list(fs.top_values.items())
                if items:
                    top_display = f"{items[0][0]} ({items[0][1]})"
                    least_display = f"{items[-1][0]} ({items[-1][1]})"

        table.add_row(
            f,
            str(cats),
            top_display,
            least_display,
            colorize_dynamic(fs.entropy, "entropy", thresholds, fmt_func=lambda v: fmt_number(v, 3)),
            entropy_rank(fs.entropy),
            colorize_dynamic(fs.dominance, "dominance", thresholds, fmt_func=lambda v: fmt_number(v, 3)),
            colorize_dynamic(fs.missing_pct, "missing_pct", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True)),
        )

    console.print("\n[bold cyan]Categorical Feature Overview[/bold cyan]\n")
    console.print(table)
    console.print()

    # === Panels (4g) ===
    panels = []
    for feat in features:
        fs = analyzer.meta[feat]
        nans_total = int(analyzer.df[feat].isna().sum())

        cats = int(fs.n_categories) if fs.n_categories is not None else 0
        top_values = []
        least_value = "-"
        if getattr(fs, "top_values", None):
            if isinstance(fs.top_values, dict):
                items = list(fs.top_values.items())
                top_values = items[:3]
                if items:
                    least_value = f"{items[-1][0]}: {items[-1][1]}"

        t = Table(box=box.MINIMAL, expand=True, padding=(0, 0))
        t.add_column("Metric", justify="right", style="cyan", no_wrap=True)
        t.add_column("Value", justify="left", min_width=22, max_width=50, overflow="fold")

        rows = [
            ("Type", str(fs.type)),
            ("Categories", cats),
            ("Entropy", colorize_dynamic(fs.entropy, "entropy", thresholds, fmt_func=lambda v: fmt_number(v, 4))),
            ("Entropy Rank", entropy_rank(fs.entropy)),
            ("Dominance", colorize_dynamic(fs.dominance, "dominance", thresholds, fmt_func=lambda v: fmt_number(v, 4))),
            ("NaN%", colorize_dynamic(fs.missing_pct, "missing_pct", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True))),
            ("NaN count", f"{nans_total:,}"),
        ]

        for idx, (name, val) in enumerate(top_values, 1):
            rows.append((f"Top {idx}", f"{name}: {val}"))
        rows.append(("Least", least_value))

        for label, val in rows:
            if not isinstance(val, str):
                val = fmt_number(val) if isinstance(val, (int, float)) else str(val)
            t.add_row(label, val)

        panels.append(
            Panel(
                t,
                title=f"[bold white]{feat}[/bold white]",
                border_style="bright_blue",
                width=34,
                padding=(0, 0),
            )
        )

    console.print("\n[bold cyan]Categorical Feature Details[/bold cyan]\n")

    # --- Render 3 panels + 3 plots per row ---
    for i in range(0, len(panels), 3):
        console.print(Columns(panels[i:i + 3], equal=True, expand=True, align="center"))

        if not plots:
            continue

        subset_feats = features[i:i + 3]
        n = len(subset_feats)
        fig, axes = plt.subplots(1, n, figsize=(n * 4.5, 3))
        if n == 1:
            axes = [axes]

        for j, feat in enumerate(subset_feats):
            series = analyzer.df[feat].dropna()
            counts = series.value_counts(normalize=True).head(10) * 100
            sns.barplot(x=counts.index, y=counts.values, ax=axes[j], color="#4e79a7", edgecolor="white")
            axes[j].set_title(feat, fontsize=13)
            axes[j].set_xlabel("")
            axes[j].set_ylabel("Share (%)")
            axes[j].tick_params(axis="x", rotation=45)
        plt.tight_layout()
        plt.show()



# import os
# import seaborn as sns
# import matplotlib.pyplot as plt
# from rich.console import Console
# from rich.table import Table
# from rich.panel import Panel
# from rich.columns import Columns
# from rich import box

# console = Console(width=160)

# COLOR_THRESHOLDS = {
#     "missing": (0, 10),
#     "unique_low": (20, 5),
#     "dominance": (0.6, 0.8),
#     "entropy": (1.0, 2.0),
# }

# # -------------------------------
# # Unified formatter
# # -------------------------------
# def fmt(value, digits=3, percent=False):
#     """Format numeric values consistently."""
#     if value is None:
#         return "-"
#     if percent:
#         return f"{value:.2f}%"
#     return f"{value:.{digits}g}"

# # -------------------------------
# # Color formatter
# # -------------------------------
# def colorize(value, kind):
#     if value is None:
#         return "-"

#     low, high = COLOR_THRESHOLDS.get(kind, (None, None))

#     if kind == "entropy":
#         if value < low:
#             return f"[bold red]{fmt(value)}[/bold red]"
#         elif value < high:
#             return f"[yellow]{fmt(value)}[/yellow]"
#         return fmt(value)

#     if kind == "dominance":
#         if value > high:
#             return f"[bold red]{fmt(value)}[/bold red]"
#         elif value > low:
#             return f"[yellow]{fmt(value)}[/yellow]"
#         return fmt(value)

#     if kind == "unique_low":
#         if value < high:
#             return f"[bold red]{fmt(value, percent=True)}[/bold red]"
#         elif value < low:
#             return f"[yellow]{fmt(value, percent=True)}[/yellow]"
#         return fmt(value, percent=True)

#     if kind == "missing":
#         if value > high:
#             return f"[bold red]{fmt(value, percent=True)}[/bold red]"
#         elif value > low or value > 0:
#             return f"[yellow]{fmt(value, percent=True)}[/yellow]"
#         return fmt(value, percent=True)

#     return fmt(value)

# # -------------------------------
# # Helper: qualitative entropy rank
# # -------------------------------
# def entropy_rank(entropy_value):
#     if entropy_value is None:
#         return "-"
#     e = entropy_value
#     if e < 0.5:
#         return "[bold red]1–Skewed[/bold red]"
#     elif e < 1.0:
#         return "[red]2–Skewed[/red]"
#     elif e < 1.5:
#         return "[yellow]3–Mod[/yellow]"
#     elif e < 2.0:
#         return "[green]4–Bal[/green]"
#     else:
#         return "[bold green]5–Uniform[/bold green]"

# # -------------------------------
# # Main analysis
# # -------------------------------
# def analyze_categoricals(analyzer, limit=None, columns=None, plots=True, order="dominance"):
#     console.print(f"\n[bold bright_black]Source: {__file__}[/bold bright_black]\n")

#     if not hasattr(analyzer, "meta"):
#         console.print("[red]⚠️ Analyzer not initialized. Run .analyze() first.[/red]")
#         return

#     # --- Basic summary ---
#     info = analyzer.info
#     console.print(
#         f"[bold cyan]📊 Data Summary[/bold cyan]\n"
#         f"Rows: [white]{info['n_rows']}[/white] | "
#         f"Columns: [white]{info['n_columns']}[/white] | "
#         f"Numeric: [white]{info['n_numeric']}[/white] | "
#         f"Categorical: [white]{info['n_categorical']}[/white] | "
#         f"Datetime: [white]{info['n_datetime']}[/white]\n"
#         f"Missing total: [white]{info['missing_total']:,}[/white] "
#         f"({info['missing_pct']:.2f}%) | Memory: [white]{info['memory_usage_mb']:.2f} MB[/white]\n"
#     )

#     # --- Feature selection ---
#     if columns:
#         features = [c for c in columns if c in analyzer.meta and analyzer.meta[c].is_categorical]
#     else:
#         features = [f for f, fs in analyzer.meta.items() if fs.is_categorical]

#     if not features:
#         console.print("[yellow]No categorical features found.[/yellow]")
#         return

#     # --- Sort order ---
#     if order == "dominance":
#         features.sort(key=lambda f: analyzer.meta[f].dominance or 0, reverse=True)
#     elif order == "unique":
#         features.sort(key=lambda f: analyzer.meta[f].n_categories or 0, reverse=True)
#     elif order == "entropy":
#         features.sort(key=lambda f: analyzer.meta[f].entropy or 0, reverse=True)
#     else:
#         features.sort()

#     if limit:
#         features = features[:limit]

#     os.makedirs("_tmp_plots", exist_ok=True)

#     # === Overview Table (3g) ===
#     table = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False, padding=(0, 0))
#     table.add_column("Feature", style="bold white", min_width=25, overflow="fold")
#     table.add_column("Categories", justify="left", min_width=9)
#     table.add_column("Top Value", justify="left", min_width=23, max_width=30, overflow="fold")
#     table.add_column("Least", justify="left", min_width=20, max_width=28, overflow="fold")
#     table.add_column("Entropy", justify="right", min_width=9)
#     table.add_column("Rank", justify="center", min_width=11)
#     table.add_column("Dominance", justify="right", min_width=11)
#     table.add_column("NaN%", justify="right", min_width=8)

#     for f in features:
#         fs = analyzer.meta[f]
#         cats = int(fs.n_categories) if fs.n_categories is not None else 0

#         top_display, least_display = "-", "-"
#         if getattr(fs, "top_values", None):
#             if isinstance(fs.top_values, dict):
#                 items = list(fs.top_values.items())
#                 if items:
#                     top_display = f"{items[0][0]} ({items[0][1]})"
#                     least_display = f"{items[-1][0]} ({items[-1][1]})"

#         table.add_row(
#             f,
#             str(cats),
#             top_display,
#             least_display,
#             colorize(fs.entropy, "entropy"),
#             entropy_rank(fs.entropy),
#             colorize(fs.dominance, "dominance"),
#             colorize(fs.missing_pct, "missing"),
#         )

#     console.print("\n[bold cyan]Categorical Feature Overview[/bold cyan]\n")
#     console.print(table)
#     console.print()

#     # === Panels (4g) ===
#     panels = []
#     for feat in features:
#         fs = analyzer.meta[feat]
#         nans_total = int(analyzer.df[feat].isna().sum())

#         cats = int(fs.n_categories) if fs.n_categories is not None else 0
#         top_values = []
#         least_value = "-"
#         if getattr(fs, "top_values", None):
#             if isinstance(fs.top_values, dict):
#                 items = list(fs.top_values.items())
#                 top_values = items[:3]
#                 if items:
#                     least_value = f"{items[-1][0]}: {items[-1][1]}"

#         t = Table(box=box.MINIMAL, expand=True, padding=(0, 0))
#         t.add_column("Metric", justify="right", style="cyan", no_wrap=True)
#         t.add_column("Value", justify="left", min_width=22, max_width=36, overflow="fold")

#         rows = [
#             ("Type", str(fs.type)),
#             ("Categories", cats),
#             ("Entropy", colorize(fs.entropy, "entropy")),
#             ("Entropy Rank", entropy_rank(fs.entropy)),
#             ("Dominance", colorize(fs.dominance, "dominance")),
#             ("NaN%", colorize(fs.missing_pct, "missing")),
#             ("NaN count", f"{nans_total:,}"),
#         ]

#         for idx, (name, val) in enumerate(top_values, 1):
#             rows.append((f"Top {idx}", f"{name}: {val}"))
#         rows.append(("Least", least_value))

#         for label, val in rows:
#             if isinstance(val, str):
#                 t.add_row(label, val)
#             elif isinstance(val, (int, float)):
#                 # more precision for panels
#                 t.add_row(label, fmt(val, 4))
#             else:
#                 t.add_row(label, "-")

#         panels.append(
#             Panel(
#                 t,
#                 title=f"[bold white]{feat}[/bold white]",
#                 border_style="bright_blue",
#                 width=34,
#                 padding=(0, 0),
#             )
#         )

#     console.print("\n[bold cyan]Categorical Feature Details[/bold cyan]\n")

#     # --- Render 3 panels + 3 plots per row ---
#     for i in range(0, len(panels), 3):
#         console.print(Columns(panels[i:i + 3], equal=True, expand=True, align="center"))

#         if not plots:
#             continue

#         subset_feats = features[i:i + 3]
#         n = len(subset_feats)
#         fig, axes = plt.subplots(1, n, figsize=(n * 4.5, 3))
#         if n == 1:
#             axes = [axes]

#         for j, feat in enumerate(subset_feats):
#             series = analyzer.df[feat].dropna()
#             counts = series.value_counts(normalize=True).head(10) * 100
#             sns.barplot(x=counts.index, y=counts.values, ax=axes[j], color="#4e79a7", edgecolor="white")
#             axes[j].set_title(feat, fontsize=13)
#             axes[j].set_xlabel("")
#             axes[j].set_ylabel("Share (%)")
#             axes[j].tick_params(axis="x", rotation=45)
#         plt.tight_layout()
#         plt.show()
