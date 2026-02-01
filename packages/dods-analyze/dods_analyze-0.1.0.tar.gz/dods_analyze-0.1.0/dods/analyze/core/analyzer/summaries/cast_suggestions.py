# dods/analyze/core/analyzer/summaries/cast_suggestions.py
"""
Suggested data type casts — highlights columns where dtype inference found mismatch.
"""

from rich.table import Table
from rich import box


def render(console, analyzer, limit=10):
    meta_df = analyzer.get_meta_df()
    if meta_df.empty:
        return

    df_cast = meta_df[meta_df["cast_suggestion"].notna()]
    if df_cast.empty:
        return

    df_cast = df_cast.head(limit)

    tbl = Table(title="🧩 Cast Suggestions", box=box.ROUNDED)
    tbl.add_column("Feature", style="bold")
    tbl.add_column("Current Type")
    tbl.add_column("Suggested Type")

    for _, r in df_cast.iterrows():
        tbl.add_row(str(r["name"]), str(r["dtype_inferred"]), str(r["cast_suggestion"]))

    console.print(tbl)
