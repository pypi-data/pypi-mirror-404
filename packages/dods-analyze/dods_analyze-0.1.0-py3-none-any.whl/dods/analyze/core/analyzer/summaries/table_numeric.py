# dods/analyze/core/analyzer/summaries/table_numeric.py

"""
Compact numeric feature summary (top variance or full overview)
"""

from rich.table import Table
from rich import box
from dods.analyze.core.utils.color_utils import fmt_number, colorize_dynamic
from dods.analyze.core.utils.common_flags import render_flag_legend, format_flags


def render(console, analyzer, limit=10):
    meta_df = analyzer.get_meta_df()
    if meta_df.empty:
        return

    df_num = meta_df.query("is_numeric")
    if df_num.empty:
        return

    thresholds = analyzer.thresholds_by_type["numeric"]
    df_num = df_num.sort_values("missing_pct", ascending=False).head(limit)

    console.print("\n[bold cyan]📊 Numeric Overview[/bold cyan]")
    render_flag_legend(console, "numeric")

    tbl = Table(box=box.ROUNDED)
    tbl.add_column("Feature", style="bold")
    tbl.add_column("Mean", justify="right")
    tbl.add_column("Std", justify="right")
    tbl.add_column("Skew", justify="right")
    tbl.add_column("Outlier %", justify="right")
    tbl.add_column("Missing %", justify="right")
    tbl.add_column("Flags", justify="center")

    for _, r in df_num.iterrows():
        tbl.add_row(
            str(r["name"]),
            fmt_number(r["mean"]),
            fmt_number(r["std"]),
            colorize_dynamic(r["skew"], "skew", thresholds),
            colorize_dynamic(
                r["outlier_ratio"], "outlier_ratio", thresholds,
                fmt_func=lambda v: f"{v:.2f}%"
            ),
            colorize_dynamic(
                r["missing_pct"], "missing_pct", thresholds,
                fmt_func=lambda v: f"{v:.2f}%"
            ),
            format_flags(r.get("flag", {}), "numeric"),
        )

    console.print(tbl)
