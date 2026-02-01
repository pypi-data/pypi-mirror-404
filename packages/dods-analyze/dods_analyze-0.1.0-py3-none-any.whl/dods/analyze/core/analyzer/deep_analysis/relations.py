
# dods/analyze/core/analyzer/deep_analysis/relations.py
# dods/analyze/core/analyzer/deep_analysis/relations.py
"""
Feature Relationship Analyzer — v4.1
------------------------------------
Refined version with:
- Robust NaN and empty-frame handling
- User feedback when plots/tables are skipped
- Defensive correlation logic
- Clean modular structure
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
def analyze_relations(
    analyzer,
    limit: int = 100,
    sort_metric: str = "max_combined",
    show_plots: bool = True,
    force_heatmaps: bool = False,
):
    console = Console()
    rel = analyzer.relations or {}
    info = analyzer.info or {}

    # ---------------------------------------------------------------
    # Defensive extraction
    # ---------------------------------------------------------------
    pearson = rel.get("pearson", pd.DataFrame())
    spearman = rel.get("spearman", pd.DataFrame())
    mi = rel.get("mi", pd.DataFrame())
    groups = rel.get("groups", {})
    pairs = rel.get("pairs", pd.DataFrame())
    iso = rel.get("isolated", [])
    summary = rel.get("summary", {})

    # 🔧 Convert list of dicts (from RelationClassifier) to DataFrame
    if isinstance(pairs, list):
        try:
            pairs = pd.DataFrame(pairs)
        except Exception as e:
            console.print(f"[red]Failed to convert pairs to DataFrame:[/red] {e}")
            pairs = pd.DataFrame()


    if not rel:
        console.print("[red]No relations found. Run RelationEngine first.[/red]")
        return None

    console.rule("[bold bright_cyan]🔍 Feature Relationship Analysis[/bold bright_cyan]")

    # ------------------------------------------------------------------
    # 0️⃣ Dataset overview
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 1️⃣ Summary block
    # ------------------------------------------------------------------
    _show_summary(console, summary)

    # ------------------------------------------------------------------
    # 2️⃣ Insights
    # ------------------------------------------------------------------
    insights, _ = _generate_insights(summary, iso)
    insight_text = "\n".join(insights) if insights else "No notable findings."
    console.print(Panel(insight_text, title="[bold yellow]🧠 Insights[/bold yellow]", expand=False))

    # ------------------------------------------------------------------
    # 3️⃣ Dominant features (Pearson + MI)
    # ------------------------------------------------------------------
    if isinstance(pearson, pd.DataFrame) and not pearson.empty:
        _show_dominant_features(console, pearson, mi)

    # ------------------------------------------------------------------
    # 4️⃣ Isolated features
    # ------------------------------------------------------------------
    if iso:
        console.print(
            Panel(
                f"[cyan]{len(iso)} isolated features[/cyan]: "
                + ", ".join(iso)
                + "\n[grey50]→ likely IDs, timestamps, or unique dimensions[/grey50]",
                title="[bold magenta]Isolated Features[/bold magenta]",
                expand=False,
            )
        )

    # ------------------------------------------------------------------
    # 5️⃣ Distributions (Pearson / Spearman / MI)
    # ------------------------------------------------------------------
    if show_plots and isinstance(pearson, pd.DataFrame) and not pearson.empty:
        _plot_distributions(pearson, spearman, mi)

    # ------------------------------------------------------------------
    # 6️⃣ Correlated Feature Pairs
    # ------------------------------------------------------------------
    if isinstance(pairs, pd.DataFrame) and not pairs.empty:
        console.print(
            "[bright_black]Flag legend:[/bright_black] "
            "[cyan]IDX[/cyan]=index-like  "
            "[yellow]SKEW[/yellow]=skewed  "
            "[magenta]OUT[/magenta]=outlier-heavy  "
            "[white]CONST[/white]=constant\n"
        )
        _show_pairs_table(console, pairs, limit=limit, sort_metric=sort_metric)
        if limit:
            console.print("[grey50]Showing top pairs only. Use limit=None for full list.[/grey50]\n")
    else:
        console.print("[grey50]No correlated feature pairs available to display.[/grey50]\n")

    # ------------------------------------------------------------------
    # 7️⃣ Redundancy Groups
    # ------------------------------------------------------------------
    if groups:
        _show_groups(console, groups)
    else:
        console.print("[grey50]No redundancy groups detected.[/grey50]\n")

    # ------------------------------------------------------------------
    # 8️⃣ Global Heatmaps
    # ------------------------------------------------------------------
    if show_plots:
        _plot_heatmaps(console, pearson, mi, force_heatmaps)


# ======================================================================
# SUMMARY
# ======================================================================
def _show_summary(console: Console, summary: dict):
    t = Table(title="[bold bright_white]📈 Relation Summary[/bold bright_white]", box=box.SIMPLE_HEAVY)
    t.add_column("Metric")
    t.add_column("Value", justify="right")

    def fmt(v):
        return f"{v:.3f}" if isinstance(v, (float, np.floating)) else str(v)

    t.add_row("Features analyzed", str(summary.get("n_features", "?")))
    t.add_row("Pearson groups", str(summary.get("n_groups_pearson", 0)))
    t.add_row("MI groups", str(summary.get("n_groups_mi", 0)))
    t.add_row("Isolated features", str(summary.get("n_isolated", 0)))
    t.add_row("Avg |r|", fmt(summary.get("avg_abs_corr", np.nan)))
    t.add_row("Strong-rel density", fmt(summary.get("strong_rel_density", np.nan)))
    console.print(t)


# ======================================================================
# Insights
# ======================================================================
def _generate_insights(summary: dict, iso: list[str]):
    msgs = []
    if summary.get("avg_abs_corr", 0) < 0.2:
        msgs.append("✅ Low average correlation — features are largely independent.")
    if summary.get("strong_rel_density", 0) > 0.5:
        msgs.append("⚠️ High inter-correlation density — redundancy likely.")
    if iso:
        msgs.append(f"🧩 {len(iso)} isolated features — likely IDs or timestamps.")
    return msgs, iso


# ======================================================================
# Distributions
# ======================================================================
def _plot_distributions(pearson, spearman, mi):
    fig, axes = plt.subplots(1, 3, figsize=(13, 3))
    metrics = [
        ("|Pearson r|", pearson),
        ("|Spearman ρ|", spearman),
        ("Mutual Information", mi),
    ]
    for ax, (label, df) in zip(axes, metrics):
        if df is None or df.empty:
            ax.axis("off")
            continue
        tri = df.where(np.triu(np.ones(df.shape), 1).astype(bool)).stack().abs()
        if tri.empty:
            ax.axis("off")
            continue
        sns.histplot(tri, bins=25, ax=ax, color="#3498db")
        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel("")
    plt.suptitle("Distributions of Feature Relationships", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.show()


# ======================================================================
# Heatmaps
# ======================================================================
def _plot_heatmaps(console, pearson, mi, force):
    if isinstance(pearson, pd.DataFrame) and not pearson.empty:
        valid_features = pearson.columns[pearson.notna().any(axis=0)]
        pearson_plot = pearson.loc[valid_features, valid_features]
        if not pearson_plot.empty and (len(pearson_plot) <= 40 or force):
            console.rule("Global Pearson Heatmap")
            plt.figure(figsize=(8, 6))
            sns.heatmap(pearson_plot, cmap="coolwarm", vmin=-1, vmax=1, square=True)
            plt.title("Global Pearson Correlation", fontsize=12, fontweight="bold")
            plt.tight_layout()
            plt.show()
        else:
            console.print("[grey50]Pearson heatmap skipped (too many features or empty).[/grey50]")

    if isinstance(mi, pd.DataFrame) and not mi.empty:
        if len(mi) <= 40 or force:
            console.rule("Global Mutual Information Heatmap")
            plt.figure(figsize=(8, 6))
            sns.heatmap(mi, cmap="viridis", vmin=0, vmax=mi.max().max(), square=True)
            plt.title("Global Mutual Information", fontsize=12, fontweight="bold")
            plt.tight_layout()
            plt.show()
        else:
            console.print("[grey50]Mutual Information heatmap skipped (too many features or empty).[/grey50]")


# ======================================================================
# Dominant Features
# ======================================================================
def _show_dominant_features(console: Console, pearson: pd.DataFrame, mi: pd.DataFrame | None):
    def table_from_matrix(df: pd.DataFrame, title: str):
        if df is None or df.empty or df.isna().all().all():
            console.print(f"[grey50]No valid data for {title}[/grey50]")
            return Table()

        abs_corr = df.abs()
        connectivity = (abs_corr > 0.6).sum(axis=1)
        top = connectivity.sort_values(ascending=False).head(8)

        tbl = Table(title=title, box=box.MINIMAL_HEAVY_HEAD)
        tbl.add_column("Feature", justify="left")
        tbl.add_column("Links", justify="right")
        tbl.add_column("Strongest Link", justify="left")
        tbl.add_column("Max", justify="right")
        tbl.add_column("Avg", justify="right")

        for f in top.index:
            row = abs_corr.loc[f].dropna()
            row_wo_self = row.drop(f, errors="ignore")
            if row_wo_self.empty:
                continue
            strongest = row_wo_self.idxmax()
            max_v = abs_corr.loc[f, strongest]
            avg_v = row.mean()
            tbl.add_row(f, str(int(connectivity.get(f, 0))), strongest, f"{max_v:.2f}", f"{avg_v:.2f}")

        return tbl

    tbl_p = table_from_matrix(pearson, "🏆 Dominant (Pearson r)")
    tbl_m = table_from_matrix(mi, "🏆 Dominant (Mutual Information)") if mi is not None and not mi.empty else None

    if len(tbl_p.rows):
        console.print(tbl_p)
    else:
        console.print("[grey50]No dominant Pearson correlations found.[/grey50]")

    if tbl_m and len(tbl_m.rows):
        console.print(tbl_m)
    elif mi is not None and not mi.empty:
        console.print("[grey50]No dominant MI correlations found.[/grey50]")


# ======================================================================
# Correlated Feature Pairs
# ======================================================================
def _show_pairs_table(console: Console, pairs: pd.DataFrame, limit: int = 100, sort_metric: str = "max_combined"):
    if pairs.empty:
        console.print("[grey50]No correlated pairs to display.[/grey50]")
        return

    def score(row):
        if sort_metric == "max_combined":
            return max(abs(row.get("pearson", 0)), abs(row.get("spearman", 0)), row.get("mi", 0))
        return abs(row.get(sort_metric, 0))

    pairs = pairs.copy()
    pairs["_score"] = pairs.apply(score, axis=1)
    pairs_sorted = pairs.sort_values("_score", ascending=False)
    if limit:
        pairs_sorted = pairs_sorted.head(limit)

    if pairs_sorted.empty:
        console.print("[grey50]No correlated pairs found after sorting/filtering.[/grey50]")
        return

    def color_corr(v):
        if abs(v) > 0.8:
            return f"[green]{v:.2f}[/green]"
        if abs(v) > 0.5:
            return f"[yellow]{v:.2f}[/yellow]"
        if abs(v) > 0.3:
            return f"[orange1]{v:.2f}[/orange1]"
        return f"[grey58]{v:.2f}[/grey58]"

    console.rule("💫 Correlated Feature Pairs")
    tbl = Table(box=box.MINIMAL_HEAVY_HEAD)
    tbl.add_column("Feature A")
    tbl.add_column("Feature B")
    tbl.add_column("r (Pearson)", justify="right")
    tbl.add_column("ρ (Spearman)", justify="right")
    tbl.add_column("MI", justify="right")
    tbl.add_column("Type", justify="left")
    tbl.add_column("Flags", justify="left")

    for _, row in pairs_sorted.iterrows():
        flags = row.get("flags", [])
        if isinstance(flags, str):
            flags = [flags]
        flag_str = "/".join(flags) if flags else "-"
        tbl.add_row(
            str(row.get("a", "?")),
            str(row.get("b", "?")),
            color_corr(row.get("pearson", 0)),
            color_corr(row.get("spearman", 0)),
            color_corr(row.get("mi", 0)),
            row.get("type", "-"),
            flag_str,
        )
    console.print(tbl)


# ======================================================================
# Redundancy Groups
# ======================================================================
def _show_groups(console: Console, groups: dict):
    console.rule("[bold white]🔁 Redundancy Groups[/bold white]")

    def render_group_list(title: str, group_list: list[dict]):
        if not group_list:
            console.print(f"[grey50]No {title} groups detected.[/grey50]\n")
            return
        console.print(f"\n[bold cyan]{title} Groups ({len(group_list)})[/bold cyan]")
        for i, g in enumerate(group_list, start=1):
            features = g.get("features", [])
            avg_corr = g.get("avg_corr", np.nan)
            min_corr = g.get("min_corr", np.nan)
            max_corr = g.get("max_corr", np.nan)
            if not features:
                continue

            tbl = Table(
                title=f"[bold magenta]{title} Group {i}[/bold magenta]",
                box=box.SIMPLE_HEAVY,
                header_style="bold white",
            )
            tbl.add_column("Size", justify="right")
            tbl.add_column("Avg |r|", justify="right", style="green")
            tbl.add_column("Min |r|", justify="right", style="yellow")
            tbl.add_column("Max |r|", justify="right", style="red")
            tbl.add_column("Main Feature", style="cyan")
            tbl.add_column("Members", style="white")

            members_str = "\n".join(f"- {m}" for m in features)
            tbl.add_row(
                str(len(features)),
                f"{avg_corr:.2f}" if not pd.isna(avg_corr) else "-",
                f"{min_corr:.2f}" if not pd.isna(min_corr) else "-",
                f"{max_corr:.2f}" if not pd.isna(max_corr) else "-",
                features[0],
                members_str,
            )
            console.print(tbl)
            console.print()

    render_group_list("Pearson", groups.get("pearson", []))
    render_group_list("Mutual Information", groups.get("mi", []))




# """
# Feature Relationship Analyzer — compatible with RelationEngine v4
# -----------------------------------------------------------------
# Displays summary, distributions, pair tables, redundancy groups,
# and heatmaps for Pearson/Spearman/MI results.
# """

