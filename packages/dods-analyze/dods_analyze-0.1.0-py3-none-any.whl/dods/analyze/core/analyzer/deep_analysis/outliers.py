# dods/analyze/core/analyzer/deep_analysis/outliers.py

"""
Visual exploration of numeric outliers.

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
# Main: analyze_outliers
# ----------------------------------------------------------------------
def analyze_outliers(analyzer, limit=None, columns=None, plots=True, order="biggest"):
    console.print(f"\n[bold bright_black]Source: {__file__}[/bold bright_black]\n")

    if not hasattr(analyzer, "meta") or not hasattr(analyzer, "thresholds_by_type"):
        console.print("[red]⚠️ Analyzer not initialized. Run .analyze() first.[/red]")
        return

    cfgs = analyzer.plot_configs.get("outliers", {}) if hasattr(analyzer, "plot_configs") else {}
    if not cfgs:
        console.print("[yellow]No outlier configurations found — likely no numeric features with outliers.[/yellow]")
        return

    info = analyzer.info or {}
    thresholds = analyzer.thresholds_by_type.get("outliers", {})

    # --- Dataset summary ---
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
        features = [c for c in columns if c in cfgs]
    else:
        features = list(cfgs.keys())

    if order == "biggest":
        features.sort(key=lambda f: analyzer.meta[f].outlier_ratio or 0, reverse=True)
    elif order == "skew":
        features.sort(key=lambda f: abs(analyzer.meta[f].skew or 0), reverse=True)
    elif order == "cv":
        features.sort(key=lambda f: analyzer.meta[f].cv or 0, reverse=True)
    else:
        features.sort()

    if limit:
        features = features[:limit]

    os.makedirs("_tmp_plots", exist_ok=True)

    # === Overview Table ===
    table = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False, padding=(0, 0))
    table.add_column("Feature", style="bold white", min_width=20, overflow="fold")
    table.add_column("Outliers%", justify="right", min_width=12)
    table.add_column("Skew", justify="right", min_width=10)
    table.add_column("CV", justify="right", min_width=10)
    table.add_column("Mean", justify="right", min_width=12)
    table.add_column("Std", justify="right", min_width=12)
    table.add_column("Min", justify="right", min_width=12)
    table.add_column("Max", justify="right", min_width=12)

    for f in features:
        fs = analyzer.meta[f]
        table.add_row(
            f,
            colorize_dynamic(fs.outlier_ratio, "outlier_ratio", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True)),
            colorize_dynamic(fs.skew, "skew", thresholds, fmt_func=lambda v: fmt_number(v, 3)),
            colorize_dynamic(fs.cv, "cv", thresholds, fmt_func=lambda v: fmt_number(v, 3)),
            fmt_number(fs.mean, 3),
            fmt_number(fs.std, 3),
            fmt_number(fs.min, 3),
            fmt_number(fs.max, 3),
        )

    console.print("\n[bold cyan]Outlier Overview[/bold cyan]\n")
    console.print(table)
    console.print()

    # === Panels ===
    panels = []
    for feat in features:
        fs = analyzer.meta[feat]
        cfg = cfgs[feat]
        params = cfg.get("params", {})

        title = cfg.get("meta", {}).get("title", feat).replace(" - Outlier distribution", "")

        t = Table(box=box.MINIMAL, expand=True, padding=(0, 0))
        t.add_column("Metric", justify="right", style="cyan", no_wrap=True)
        t.add_column("Value", justify="left", min_width=24)

        rows = [
            ("Mean", fmt_number(fs.mean, 4)),
            ("Std", fmt_number(fs.std, 4)),
            ("Var", fmt_number(fs.variance, 4)),
            ("Skew", colorize_dynamic(fs.skew, "skew", thresholds, fmt_func=lambda v: fmt_number(v, 4))),
            ("CV", colorize_dynamic(fs.cv, "cv", thresholds, fmt_func=lambda v: fmt_number(v, 4))),
            ("CVr", colorize_dynamic(fs.cv_robust, "cv_robust", thresholds, fmt_func=lambda v: fmt_number(v, 4))),
            ("Outliers%", colorize_dynamic(fs.outlier_ratio, "outlier_ratio", thresholds, fmt_func=lambda v: fmt_number(v, 2, percent=True))),
            ("Outlier count", fmt_number(fs.outliers, 4)),
            ("IQR", fmt_number(fs.iqr, 4)),
            ("Q25", fmt_number(fs.q25, 4)),
            ("Q75", fmt_number(fs.q75, 4)),
            ("Min", fmt_number(fs.min, 4)),
            ("Max", fmt_number(fs.max, 4)),
        ]

        for label, val in rows:
            if not isinstance(val, str):
                val = fmt_number(val) if isinstance(val, (int, float)) else str(val)
            t.add_row(label, val)

        panels.append(
            Panel(
                t,
                title=f"[bold white]{title}[/bold white]",
                border_style="bright_blue",
                width=32,
                padding=(0, 0),
            )
        )

        # === Plot ===
        if plots:
            fig, ax = plt.subplots(figsize=(3.5, 2.3))
            sns.boxplot(
                x=analyzer.df[feat].dropna(),
                whis=params.get("whis", 1.5),
                showfliers=params.get("showfliers", True),
                notch=params.get("notch", True),
                color="#4e79a7",
                ax=ax,
            )
            ax.set_title(title, fontsize=8)
            plt.tight_layout()
            fig.savefig(f"_tmp_plots/{feat}_outliers.png", bbox_inches="tight")
            plt.close(fig)

    console.print("\n[bold cyan]Outlier Details[/bold cyan]\n")

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
            cfg = cfgs[feat]
            params = cfg.get("params", {})
            sns.boxplot(
                x=analyzer.df[feat].dropna(),
                whis=params.get("whis", 1.5),
                showfliers=params.get("showfliers", True),
                notch=params.get("notch", True),
                color="#4e79a7",
                ax=axes[j],
            )
            axes[j].set_title(cfg.get("meta", {}).get("title", feat), fontsize=13)
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
#     "outlier_ratio": (1, 5),   # yellow >1%, red >5%
#     "skew": (1, 3),
#     "cv": (0.5, 1.0),
# }


# # -------------------------------
# # Helper: unified number formatter
# # -------------------------------
# def fmt(value, digits=3, percent=False):
#     """Format numbers consistently across tables and panels."""
#     if value is None:
#         return "-"
#     if percent:
#         return f"{value:.2f}%"
#     return f"{value:.{digits}g}"


# # -------------------------------
# # Helper: color formatting
# # -------------------------------
# def colorize(value, kind):
#     if value is None:
#         return "-"

#     low, high = COLOR_THRESHOLDS.get(kind, (None, None))

#     # percentage-based colorization
#     if kind == "outlier_ratio":
#         if value > high:
#             return f"[bold red]{fmt(value, percent=True)}[/bold red]"
#         elif value > low:
#             return f"[yellow]{fmt(value, percent=True)}[/yellow]"
#         return fmt(value, percent=True)

#     # numeric metrics (skew, cv)
#     if kind == "skew":
#         v = abs(value)
#         if v > high:
#             return f"[bold red]{fmt(value)}[/bold red]"
#         elif v > low:
#             return f"[yellow]{fmt(value)}[/yellow]"
#         return fmt(value)

#     if kind == "cv":
#         if value > high:
#             return f"[bold red]{fmt(value)}[/bold red]"
#         elif value > low:
#             return f"[yellow]{fmt(value)}[/yellow]"
#         return fmt(value)

#     return fmt(value)


# # -------------------------------
# # Main: analyze_outliers
# # -------------------------------
# def analyze_outliers(analyzer, limit=None, columns=None, plots=True, order="biggest"):
#     if not hasattr(analyzer, "meta") or not hasattr(analyzer, "plot_configs"):
#         console.print("[red]⚠️ Analyzer not initialized. Run .analyze() first.[/red]")
#         return

#     cfgs = analyzer.plot_configs.get("outliers", {})
#     if not cfgs:
#         console.print("[yellow]No outlier configurations found — likely no numeric features with outliers.[/yellow]")
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
#         features = [c for c in columns if c in cfgs]
#     else:
#         features = list(cfgs.keys())

#     if order == "biggest":
#         features.sort(key=lambda f: analyzer.meta[f].outlier_ratio or 0, reverse=True)
#     elif order == "skew":
#         features.sort(key=lambda f: abs(analyzer.meta[f].skew or 0), reverse=True)
#     elif order == "cv":
#         features.sort(key=lambda f: analyzer.meta[f].cv or 0, reverse=True)
#     else:
#         features.sort()

#     if limit:
#         features = features[:limit]

#     os.makedirs("_tmp_plots", exist_ok=True)

#     # === Overview Table ===
#     table = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False, padding=(0, 0))
#     table.add_column("Feature", style="bold white", min_width=20, overflow="fold")
#     table.add_column("Outliers%", justify="right", min_width=12)
#     table.add_column("Skew", justify="right", min_width=10)
#     table.add_column("CV", justify="right", min_width=10)
#     table.add_column("Mean", justify="right", min_width=12)
#     table.add_column("Std", justify="right", min_width=12)
#     table.add_column("Min", justify="right", min_width=12)
#     table.add_column("Max", justify="right", min_width=12)

#     for f in features:
#         fs = analyzer.meta[f]
#         table.add_row(
#             f,
#             colorize(fs.outlier_ratio, "outlier_ratio"),
#             colorize(fs.skew, "skew"),
#             colorize(fs.cv, "cv"),
#             fmt(fs.mean),
#             fmt(fs.std),
#             fmt(fs.min),
#             fmt(fs.max),
#         )

#     console.print("\n[bold cyan]Outlier Overview[/bold cyan]\n")
#     console.print(table)
#     console.print()

#     # --- Panels ---
#     panels = []
#     for feat in features:
#         fs = analyzer.meta[feat]
#         cfg = cfgs[feat]
#         params = cfg.get("params", {})

#         # Shorten title
#         title = cfg["meta"].get("title", feat)
#         if " - Outlier distribution" in title:
#             title = title.replace(" - Outlier distribution", "")

#         t = Table(box=box.MINIMAL, expand=True)
#         t.add_column("Metric", justify="right", style="cyan", no_wrap=True)
#         t.add_column("Value", justify="left", min_width=24)

#         rows = [
#             ("Mean", fmt(fs.mean, 4)),
#             ("Std", fmt(fs.std, 4)),
#             ("Var", fmt(fs.variance, 4)),
#             ("Skew", colorize(fs.skew, "skew")),
#             ("CV", colorize(fs.cv, "cv")),
#             ("CVr", colorize(fs.cv_robust, "cv")),
#             ("Outliers%", colorize(fs.outlier_ratio, "outlier_ratio")),
#             ("Outlier count", fmt(fs.outliers, 4)),
#             ("IQR", fmt(fs.iqr, 4)),
#             ("Q25", fmt(fs.q25, 4)),
#             ("Q75", fmt(fs.q75, 4)),
#             ("Min", fmt(fs.min, 4)),
#             ("Max", fmt(fs.max, 4)),
#         ]

#         for label, val in rows:
#             t.add_row(label, val)

#         panels.append(
#             Panel(
#                 t,
#                 title=f"[bold white]{title}[/bold white]",
#                 border_style="bright_blue",
#                 width=32,
#                 padding=(0, 0),
#             )
#         )

#         # === Plot ===
#         if plots:
#             fig, ax = plt.subplots(figsize=(3.5, 2.3))
#             sns.boxplot(
#                 x=analyzer.df[feat].dropna(),
#                 whis=params.get("whis", 1.5),
#                 showfliers=params.get("showfliers", True),
#                 notch=params.get("notch", True),
#                 color="#4e79a7",
#                 ax=ax,
#             )
#             ax.set_title(title, fontsize=8)
#             plt.tight_layout()
#             fig.savefig(f"_tmp_plots/{feat}_outliers.png", bbox_inches="tight")
#             plt.close(fig)

#     console.print("\n[bold cyan]Outlier Details[/bold cyan]\n")

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
#             cfg = cfgs[feat]
#             params = cfg.get("params", {})
#             sns.boxplot(
#                 x=analyzer.df[feat].dropna(),
#                 whis=params.get("whis", 1.5),
#                 showfliers=params.get("showfliers", True),
#                 notch=params.get("notch", True),
#                 color="#4e79a7",
#                 ax=axes[j],
#             )
#             axes[j].set_title(cfg["meta"].get("title", feat), fontsize=13)
#         plt.tight_layout()
#         plt.show()
