# dods/analyze/core/analyzer/deep_analysis/distributions.py
"""
Visual exploration of numeric feature distributions.

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
# Main entry point
# ----------------------------------------------------------------------
def analyze_distributions(analyzer, limit=None, columns=None, plots=True):
    """
    Display numeric feature summary tables and histograms.
    """
    if not hasattr(analyzer, "meta") or not hasattr(analyzer, "thresholds_by_type"):
        console.print("[red]⚠️ Analyzer not initialized. Run .analyze() first.[/red]")
        return

    cfgs = analyzer.plot_configs.get("distribution", {}) if hasattr(analyzer, "plot_configs") else {}
    info = analyzer.info or {}
    thresholds = analyzer.thresholds_by_type.get("numeric", {})

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
        features = [c for c in columns if c in analyzer.meta and analyzer.meta[c].is_numeric]
    else:
        features = [f for f, fs in analyzer.meta.items() if fs.is_numeric and f in cfgs]

    if limit:
        features = features[:limit]

    if not features:
        console.print("[yellow]No numeric features found.[/yellow]")
        return

    os.makedirs("_tmp_plots", exist_ok=True)

    # === Overview Table (3g) ===
    table = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False, padding=(0, 0))
    table.add_column("Feature", style="bold white", justify="left", min_width=18, max_width=30, overflow="fold")

    columns = [
        ("Mean", 12),
        ("Min", 11),
        ("Max", 11),
        ("Std", 11),
        ("Var", 11),
        ("Skew", 12),
        ("CV", 11),
        ("CVr", 11),
        ("NaN%", 9),
        ("Unique%", 9),
        ("Outliers%", 9),
    ]
    for col, width in columns:
        table.add_column(col, justify="right", min_width=width, max_width=width, no_wrap=True)

    # === Fill rows ===
    for f in features:
        fs = analyzer.meta[f]
        table.add_row(
            f,
            fmt_number(fs.mean, 3),
            fmt_number(fs.min, 3),
            fmt_number(fs.max, 3),
            fmt_number(fs.std, 3),
            fmt_number(fs.variance, 3),
            colorize_dynamic(fs.skew, "skew", thresholds, fmt_func=lambda v: fmt_number(v, 3)),
            colorize_dynamic(fs.cv, "cv", thresholds, fmt_func=lambda v: fmt_number(v, 3)),
            colorize_dynamic(fs.cv_robust, "cv_robust", thresholds, fmt_func=lambda v: fmt_number(v, 3)),
            colorize_dynamic(fs.missing_pct, "missing_pct", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True)),
            colorize_dynamic(fs.unique_pct, "unique_pct", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True)),
            colorize_dynamic(fs.outlier_ratio, "outlier_ratio", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True)),
        )

    console.print("\n[bold cyan]Numeric Feature Overview[/bold cyan]\n")
    console.print(table)
    console.print()

    # === Panels (4g) ===
    panels = []
    for feat in features:
        fs = analyzer.meta[feat]
        cfg = cfgs.get(feat, {})
        params = cfg.get("params", {})

        t = Table(box=box.MINIMAL, expand=True)
        t.add_column("Metric", justify="right", style="cyan", no_wrap=True)
        t.add_column("Value", justify="left", min_width=20)

        rows = [
            ("DType", str(getattr(fs, "type", "-"))),
            ("Mean", fmt_number(fs.mean, 4)),
            ("Q25", fmt_number(fs.q25, 4)),
            ("Q75", fmt_number(fs.q75, 4)),
            ("Min", fmt_number(fs.min, 4)),
            ("Max", fmt_number(fs.max, 4)),
            ("Std", fmt_number(fs.std, 4)),
            ("Var", fmt_number(fs.variance, 4)),
            ("Skew", colorize_dynamic(fs.skew, "skew", thresholds, fmt_func=lambda v: fmt_number(v, 4))),
            ("CV", colorize_dynamic(fs.cv, "cv", thresholds, fmt_func=lambda v: fmt_number(v, 4))),
            ("CVr", colorize_dynamic(fs.cv_robust, "cv_robust", thresholds, fmt_func=lambda v: fmt_number(v, 4))),
            ("NaN%", colorize_dynamic(fs.missing_pct, "missing_pct", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True))),
            ("Unique%", colorize_dynamic(fs.unique_pct, "unique_pct", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True))),
            ("Outliers%", colorize_dynamic(fs.outlier_ratio, "outlier_ratio", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True))),
        ]
        for label, val in rows:
            t.add_row(label, val)

        panels.append(
            Panel(
                t,
                title=f"[bold white]{cfg.get('meta', {}).get('title', feat)}[/bold white]",
                border_style="bright_blue",
                width=35,
                padding=(0, 0),
            )
        )

        # === Plot ===
        fig, ax = plt.subplots(figsize=(3.5, 2.3))
        sns.histplot(
            analyzer.df[feat].dropna(),
            bins=params.get("bins", 30),
            stat="density" if params.get("density") else "count",
            color="#4e79a7",
            edgecolor="white",
            ax=ax,
        )
        ax.set_title(cfg.get("meta", {}).get("title", feat), fontsize=9)
        if params.get("xlim"):
            ax.set_xlim(params["xlim"])
        plt.tight_layout()
        fig.savefig(f"_tmp_plots/{feat}.png", bbox_inches="tight")
        plt.close(fig)

    console.print("\n[bold cyan]Numeric Feature Distributions[/bold cyan]\n")

    # === Panels & plots grouped by 3 ===
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
            ax = axes[j]
            cfg = cfgs.get(feat, {})
            params = cfg.get("params", {})
            sns.histplot(
                analyzer.df[feat].dropna(),
                bins=params.get("bins", 30),
                stat="density" if params.get("density") else "count",
                color="#4e79a7",
                edgecolor="white",
                ax=ax,
            )
            ax.set_title(cfg.get("meta", {}).get("title", feat), fontsize=13)
            if params.get("xlim"):
                ax.set_xlim(params["xlim"])
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
#     "outlier": (0, 1),
#     "skew": (1, 3),
#     "cv": (0.5, 1.0),
#     "cv_robust": (0.5, 1.0),
# }


# # -------------------------------
# # Unified number formatter
# # -------------------------------
# def fmt(value, digits=3, percent=False):
#     """Format numbers consistently across tables and panels."""
#     if value is None:
#         return "-"
#     if percent:
#         return f"{value:.2f}%"
#     return f"{value:.{digits}g}"


# # -------------------------------
# # Unified colorizer
# # -------------------------------
# def colorize(value, kind):
#     if value is None:
#         return "-"

#     if kind == "unique_low":
#         low, high = COLOR_THRESHOLDS[kind]
#         if value < high:
#             return f"[bold red]{fmt(value, percent=True)}[/bold red]"
#         elif value < low:
#             return f"[yellow]{fmt(value, percent=True)}[/yellow]"
#         return fmt(value, percent=True)

#     low, high = COLOR_THRESHOLDS.get(kind, (None, None))

#     if kind == "skew":
#         v = abs(value)
#         if v > high:
#             return f"[bold red]{fmt(value)}[/bold red]"
#         elif v > low:
#             return f"[yellow]{fmt(value)}[/yellow]"
#         return fmt(value)

#     if kind in ("cv", "cv_robust"):
#         if value > high:
#             return f"[bold red]{fmt(value)}[/bold red]"
#         elif value > low:
#             return f"[yellow]{fmt(value)}[/yellow]"
#         return fmt(value)

#     # Missing / Outlier percentages
#     if kind in ("missing", "outlier"):
#         if value > high:
#             return f"[bold red]{fmt(value, percent=True)}[/bold red]"
#         elif value > low or value > 0:
#             return f"[yellow]{fmt(value, percent=True)}[/yellow]"
#         return fmt(value, percent=True)

#     # Fallback
#     return fmt(value)


# # -------------------------------
# # Main: analyze_distributions
# # -------------------------------
# def analyze_distributions(analyzer, limit=None, columns=None, plots=True):
#     if not hasattr(analyzer, "meta") or not hasattr(analyzer, "plot_configs"):
#         console.print("[red]⚠️ Analyzer not initialized. Run .analyze() first.[/red]")
#         return

#     cfgs = analyzer.plot_configs.get("distribution", {})

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
#         features = [c for c in columns if c in analyzer.meta and analyzer.meta[c].is_numeric]
#     else:
#         features = [f for f, fs in analyzer.meta.items() if fs.is_numeric and f in cfgs]

#     if limit:
#         features = features[:limit]

#     if not features:
#         console.print("[yellow]No numeric features found.[/yellow]")
#         return

#     os.makedirs("_tmp_plots", exist_ok=True)

#     # === Overview Table ===
#     table = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False, padding=(0, 0))
#     table.add_column("Feature", style="bold white", justify="left", min_width=18, max_width=30, overflow="fold")

#     columns = [
#         ("Mean", 12),
#         ("Min", 11),
#         ("Max", 11),
#         ("Std", 11),
#         ("Var", 11),
#         ("Skew", 12),
#         ("CV", 11),
#         ("CVr", 11),
#         ("NaN%", 9),
#         ("Unique%", 9),
#         ("Outliers%", 9),
#     ]
#     for col, width in columns:
#         table.add_column(col, justify="right", min_width=width, max_width=width, no_wrap=True)

#     # === Fill rows === (overview → 3g)
#     for f in features:
#         fs = analyzer.meta[f]
#         table.add_row(
#             f,
#             fmt(fs.mean, 3),
#             fmt(fs.min, 3),
#             fmt(fs.max, 3),
#             fmt(fs.std, 3),
#             fmt(fs.variance, 3),
#             colorize(fs.skew, "skew"),
#             colorize(fs.cv, "cv"),
#             colorize(fs.cv_robust, "cv_robust"),
#             colorize(fs.missing_pct, "missing"),
#             colorize(fs.unique_pct, "unique_low"),
#             colorize(fs.outlier_ratio, "outlier"),
#         )

#     console.print("\n[bold cyan]Numeric Feature Overview[/bold cyan]\n")
#     console.print(table)
#     console.print()

#     # === Panels + Plots === (panels → 4g)
#     panels = []
#     for feat in features:
#         fs = analyzer.meta[feat]
#         cfg = cfgs[feat]
#         params = cfg.get("params", {})

#         t = Table(box=box.MINIMAL, expand=True)
#         t.add_column("Metric", justify="right", style="cyan", no_wrap=True)
#         t.add_column("Value", justify="left", min_width=20)

#         rows = [
#             ("DType", str(fs.type) if getattr(fs, "type", None) else "-"),
#             ("Mean", fmt(fs.mean, 4)),
#             ("Q25", fmt(fs.q25, 4)),
#             ("Q75", fmt(fs.q75, 4)),
#             ("Min", fmt(fs.min, 4)),
#             ("Max", fmt(fs.max, 4)),
#             ("Std", fmt(fs.std, 4)),
#             ("Var", fmt(fs.variance, 4)),
#             ("Skew", colorize(fs.skew, "skew")),
#             ("CV", colorize(fs.cv, "cv")),
#             ("CVr", colorize(fs.cv_robust, "cv_robust")),
#             ("NaN%", colorize(fs.missing_pct, "missing")),
#             ("Unique%", colorize(fs.unique_pct, "unique_low")),
#             ("Outliers%", colorize(fs.outlier_ratio, "outlier")),
#         ]

#         for label, val in rows:
#             t.add_row(label, val)

#         panels.append(
#             Panel(
#                 t,
#                 title=f"[bold white]{cfg['meta'].get('title', feat)}[/bold white]",
#                 border_style="bright_blue",
#                 width=35,
#                 padding=(0, 0),
#             )
#         )

#         # === Plot ===
#         fig, ax = plt.subplots(figsize=(3.5, 2.3))
#         sns.histplot(
#             analyzer.df[feat].dropna(),
#             bins=params.get("bins", 30),
#             stat="density" if params.get("density") else "count",
#             color="#4e79a7",
#             edgecolor="white",
#             ax=ax,
#         )
#         ax.set_title(cfg["meta"].get("title", feat), fontsize=9)
#         if params.get("xlim"):
#             ax.set_xlim(params["xlim"])
#         plt.tight_layout()
#         fig.savefig(f"_tmp_plots/{feat}.png", bbox_inches="tight")
#         plt.close(fig)

#     console.print("\n[bold cyan]Numeric Feature Distributions[/bold cyan]\n")

#     # === Panels & plots grouped by 3 ===
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
#             ax = axes[j]
#             cfg = cfgs[feat]
#             params = cfg.get("params", {})
#             sns.histplot(
#                 analyzer.df[feat].dropna(),
#                 bins=params.get("bins", 30),
#                 stat="density" if params.get("density") else "count",
#                 color="#4e79a7",
#                 edgecolor="white",
#                 ax=ax,
#             )
#             ax.set_title(cfg["meta"].get("title", feat), fontsize=13)
#             if params.get("xlim"):
#                 ax.set_xlim(params["xlim"])
#         plt.tight_layout()
#         plt.show()