# import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# from rich.console import Console
# from rich.table import Table
# from rich.panel import Panel
# from rich import box


# # ======================================================================
# # MAIN ENTRY
# # ======================================================================
# def analyze_relations(analyzer, limit: int = 100, sort_metric: str = "max_combined", show_plots: bool = True, force_heatmaps: bool = False):
#     console = Console()
#     rel = analyzer.relations or {}
#     info = analyzer.info or {}

#     # ---------------------------------------------------------------
#     # Defensive data extraction
#     # ---------------------------------------------------------------
#     pearson = rel.get("pearson", pd.DataFrame())
#     spearman = rel.get("spearman", pd.DataFrame())
#     mi = rel.get("mi", pd.DataFrame())
#     groups = rel.get("groups", {})
#     pairs = rel.get("pairs", pd.DataFrame())
#     iso = rel.get("isolated", [])
#     summary = rel.get("summary", {})

#     if not rel:
#         console.print("[red]No relations found. Run RelationEngine first.[/red]")
#         return None

#     console.rule("[bold bright_cyan]🔍 Feature Relationship Analysis[/bold bright_cyan]")

#     # ------------------------------------------------------------------
#     # 0️⃣ Dataset overview
#     # ------------------------------------------------------------------
#     console.print(
#         f"[bold cyan]📊 Data Summary[/bold cyan]\n"
#         f"Rows: [white]{info.get('n_rows', '?')}[/white] | "
#         f"Columns: [white]{info.get('n_columns', '?')}[/white] | "
#         f"Numeric: [white]{info.get('n_numeric', '?')}[/white] | "
#         f"Categorical: [white]{info.get('n_categorical', '?')}[/white] | "
#         f"Datetime: [white]{info.get('n_datetime', '?')}[/white]\n"
#         f"Missing total: [white]{info.get('missing_total', '?')}[/white] "
#         f"({info.get('missing_pct', 0.0):.2f}%) | "
#         f"Memory: [white]{info.get('memory_usage_mb', 0.0):.2f} MB[/white]\n"
#     )

