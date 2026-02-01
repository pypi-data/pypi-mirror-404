# dods/analyze/core/analyzer/summaries/table_categorical.py

"""
Compact categorical feature summary with dominance, entropy and unique ratios.
"""

from rich.table import Table
from rich import box
from dods.analyze.core.utils.color_utils import fmt_number, colorize_dynamic
from dods.analyze.core.utils.common_flags import render_flag_legend, format_flags


def render(console, analyzer, limit=10):
    meta_df = analyzer.get_meta_df()
    if meta_df.empty:
        return

    df_cat = meta_df.query("is_categorical")
    if df_cat.empty:
        return

    thresholds = analyzer.thresholds_by_type["categorical"]
    df_cat = df_cat.sort_values("dominance", ascending=False).head(limit)

    console.print("\n[bold cyan]🔤 Categorical Overview[/bold cyan]")
    render_flag_legend(console, "categorical")

    tbl = Table(box=box.ROUNDED)
    tbl.add_column("Feature", style="bold")
    tbl.add_column("Unique %", justify="right")
    tbl.add_column("Dominance", justify="right")
    tbl.add_column("Entropy", justify="right")
    tbl.add_column("Top Value", justify="left")
    tbl.add_column("Flags", justify="center")

    for _, r in df_cat.iterrows():
        top_val = "-"
        if isinstance(r.get("top_values"), dict) and len(r["top_values"]) > 0:
            k, v = next(iter(r["top_values"].items()))
            top_val = f"{k} ({v})"

        tbl.add_row(
            str(r["name"]),
            colorize_dynamic(
                r["unique_pct"], "unique_pct", thresholds,
                fmt_func=lambda v: f"{v:.1f}%"
            ),
            colorize_dynamic(
                r["dominance"], "dominance", thresholds,
                fmt_func=lambda v: f"{v:.2f}"
            ),
            colorize_dynamic(
                r["entropy"], "entropy", thresholds,
                fmt_func=lambda v: f"{v:.2f}"
            ),
            top_val,
            format_flags(r.get("flag", {}), "categorical"),
        )

    console.print(tbl)
