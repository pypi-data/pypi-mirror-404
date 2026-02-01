# dods/analyze/core/analyzer/summaries/dataset_summary.py
"""
Dataset Overview — high-level structural summary.
Shows size, types, duplicates, memory, and missing values.
"""

import pandas as pd
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from dods.analyze.core.utils.color_utils import fmt_number


def render(console, analyzer):
    df = analyzer.df
    info = analyzer.info or {}

    # --- Base counts ---------------------------------------------------
    n_rows = len(df)
    n_cols = len(df.columns)
    n_numeric = sum(fs.is_numeric for fs in analyzer.meta.values()) if analyzer.meta else 0
    n_categorical = sum(fs.is_categorical for fs in analyzer.meta.values()) if analyzer.meta else 0
    n_datetime = sum(fs.is_datetime for fs in analyzer.meta.values()) if analyzer.meta else 0
    n_duplicates = int(df.duplicated().sum())
    dup_pct = (n_duplicates / n_rows * 100) if n_rows else 0.0

    # --- Missing summary -----------------------------------------------
    total_missing = info.get("missing_total", int(df.isna().sum().sum()))
    missing_pct = info.get("missing_pct", total_missing / (n_rows * n_cols) * 100)

    # --- Memory usage --------------------------------------------------
    mem_mb = info.get("memory_usage_mb", df.memory_usage(deep=True).sum() / 1e6)

    # --- Build summary table -------------------------------------------
    tbl = Table.grid(expand=True)
    tbl.add_column(justify="right", ratio=1)
    tbl.add_column(justify="left", ratio=4)

    tbl.add_row(
        "[bold white]Rows[/bold white]",
        f"{n_rows:,}   [dim](+{n_duplicates:,} duplicates → {dup_pct:.2f}%)[/dim]",
    )
    tbl.add_row("[bold white]Columns[/bold white]", f"{n_cols:,}")
    tbl.add_row(
        "[bold white]Types[/bold white]",
        f"Numeric: {n_numeric} | Categorical: {n_categorical} | Datetime: {n_datetime}",
    )
    tbl.add_row("[bold white]Missing[/bold white]", f"{total_missing:,}  ({missing_pct:.2f}%)")
    tbl.add_row("[bold white]Memory[/bold white]", f"{mem_mb:.2f} MB")

    # --- Data type overview (top 5 dtypes) ------------------------------
    dtype_counts = df.dtypes.value_counts().head(5)
    dtype_str = " | ".join(f"{k}: {v}" for k, v in dtype_counts.items())
    tbl.add_row("[bold white]Top dtypes[/bold white]", dtype_str)

    # --- Final panel ----------------------------------------------------
    console.print(Panel(tbl, title="📊 Dataset Overview", border_style="cyan", box=box.ROUNDED))