#     # ------------------------------------------------------------------
#     # 1️⃣ Summary block
#     # ------------------------------------------------------------------
#     _show_summary(console, summary)

#     # ------------------------------------------------------------------
#     # 2️⃣ Insights
#     # ------------------------------------------------------------------
#     insights, _ = _generate_insights(summary, iso)
#     insight_text = "\n".join(insights) if insights else "No notable findings."
#     console.print(Panel(insight_text, title="[bold yellow]🧠 Insights[/bold yellow]", expand=False))

#     # ------------------------------------------------------------------
#     # 3️⃣ Dominant features (Pearson + MI)
#     # ------------------------------------------------------------------
#     if isinstance(pearson, pd.DataFrame) and not pearson.empty:
#         _show_dominant_features(console, pearson, mi)

#     # ------------------------------------------------------------------
#     # 4️⃣ Isolated features
#     # ------------------------------------------------------------------
#     if iso:
#         console.print(
#             Panel(
#                 f"[cyan]{len(iso)} isolated features[/cyan]: "
#                 + ", ".join(iso)
#                 + "\n[grey50]→ likely IDs, timestamps, or unique dimensions[/grey50]",
#                 title="[bold magenta]Isolated Features[/bold magenta]",
#                 expand=False,
#             )
#         )

#     # ------------------------------------------------------------------
#     # 5️⃣ Distributions (Pearson / Spearman / MI)
#     # ------------------------------------------------------------------
#     if show_plots and isinstance(pearson, pd.DataFrame) and not pearson.empty:
#         _plot_distributions(pearson, spearman, mi)

