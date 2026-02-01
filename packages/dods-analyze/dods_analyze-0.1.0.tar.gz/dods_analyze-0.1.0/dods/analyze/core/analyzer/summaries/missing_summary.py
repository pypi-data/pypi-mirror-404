# dods/analyze/core/analyzer/summaries/missing_summary.py

"""
Missing value overview — column + row-level view with simple recommendations.
"""

import pandas as pd
from rich.table import Table
from rich import box


def render(console, analyzer):
    df = analyzer.df
    missing_counts = df.isna().sum()
    total_missing = int(missing_counts.sum())
    missing_cols = (missing_counts > 0).sum()
    n_rows = len(df)

    if total_missing == 0:
        console.print("[green]✅ No missing values detected.[/green]")
        return

    missing_pct = (total_missing / (n_rows * len(df.columns))) * 100
    top_missing = missing_counts.sort_values(ascending=False).head(5)

    tbl = Table(title=f"🩹 Missing Summary (total {missing_cols} cols)", box=box.ROUNDED)
    tbl.add_column("Feature")
    tbl.add_column("Missing #", justify="right")
    tbl.add_column("Missing %", justify="right")
    tbl.add_column("Recommendation")

    for col, miss in top_missing.items():
        pct = miss / n_rows * 100
        if pct > 40:
            rec = "🚫 Drop or review"
        elif pct > 10:
            rec = "⚠️ Impute / check cause"
        else:
            rec = "ℹ️ Negligible"
        tbl.add_row(col, f"{miss:,}", f"{pct:.2f}%", rec)

    console.print(tbl)
