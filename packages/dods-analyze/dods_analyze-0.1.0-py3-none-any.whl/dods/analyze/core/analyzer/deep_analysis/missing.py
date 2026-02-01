# # dods/analyze/core/analyzer/deep_analysis/missing.py
"""
🩹 Missing Value Analyzer v2
----------------------------
Layered Analysis:
  1️⃣ Summary (global + per-feature)
  2️⃣ Row-wise and structural patterns
  3️⃣ Visual diagnostics (barplot, histogram, heatmaps)
  4️⃣ Recommendations
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


# ======================================================================
# MAIN ENTRY
# ======================================================================
def analyze_missing(analyzer, show_plots: bool = True, top_n: int = 10):
    console = Console()
    df = analyzer.df

    console.rule("[bold bright_cyan]🩹 Missing Value Analysis[/bold bright_cyan]")

    # ------------------------------------------------------------------
    # 1️⃣ Summary Layer
    # ------------------------------------------------------------------
    missing_counts = df.isna().sum()
    missing_pct = (missing_counts / len(df)) * 100
    missing_df = pd.DataFrame({
        "Feature": df.columns,
        "Missing (%)": missing_pct.round(2),
        "Missing #": missing_counts,
        "Type": [str(df[c].dtype) for c in df.columns]
    })
    missing_df = missing_df[missing_df["Missing #"] > 0].sort_values("Missing (%)", ascending=False)

    total_missing = int(missing_counts.sum())
    n_cols_missing = (missing_counts > 0).sum()
    mean_missing_pct = missing_pct.mean()

    console.print(
        f"[cyan]Summary:[/cyan]\n"
        f"Rows: [white]{len(df)}[/white] | "
        f"Columns with missing: [white]{n_cols_missing}/{df.shape[1]}[/white] | "
        f"Total missing values: [white]{total_missing:,}[/white] "
        f"([white]{mean_missing_pct:.2f}%[/white] mean per col)\n"
    )

    # Display top features
    if not missing_df.empty:
        top_features = missing_df.head(top_n)
        tbl = Table(title=f"Top Columns by Missing Percentage", box=box.ROUNDED)
        tbl.add_column("Feature")
        tbl.add_column("Missing (%)", justify="right")
        tbl.add_column("Missing #", justify="right")
        tbl.add_column("Type", justify="center")
        for _, row in top_features.iterrows():
            tbl.add_row(
                str(row["Feature"]),
                f"{row['Missing (%)']:.2f}",
                f"{int(row['Missing #']):,}",
                row["Type"],
            )
        console.print(tbl)

    # ------------------------------------------------------------------
    # 2️⃣ Row-wise & Structural Patterns
    # ------------------------------------------------------------------
    row_missing = df.isna().sum(axis=1)
    row_missing_pct = row_missing / df.shape[1] * 100
    high_missing_rows = (row_missing_pct > 50).sum()

    console.print(
        f"[grey50]Row-wise summary:[/grey50] "
        f"{high_missing_rows} rows have >50% missing values "
        f"({row_missing_pct.mean():.2f}% avg per row)\n"
    )

    # Co-missing correlation (Feature vs Feature)
    mask = df.isna().astype(int)
    if mask.shape[1] > 1:
        co_corr = mask.corr()
    else:
        co_corr = None

    # ------------------------------------------------------------------
    # 3️⃣ Visualization Layer
    # ------------------------------------------------------------------
    if show_plots:
        sns.set_style("whitegrid")
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("🩹 Missing Value Patterns", fontsize=13, fontweight="bold")

        # (1) Barplot – Missing % per feature (Top N)
        sns.barplot(
            x="Missing (%)",
            y="Feature",
            data=missing_df.head(top_n),
            ax=axes[0, 0],
            palette="Reds_r"
        )
        axes[0, 0].set_title("Top Missing Features", fontsize=11)

        # (2) Histogram – Missing Columns per Row
        sns.histplot(row_missing, bins=25, ax=axes[0, 1], color="#e67e22")
        axes[0, 1].set_title("Missing Columns per Row", fontsize=11)
        axes[0, 1].set_xlabel("# Missing Columns")
        axes[0, 1].set_ylabel("Row Count")

        # (3) Co-Missing Correlation Heatmap
        if co_corr is not None and len(co_corr) > 1:
            sns.heatmap(co_corr, cmap="mako", ax=axes[1, 0],
                        vmin=0, vmax=1, square=True, cbar_kws={"label": "Co-Missing Corr"})
            axes[1, 0].set_title("Co-Missing Feature Correlation", fontsize=11)
        else:
            axes[1, 0].axis("off")

        # (4) Missing Pattern Heatmap (Feature × Row, subsampled)
        sample_mask = mask.sample(min(len(mask), 200), random_state=42)
        sns.heatmap(sample_mask.T, cmap="coolwarm", cbar=False, ax=axes[1, 1])
        axes[1, 1].set_title("Missingness Pattern (Sample 200 Rows)", fontsize=11)
        axes[1, 1].set_xlabel("Rows")
        axes[1, 1].set_ylabel("Features")

        plt.tight_layout()
        plt.show()

    # ------------------------------------------------------------------
    # 4️⃣ Recommendations Layer
    # ------------------------------------------------------------------
    recs = []
    if mean_missing_pct < 5:
        recs.append("✅ Low average missingness – dataset generally complete.")
    if (missing_pct > 30).any():
        bad = missing_pct[missing_pct > 30]
        recs.append(f"🚫 {len(bad)} feature(s) >30% missing: consider dropping or flagging.")
    if (missing_pct.between(10, 30)).any():
        mid = missing_pct[missing_pct.between(10, 30)]
        recs.append(f"⚠️ {len(mid)} moderately incomplete feature(s): consider imputation.")
    if high_missing_rows > 0:
        recs.append(f"🧱 {high_missing_rows} rows >50% missing – consider row removal.")
    if co_corr is not None and (co_corr.values[np.triu_indices_from(co_corr, 1)] > 0.7).any():
        recs.append("🔗 strong co-missing patterns detected – check structural dependencies.")

    console.print(Panel("\n".join(recs) if recs else "No notable issues.", title="[bold yellow]Recommendations[/bold yellow]"))

    console.rule("[green]End of Missing Analysis[/green]")

    return {
        "missing_summary": missing_df,
        "row_missing": row_missing,
        "co_missing_corr": co_corr,
        "recommendations": recs,
    }




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
#     "missing": (5, 20),   # yellow >5%, red >20%
#     "unique": (10, 2),    # low uniqueness = warning
# }


# # -------------------------------
# # Helper: color formatting
# # -------------------------------
# def colorize(value, kind):
#     if value is None:
#         return "-"
#     low, high = COLOR_THRESHOLDS.get(kind, (None, None))
#     if kind == "missing":
#         if value > high:
#             return f"[bold red]{value:.3g}%[/bold red]"
#         elif value > low:
#             return f"[yellow]{value:.3g}%[/yellow]"
#         return f"{value:.3g}%"
#     if kind == "unique":
#         if value < high:
#             return f"[bold red]{value:.2f}%[/bold red]"
#         elif value < low:
#             return f"[yellow]{value:.2f}%[/yellow]"
#         return f"{value:.2f}%"
#     return str(value)


# # -------------------------------
# # Main: analyze_missing
# # -------------------------------
# def analyze_missing(analyzer, limit=None, columns=None, plots=True, order="most_missing"):
#     if not hasattr(analyzer, "meta"):
#         console.print("[red]⚠️ Analyzer not initialized. Run .analyze() first.[/red]")
#         return

#     info = analyzer.info
#     console.print(
#         f"[bold cyan]📊 Data Summary[/bold cyan]\n"
#         f"Rows: [white]{info['n_rows']}[/white] | "
#         f"Columns: [white]{info['n_columns']}[/white] | "
#         f"Missing total: [white]{info['missing_total']:,}[/white] "
#         f"({info['missing_pct']:.2f}%) | "
#         f"Memory: [white]{info['memory_usage_mb']:.2f} MB[/white]\n"
#     )

#     # --- Feature selection ---
#     if columns:
#         features = [c for c in columns if c in analyzer.meta]
#     else:
#         features = list(analyzer.meta.keys())

#     # --- Sort by missing percentage ---
#     if order == "most_missing":
#         features.sort(key=lambda f: analyzer.meta[f].missing_pct or 0, reverse=True)
#     else:
#         features.sort()

#     if limit:
#         features = features[:limit]

#     # --- Overview Table ---
#     table = Table(box=box.SIMPLE_HEAVY, expand=True, pad_edge=False, padding=(0, 0))
#     table.add_column("Feature", style="bold white", min_width=25, overflow="fold")
#     table.add_column("Type", justify="left", min_width=10)
#     table.add_column("Missing%", justify="right", min_width=10)
#     table.add_column("Unique%", justify="right", min_width=10)
#     table.add_column("Non-null", justify="right", min_width=10)
#     table.add_column("Flags", justify="left", min_width=20)

#     for f in features:
#         fs = analyzer.meta[f]
#         table.add_row(
#             f,
#             str(fs.type),
#             colorize(fs.missing_pct or 0, "missing"),
#             colorize(fs.unique_pct or 0, "unique"),
#             f"{fs.n_non_null:,}",
#             ", ".join(fs.flag or []),
#         )

#     console.print("\n[bold cyan]Missing Value Overview[/bold cyan]\n")
#     console.print(table)
#     console.print()

#     # --- Panels ---
#     panels = []
#     for feat in features:
#         fs = analyzer.meta[feat]
#         n_missing = int(info['n_rows'] * (fs.missing_pct or 0) / 100)

#         t = Table(box=box.MINIMAL, expand=True)
#         t.add_column("Metric", justify="right", style="cyan", no_wrap=True)
#         t.add_column("Value", justify="left", min_width=24)

#         rows = [
#             ("Type", str(fs.type)),
#             ("Missing%", colorize(fs.missing_pct or 0, "missing")),
#             ("Missing count", f"{n_missing:4g}"),
#             ("Unique%", colorize(fs.unique_pct or 0, "unique")),
#             ("Non-null", f"{fs.n_non_null:4g}"),
#             ("Flags", ", ".join(fs.flag or [])),
#         ]

#         for label, val in rows:
#             t.add_row(label, val)

#         panels.append(
#             Panel(
#                 t,
#                 title=f"[bold white]{feat}[/bold white]",
#                 border_style="bright_blue",
#                 width=28,
#                 padding=(0, 0),
#             )
#         )

#     console.print("\n[bold cyan]Missing Detail Panels[/bold cyan]\n")

#     # --- Render 3 per row + missing plots ---
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
#             missing_mask = analyzer.df[feat].isna()
#             sns.histplot(
#                 missing_mask.astype(int),
#                 bins=2,
#                 color="#4e79a7",
#                 ax=ax,
#                 discrete=True,
#             )
#             ax.set_title(f"{feat} (missing%)", fontsize=13)
#             ax.set_xticks([0, 1])
#             ax.set_xticklabels(["Present", "Missing"])
#             ax.set_ylabel("Count")
#         plt.tight_layout()
#         plt.show()