#     # ------------------------------------------------------------------
#     # 6️⃣ Correlated Feature Pairs
#     # ------------------------------------------------------------------
#     if isinstance(pairs, pd.DataFrame) and not pairs.empty:
#         console.print(
#             "[bright_black]Flag legend:[/bright_black] "
#             "[cyan]IDX[/cyan]=index-like  "
#             "[yellow]SKEW[/yellow]=skewed  "
#             "[magenta]OUT[/magenta]=outlier-heavy  "
#             "[white]CONST[/white]=constant\n"
#         )
#         _show_pairs_table(console, pairs, limit=limit, sort_metric=sort_metric)
#         if limit:
#             console.print("[grey50]Showing top pairs only. Use limit=None for full list.[/grey50]\n")

#     # ------------------------------------------------------------------
#     # 7️⃣ Redundancy Groups
#     # ------------------------------------------------------------------
#     if groups:
#         _show_groups(console, groups)
#     else:
#         console.print("[grey50]No redundancy groups detected.[/grey50]\n")

#     # ------------------------------------------------------------------
#     # 8️⃣ Global Pearson / MI Heatmaps
#     # ------------------------------------------------------------------
#     if show_plots:
#         _plot_heatmaps(console, pearson, mi, force_heatmaps)


# # ======================================================================
# # SUMMARY
# # ======================================================================
# def _show_summary(console: Console, summary: dict):
#     t = Table(title="[bold bright_white]📈 Relation Summary[/bold bright_white]", box=box.SIMPLE_HEAVY)
#     t.add_column("Metric")
#     t.add_column("Value", justify="right")

#     def fmt(v):
#         return f"{v:.3f}" if isinstance(v, (float, np.floating)) else str(v)

#     t.add_row("Features analyzed", str(summary.get("n_features", "?")))
#     t.add_row("Pearson groups", str(summary.get("n_groups_pearson", 0)))
#     t.add_row("MI groups", str(summary.get("n_groups_mi", 0)))
#     t.add_row("Isolated features", str(summary.get("n_isolated", 0)))
#     t.add_row("Avg |r|", fmt(summary.get("avg_abs_corr", np.nan)))
#     t.add_row("Strong-rel density", fmt(summary.get("strong_rel_density", np.nan)))
#     console.print(t)


# # ======================================================================
# # Insights
# # ======================================================================
# def _generate_insights(summary: dict, iso: list[str]):
#     msgs = []
#     if summary.get("avg_abs_corr", 0) < 0.2:
#         msgs.append("✅ Low average correlation — features are largely independent.")
#     if summary.get("strong_rel_density", 0) > 0.5:
#         msgs.append("⚠️ High inter-correlation density — redundancy likely.")
#     if iso:
#         msgs.append(f"🧩 {len(iso)} isolated features — likely IDs or timestamps.")
#     return msgs, iso


# # ======================================================================
# # Distributions
# # ======================================================================
# def _plot_distributions(pearson, spearman, mi):
#     fig, axes = plt.subplots(1, 3, figsize=(13, 3))
#     metrics = [
#         ("|Pearson r|", pearson),
#         ("|Spearman ρ|", spearman),
#         ("Mutual Information", mi),
#     ]
#     for ax, (label, df) in zip(axes, metrics):
#         if df is None or df.empty:
#             ax.axis("off")
#             continue
#         tri = df.where(np.triu(np.ones(df.shape), 1).astype(bool)).stack().abs()
#         sns.histplot(tri, bins=25, ax=ax, color="#3498db")
#         ax.set_title(label, fontsize=11, fontweight="bold")
#         ax.set_xlabel("")
#         ax.set_ylabel("")
#     plt.suptitle("Distributions of Feature Relationships", fontsize=13, fontweight="bold")
#     plt.tight_layout()
#     plt.show()


# # ======================================================================
# # Heatmaps
# # ======================================================================
# def _plot_heatmaps(console, pearson, mi, force):
#     if isinstance(pearson, pd.DataFrame) and not pearson.empty:
#         valid_features = pearson.columns[pearson.notna().any(axis=0)]
#         pearson_plot = pearson.loc[valid_features, valid_features]
#         if not pearson_plot.empty and (len(pearson_plot) <= 40 or force):
#             console.rule("Global Pearson Heatmap")
#             plt.figure(figsize=(8, 6))
#             sns.heatmap(pearson_plot, cmap="coolwarm", vmin=-1, vmax=1, square=True)
#             plt.title("Global Pearson Correlation", fontsize=12, fontweight="bold")
#             plt.tight_layout()
#             plt.show()

#     if isinstance(mi, pd.DataFrame) and not mi.empty and (len(mi) <= 40 or force):
#         console.rule("Global Mutual Information Heatmap")
#         plt.figure(figsize=(8, 6))
#         sns.heatmap(mi, cmap="viridis", vmin=0, vmax=mi.max().max(), square=True)
#         plt.title("Global Mutual Information", fontsize=12, fontweight="bold")
#         plt.tight_layout()
#         plt.show()


