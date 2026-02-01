# dods/analyze/core/analyzer/summaries/correlation_alerts.py

"""
Correlation summary — overview of pairwise relations and redundancy groups.
"""
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.layout import Layout
from rich.columns import Columns

def render(console, analyzer):
    rel = analyzer.relations or {}
    if not rel:
        return

    summary = rel.get("summary", {})
    groups = rel.get("groups", [])
    pearson = rel.get("pearson")
    mi = rel.get("mi_knn")

    console.print("\n[bold yellow]💫 Feature Relation Summary[/bold yellow]")

    # --- Insights panel ---
    insights = []
    avg_corr = summary.get("avg_abs_corr", 0)
    n_iso = summary.get("n_isolated", 0)
    if avg_corr < 0.25:
        insights.append("✅ Low average correlation — features are largely independent.")
    else:
        insights.append("⚠️ Strong average correlation — some redundancy expected.")
    if n_iso > 0:
        insights.append(f"🧩 {n_iso} isolated features — likely IDs or timestamps.")
    else:
        insights.append("🧠 No isolated features — all features relate to others.")

    insight_text = "\n".join(f"│ {line}" for line in insights)
    console.print(
        f"───────────────────────── 🧠 Insights ──────────────────────────╮\n"
        f"{insight_text}\n"
        f"╰────────────────────────────────────────────────────────────────╯"
    )

    # --- Redundancy Groups ---
    if groups:
        console.print(f"\n[bold white]🔗 {len(groups)} Redundancy Groups detected[/bold white]")
    else:
        console.print("\n[dim]No redundancy groups detected.[/dim]")

    # --- Dominant Correlations ---
    console.print("\n[bold cyan]🏆 Dominant (Pearson r)            🏆 Dominant (Mutual Information)[/bold cyan]")

    # Top 5 features by max correlation
    def dominant_table(corr_df, title):
        if corr_df is None or corr_df.empty:
            return Table(title=title, box=box.SIMPLE)
        tbl = Table(title=title, box=box.SIMPLE)
        tbl.add_column("Feature", style="bold")
        tbl.add_column("Links", justify="right")
        tbl.add_column("Strongest Link", justify="left")
        tbl.add_column("Max", justify="right")
        tbl.add_column("Avg", justify="right")

        abs_corr = corr_df.abs()
        top_features = abs_corr.max().sort_values(ascending=False).head(5)

        for feat in top_features.index:
            series = abs_corr.loc[feat].drop(feat)

            if series.empty or series.isna().all():
                strongest = "-"
                max_corr = 0.0
            else:
                strongest = series.idxmax()
                max_corr = series.max()

            tbl.add_row(
                feat,
                str((abs_corr.loc[feat] > 0.5).sum()),
                strongest,
                f"{max_corr:.2f}",
                f"{abs_corr.loc[feat].mean():.2f}",
            )
        return tbl


    tbl_pearson = dominant_table(pearson, "[bold cyan]🏆 Dominant (Pearson r)[/bold cyan]")
    tbl_mi = dominant_table(mi, "[bold cyan]🏆 Dominant (Mutual Information)[/bold cyan]")
    console.print(Columns([tbl_pearson, tbl_mi]))
