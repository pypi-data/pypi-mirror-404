"""
Unified dataset summary view.
Combines multiple summary modules for compact, information-rich console output.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule

from dods.analyze.core.analyzer.summaries import (
    dataset_summary,
    table_numeric,
    table_categorical,
    correlation_alerts,
    missing_summary,
    cast_suggestions,
    analysis_options,
)


def render_summary(analyzer):
    """
    Central summary orchestrator for DataAnalyzer.
    Uses modular render() functions from /summaries.
    """
    console = Console(width=140)
    console.rule("[bold cyan]📋 DATASET SUMMARY[/bold cyan]")

    # --- Overview -----------------------------------------------------
    dataset_summary.render(console, analyzer)

    # --- Optional detail blocks (only if data present) ----------------
    if analyzer.meta:
        table_numeric.render(console, analyzer, limit=8)
        table_categorical.render(console, analyzer, limit=8)
    if analyzer.relations:
        correlation_alerts.render(console, analyzer)
    if analyzer.meta:
        missing_summary.render(console, analyzer)
    if any(fs.cast_suggestion for fs in analyzer.meta.values()):
        cast_suggestions.render(console, analyzer)

    # --- Analysis config at the end -----------------------------------
    analysis_options.render(console, analyzer)

    console.print()
    console.rule("[green]✔ End of Summary[/green]")
    console.print()


# optional shorthand for DataAnalyzer.summary()
def attach_to_analyzer():
    from dods.analyze.core.analyzer.main import DataAnalyzer
    DataAnalyzer.summary = lambda self: render_summary(self)