# # ======================================================================
# # Dominant Features
# # ======================================================================
# def _show_dominant_features(console: Console, pearson: pd.DataFrame, mi: pd.DataFrame | None):
#     def table_from_matrix(df: pd.DataFrame, title: str):
#         if df is None or df.empty:
#             console.print(f"[grey50]No valid data for {title}[/grey50]")
#             return Table()

#         abs_corr = df.abs()
#         connectivity = (abs_corr > 0.6).sum(axis=1)
#         top = connectivity.sort_values(ascending=False).head(8)

#         tbl = Table(title=title, box=box.MINIMAL_HEAVY_HEAD)
#         tbl.add_column("Feature", justify="left")
#         tbl.add_column("Links", justify="right")
#         tbl.add_column("Strongest Link", justify="left")
#         tbl.add_column("Max", justify="right")
#         tbl.add_column("Avg", justify="right")

#         for f in top.index:
#             row = abs_corr.loc[f].dropna()
#             row_wo_self = row.drop(f, errors="ignore")
#             if row_wo_self.empty:
#                 continue
#             strongest = row_wo_self.idxmax()
#             max_v = abs_corr.loc[f, strongest]
#             avg_v = row.mean()
#             tbl.add_row(f, str(int(connectivity.get(f, 0))), strongest, f"{max_v:.2f}", f"{avg_v:.2f}")

#         return tbl

#     tbl_p = table_from_matrix(pearson, "🏆 Dominant (Pearson r)")
#     tbl_m = table_from_matrix(mi, "🏆 Dominant (Mutual Information)") if mi is not None and not mi.empty else None
#     if len(tbl_p.rows):
#         console.print(tbl_p)
#     if tbl_m and len(tbl_m.rows):
#         console.print(tbl_m)


# # ======================================================================
# # Pairs Table
# # ======================================================================
# def _show_pairs_table(console: Console, pairs: pd.DataFrame, limit: int = 100, sort_metric: str = "max_combined"):
#     def score(row):
#         if sort_metric == "max_combined":
#             return max(abs(row["pearson"]), abs(row["spearman"]), row["mi"])
#         return abs(row.get(sort_metric, 0))

#     pairs = pairs.copy()
#     pairs["_score"] = pairs.apply(score, axis=1)
#     pairs_sorted = pairs.sort_values("_score", ascending=False)
#     if limit:
#         pairs_sorted = pairs_sorted.head(limit)

#     def color_corr(v):
#         if abs(v) > 0.8:
#             return f"[green]{v:.2f}[/green]"
#         if abs(v) > 0.5:
#             return f"[yellow]{v:.2f}[/yellow]"
#         if abs(v) > 0.3:
#             return f"[orange1]{v:.2f}[/orange1]"
#         return f"[grey58]{v:.2f}[/grey58]"

#     console.rule("💫 Correlated Feature Pairs")
#     tbl = Table(box=box.MINIMAL_HEAVY_HEAD)
#     tbl.add_column("Feature A")
#     tbl.add_column("Feature B")
#     tbl.add_column("r (Pearson)", justify="right")
#     tbl.add_column("ρ (Spearman)", justify="right")
#     tbl.add_column("MI", justify="right")
#     tbl.add_column("Type", justify="left")
#     tbl.add_column("Flags", justify="left")

#     for _, row in pairs_sorted.iterrows():
#         flags = row.get("flags", [])
#         if isinstance(flags, str):
#             flags = [flags]
#         flag_str = "/".join(flags) if flags else "-"
#         tbl.add_row(
#             str(row["a"]),
#             str(row["b"]),
#             color_corr(row["pearson"]),
#             color_corr(row["spearman"]),
#             color_corr(row["mi"]),
#             row.get("type", "-"),
#             flag_str,
#         )
#     console.print(tbl)


# # ======================================================================
# # Redundancy Groups
# # ======================================================================
# def _show_groups(console: Console, groups: dict):
#     console.rule("[bold white]🔁 Redundancy Groups[/bold white]")

#     def render_group_list(title: str, group_list: list[dict]):
#         if not group_list:
#             console.print(f"[grey50]No {title} groups detected.[/grey50]\n")
#             return
#         console.print(f"\n[bold cyan]{title} Groups ({len(group_list)})[/bold cyan]")
#         for i, g in enumerate(group_list, start=1):
#             features = g.get("features", [])
#             avg_corr = g.get("avg_corr", np.nan)
#             min_corr = g.get("min_corr", np.nan)
#             max_corr = g.get("max_corr", np.nan)
#             if not features:
#                 continue

#             tbl = Table(
#                 title=f"[bold magenta]{title} Group {i}[/bold magenta]",
#                 box=box.SIMPLE_HEAVY,
#                 header_style="bold white",
#             )
#             tbl.add_column("Size", justify="right")
#             tbl.add_column("Avg |r|", justify="right", style="green")
#             tbl.add_column("Min |r|", justify="right", style="yellow")
#             tbl.add_column("Max |r|", justify="right", style="red")
#             tbl.add_column("Main Feature", style="cyan")
#             tbl.add_column("Members", style="white")

#             members_str = "\n".join(f"- {m}" for m in features)
#             tbl.add_row(
#                 str(len(features)),
#                 f"{avg_corr:.2f}" if not pd.isna(avg_corr) else "-",
#                 f"{min_corr:.2f}" if not pd.isna(min_corr) else "-",
#                 f"{max_corr:.2f}" if not pd.isna(max_corr) else "-",
#                 features[0],
#                 members_str,
#             )
#             console.print(tbl)
#             console.print()

#     render_group_list("Pearson", groups.get("pearson", []))
#     render_group_list("Mutual Information", groups.get("mi", []))

#############################################################
#############################################################

#############################################################
#############################################################

# # dods/analyze/core/analyzer/deep_analysis/relations.py

# """
# Feature Relationship Analyzer – v4
# - Adds summary & insights back
# - Parallel Pearson / Spearman / MI distributions
# - Dual dominant tables (Pearson + MI)
# - Flag legend near correlated pairs
# - Clean redundancy layout with spacing
# """

# import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# from rich.console import Console
# from rich.table import Table
# from rich.panel import Panel
# from rich import box


# # ======================================================================
# # MAIN ENTRY
# # ======================================================================
# def analyze_relations(analyzer, limit: int = 100, sort_metric: str = "max_combined", show_plots: bool = True, force_heatmaps: bool = False):
#     console = Console()
#     rel = analyzer.relations
#     info = analyzer.info or {}

#     if not rel:
#         console.print("[red]No relations found. Run RelationEngine first.[/red]")
#         return None




#     pearson = rel.get("pearson", pd.DataFrame())
#     spearman = rel.get("spearman", pd.DataFrame())
#     mi = rel.get("mi", pd.DataFrame())
#     groups = rel.get("groups", {})
#     pairs = rel.get("pairs", pd.DataFrame())
#     iso = rel.get("isolated", [])
#     summary = rel.get("summary", {})
#     # summary = rel.get("summary", {})
#     # pairs = pd.DataFrame(rel.get("pairs", []))
#     # groups = rel.get("groups", [])
#     # iso = rel.get("isolated", [])
#     # pearson = rel.get("pearson", pd.DataFrame())
#     # spearman = rel.get("spearman", pd.DataFrame())
#     # mi = rel.get("mi_knn", pd.DataFrame())

#     console.rule("[bold bright_cyan]🔍 Feature Relationship Analysis[/bold bright_cyan]")

#     # ------------------------------------------------------------------
#     # 0️⃣ Dataset overview
#     # ------------------------------------------------------------------
#     # --- Dataset summary ---
#     console.print(
#         f"[bold cyan]📊 Data Summary[/bold cyan]\n"
#         f"Rows: [white]{info.get('n_rows', '?')}[/white] | "
#         f"Columns: [white]{info.get('n_columns', '?')}[/white] | "
#         f"Numeric: [white]{info.get('n_numeric', '?')}[/white] | "
#         f"Categorical: [white]{info.get('n_categorical', '?')}[/white] | "
#         f"Datetime: [white]{info.get('n_datetime', '?')}[/white]\n"
#         f"Missing total: [white]{info.get('missing_total', '?')}[/white] "
#         f"({info.get('missing_pct', 0.0):.2f}%) | "
#         f"Memory: [white]{info.get('memory_usage_mb', 0.0):.2f} MB[/white]\n"
#     )

#     # ------------------------------------------------------------------
#     # 1️⃣ Summary block
#     # ------------------------------------------------------------------
#     t = Table(title="[bold bright_white]📈 Relation Summary[/bold bright_white]", box=box.SIMPLE_HEAVY)
#     t.add_column("Metric")
#     t.add_column("Value", justify="right")

#     def fmt(v):
#         return f"{v:.3f}" if isinstance(v, (float, np.floating)) else str(v)

#     t.add_row("[bold]Structure[/bold]", "")
#     t.add_row("  Features analyzed", str(summary.get("n_features", "?")))
#     t.add_row("  Redundancy groups", str(summary.get("n_groups", 0)))
#     t.add_row("  Isolated features", str(summary.get("n_isolated", 0)))
#     t.add_row("", "")

#     t.add_row("[bold]Strength[/bold]", "")
#     t.add_row("  Avg |r|", fmt(summary.get("avg_abs_corr", np.nan)))
#     t.add_row("  Strong-rel density", fmt(summary.get("strong_rel_density", np.nan)))
#     console.print(t)

#     # ------------------------------------------------------------------
#     # 2️⃣ Insights
#     # ------------------------------------------------------------------
#     insights, _ = _generate_insights(summary, iso)
#     insight_text = "\n".join(insights) if insights else "No notable findings."
#     console.print(Panel(insight_text, title="[bold yellow]🧠 Insights[/bold yellow]", expand=False))

#     # ------------------------------------------------------------------
#     # 3️⃣ Dominant features (Pearson + MI)
#     # ------------------------------------------------------------------
#     if isinstance(pearson, pd.DataFrame) and not pearson.empty:
#         _show_dominant_features(console, pearson, mi)

#     # ------------------------------------------------------------------
#     # 4️⃣ Isolated features (directly below)
#     # ------------------------------------------------------------------
#     if iso:
#         console.print(
#             Panel(
#                 f"[cyan]{len(iso)} isolated features[/cyan]: "
#                 + ", ".join(iso)
#                 + "\n[grey50]→ likely IDs, timestamps, or unique dimensions[/grey50]",
#                 title="[bold magenta]Isolated Features[/bold magenta]",
#                 expand=False,
#             )
#         )

#     # ------------------------------------------------------------------
#     # 5️⃣ Distributions (Pearson / Spearman / MI)
#     # ------------------------------------------------------------------
#     if show_plots and isinstance(pearson, pd.DataFrame) and not pearson.empty:
#         fig, axes = plt.subplots(1, 3, figsize=(13, 3))
#         metrics = [
#             ("|Pearson r|", pearson),
#             ("|Spearman ρ|", spearman),
#             ("Mutual Information", mi),
#         ]
#         for ax, (label, df) in zip(axes, metrics):
#             if df is None or df.empty:
#                 ax.axis("off")
#                 continue
#             tri = df.where(np.triu(np.ones(df.shape), 1).astype(bool)).stack().abs()
#             sns.histplot(tri, bins=25, ax=ax, color="#3498db")
#             ax.set_title(label, fontsize=11, fontweight="bold")
#             ax.set_xlabel("")
#             ax.set_ylabel("")
#         plt.suptitle("Distributions of Feature Relationships", fontsize=13, fontweight="bold")
#         plt.tight_layout()
#         plt.show()

#     # ------------------------------------------------------------------
#     # 6️⃣ Correlated Feature Pairs
#     # ------------------------------------------------------------------
#     if not pairs.empty:
#         console.print(
#             "[bright_black]Flag legend:[/bright_black] "
#             "[cyan]IDX[/cyan]=index-like  "
#             "[yellow]SKEW[/yellow]=skewed  "
#             "[magenta]OUT[/magenta]=outlier-heavy  "
#             "[white]CONST[/white]=constant\n"
#         )
#         _show_pairs_table(console, pairs, limit=limit, sort_metric=sort_metric)
#         if limit:
#             console.print("[grey50]Showing top pairs only. Use limit=None for full list.[/grey50]\n")

#     # ------------------------------------------------------------------
#     # 7️⃣ Redundancy Groups
#     # ------------------------------------------------------------------
#     if groups:
#         _show_groups(console, groups)

#     else:
#         console.print("[grey50]No redundancy groups detected.[/grey50]\n")
#     # ------------------------------------------------------------------
#     # 8️⃣ Global Pearson Heatmap (mit NaN-Maske)
#     # ------------------------------------------------------------------

# # ------------------------------------------------------------------
# # 8️⃣ Global Pearson Heatmap (kompakt, nur numerische Features)
# # ------------------------------------------------------------------
#     if (show_plots and isinstance(pearson, pd.DataFrame)) or force_heatmaps:
#         pearson_plot = pearson.replace([np.inf, -np.inf], np.nan)

#         # 🔹 Nur Zeilen/Spalten behalten, die wenigstens einen gültigen Wert haben
#         valid_features = pearson_plot.columns[pearson_plot.notna().any(axis=0)]
#         pearson_plot = pearson_plot.loc[valid_features, valid_features]

#         if not pearson_plot.empty and len(pearson_plot) <= 40:
#             console.rule("[bold white]Global Pearson Heatmap[/bold white]")
#             plt.figure(figsize=(8, 6))

#             sns.heatmap(
#                 pearson_plot,
#                 cmap="coolwarm",
#                 vmin=-1,
#                 vmax=1,
#                 square=True,
#                 cbar_kws={"label": "Pearson r"},
#             )

#             plt.title("Global Pearson Correlation", fontsize=12, fontweight="bold")
#             plt.tight_layout()
#             plt.show()
#         else:
#             if pearson_plot.empty:
#                 console.print("[grey50]Pearson heatmap skipped: no valid numeric correlations.[/grey50]")
#             elif len(pearson_plot) > 40 and not force_heatmaps:
#                 console.print("[grey50]Pearson heatmap skipped: too many features (> 40).[/grey50]")





#     # 9️⃣ Global Mutual Information Heatmap
#     if (show_plots and isinstance(mi, pd.DataFrame) and not mi.empty and len(mi) <= 40) or force_heatmaps:
#         console.rule("[bold white]Global Mutual Information Heatmap[/bold white]")
#         plt.figure(figsize=(8, 6))

#         mask = mi.isna()
#         sns.heatmap(
#             mi,
#             cmap="viridis",
#             vmin=0,
#             vmax=mi.max().max(),
#             square=True,
#             mask=mask,
#             cbar_kws={"label": "Mutual Information"},
#         )

#         plt.title("Global Mutual Information", fontsize=12, fontweight="bold")
#         plt.tight_layout()
#         plt.show()


# # ======================================================================
# # Helper: Insights
# # ======================================================================
# def _generate_insights(summary: dict, iso: list[str]):
#     msgs = []
#     if summary.get("avg_abs_corr", 0) < 0.2:
#         msgs.append("✅ Low average correlation — features are largely independent.")
#     if summary.get("strong_rel_density", 0) > 0.5:
#         msgs.append("⚠️ High inter-correlation density — redundancy likely.")
#     if iso:
#         msgs.append(f"🧩 {len(iso)} isolated features — likely IDs or timestamps.")
#     return msgs, iso


# # ======================================================================
# # Dominant features (Pearson + MI)
# # ======================================================================
# def _show_dominant_features(console: Console, pearson: pd.DataFrame, mi: pd.DataFrame | None):
#     def table_from_matrix(df: pd.DataFrame, title: str):
#         if df is None or df.empty:
#             console.print(f"[grey50]No valid data for {title}[/grey50]")
#             return Table()

#         abs_corr = df.abs()
#         connectivity = (abs_corr > 0.6).sum(axis=1)
#         top = connectivity.sort_values(ascending=False).head(8)

#         tbl = Table(title=title, box=box.MINIMAL_HEAVY_HEAD)
#         tbl.add_column("Feature", justify="left")
#         tbl.add_column("Links", justify="right")
#         tbl.add_column("Strongest Link", justify="left")
#         tbl.add_column("Max", justify="right")
#         tbl.add_column("Avg", justify="right")

#         for f in top.index:
#             # defensive: Zeile holen & NaN filtern
#             row = abs_corr.loc[f].dropna()
#             if row.empty:
#                 continue

#             # eigenen Eintrag entfernen
#             row_wo_self = row.drop(f, errors="ignore")
#             if row_wo_self.empty:
#                 continue

#             try:
#                 strongest = row_wo_self.idxmax()
#             except ValueError:
#                 continue

#             if pd.isna(strongest) or strongest not in abs_corr.columns:
#                 continue

#             max_v = abs_corr.loc[f, strongest]
#             avg_v = row.mean()
#             tbl.add_row(f, str(int(connectivity.get(f, 0))), strongest, f"{max_v:.2f}", f"{avg_v:.2f}")

#         if len(tbl.rows) == 0:
#             console.print(f"[grey50]No dominant correlations found for {title}[/grey50]\n")

#         return tbl

#     # --- beide Tabellen rendern ---
#     tbl_p = table_from_matrix(pearson, "🏆 Dominant (Pearson r)")
#     tbl_m = table_from_matrix(mi, "🏆 Dominant (Mutual Information)") if mi is not None and not mi.empty else None

#     if len(tbl_p.rows) or (tbl_m and len(tbl_m.rows)):
#         console.print(tbl_p)
#         if tbl_m:
#             console.print(tbl_m)
#     else:
#         console.print("[grey50]No dominant features detected.[/grey50]\n")



# # ======================================================================
# # Correlated pairs
# # ======================================================================
# def _show_pairs_table(console: Console, pairs: pd.DataFrame, limit: int = 100, sort_metric: str = "max_combined"):
#     def score(row):
#         if sort_metric == "max_combined":
#             return max(abs(row["pearson"]), abs(row["spearman"]), row["mi"])
#         if sort_metric == "pearson":
#             return abs(row["pearson"])
#         if sort_metric == "spearman":
#             return abs(row["spearman"])
#         if sort_metric == "mi":
#             return row["mi"]
#         return abs(row["pearson"])

#     pairs = pairs.copy()
#     pairs["_score"] = pairs.apply(score, axis=1)
#     pairs_sorted = pairs.sort_values("_score", ascending=False)
#     if limit:
#         pairs_sorted = pairs_sorted.head(limit)

#     def color_corr(v):
#         if abs(v) > 0.8: return f"[green]{v:.2f}[/green]"
#         if abs(v) > 0.5: return f"[yellow]{v:.2f}[/yellow]"
#         if abs(v) > 0.3: return f"[orange1]{v:.2f}[/orange1]"
#         return f"[grey58]{v:.2f}[/grey58]"

#     console.rule("💫 Correlated Feature Pairs")
#     tbl = Table(box=box.MINIMAL_HEAVY_HEAD)
#     tbl.add_column("Feature A")
#     tbl.add_column("Feature B")
#     tbl.add_column("r (Pearson)", justify="right")
#     tbl.add_column("ρ (Spearman)", justify="right")
#     tbl.add_column("MI", justify="right")
#     tbl.add_column("Type", justify="left")
#     tbl.add_column("Flags", justify="left")

#     for _, row in pairs_sorted.iterrows():
#         flags = row.get("flags", [])
#         if isinstance(flags, str):
#             flags = [flags]
#         flag_str = "/".join(flags) if flags else "-"
#         tbl.add_row(
#             str(row["a"]),
#             str(row["b"]),
#             color_corr(row["pearson"]),
#             color_corr(row["spearman"]),
#             color_corr(row["mi"]),
#             row.get("type", "-"),
#             flag_str,
#         )
#     console.print(tbl)


# # ======================================================================
# # Redundancy groups
# # ======================================================================
# def _show_groups(console: Console, groups: dict):
#     """
#     Zeigt Redundanzgruppen für Pearson und MI an — mit Metriken und schöner Formatierung.
#     """

#     console.rule("[bold white]🔁 Redundancy Groups[/bold white]")

#     def render_group_list(title: str, group_list: list[dict]):
#         """Render a single correlation type (Pearson or MI)."""
#         if not group_list:
#             console.print(f"[grey50]No {title} groups detected.[/grey50]\n")
#             return

#         console.print(f"\n[bold cyan]{title} Groups ({len(group_list)})[/bold cyan]")

#         # jede Gruppe als eigene Tabelle
#         for i, g in enumerate(group_list, start=1):
#             # Defensive checks – alte Formate unterstützen
#             if isinstance(g, dict):
#                 features = g.get("features", [])
#                 avg_corr = g.get("avg_corr", np.nan)
#                 min_corr = g.get("min_corr", np.nan)
#                 max_corr = g.get("max_corr", np.nan)
#             elif isinstance(g, (list, tuple)):
#                 features = list(g)
#                 avg_corr = min_corr = max_corr = np.nan
#             else:
#                 continue

#             if not features:
#                 continue

#             # --- Tabelle rendern ---
#             tbl = Table(
#                 title=f"[bold magenta]{title} Group {i}[/bold magenta]",
#                 box=box.SIMPLE_HEAVY,
#                 show_header=True,
#                 header_style="bold white",
#             )

#             tbl.add_column("Group", justify="right", style="bold bright_white", no_wrap=True)
#             tbl.add_column("Size", justify="right", style="bright_white")
#             tbl.add_column("Avg |r|", justify="right", style="green")
#             tbl.add_column("Min |r|", justify="right", style="yellow")
#             tbl.add_column("Max |r|", justify="right", style="red")
#             tbl.add_column("Main Feature", style="cyan")
#             tbl.add_column("Members", style="white")

#             members_str = "\n".join(f"- {m}" for m in features)
#             tbl.add_row(
#                 str(i),
#                 str(len(features)),
#                 f"{avg_corr:.2f}" if not pd.isna(avg_corr) else "-",
#                 f"{min_corr:.2f}" if not pd.isna(min_corr) else "-",
#                 f"{max_corr:.2f}" if not pd.isna(max_corr) else "-",
#                 features[0],
#                 members_str,
#             )

#             console.print(tbl)
#             console.print()  # spacing

#     # --- Pearson Groups ---
#     pearson_groups = groups.get("pearson", [])
#     render_group_list("Pearson", pearson_groups)

#     # --- MI Groups ---
#     mi_groups = groups.get("mi", [])
#     render_group_list("Mutual Information", mi_groups)

