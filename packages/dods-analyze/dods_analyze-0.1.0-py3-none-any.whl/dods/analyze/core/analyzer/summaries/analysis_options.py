# dods/analyze/core/analyzer/summaries/analysis_options.py
"""
Readable list of available analysis methods with real instance name.
Compact vertical layout for better readability.
"""

import inspect
from rich.panel import Panel
from rich.console import Console
from rich.text import Text


def _infer_instance_name(obj, max_depth: int = 6) -> str:
    """Try to infer variable name of analyzer instance by inspecting locals/globals."""
    try:
        frame = inspect.currentframe().f_back  # caller
        depth = 0
        while frame and depth < max_depth:
            for n, v in frame.f_locals.items():
                if v is obj:
                    return n
            for n, v in frame.f_globals.items():
                if v is obj:
                    return n
            frame = frame.f_back
            depth += 1
    except Exception:
        pass
    return "analyzer"


def render(console, analyzer, instance_name: str | None = None):
    """
    Clean, compact rendering of all available .analyze_*** methods.
    No emoji before 'Run me', parameters listed vertically with gray explanations.
    """
    instance_name = getattr(analyzer, "name", None) or _infer_instance_name(analyzer)
    console.rule(f"🧭 Available Analysis Methods for {instance_name}")

    methods = [
        {
            "call": f"{instance_name}.analyze_distributions()",
            "desc": (
                "Run me 👉 [bold cyan]{call}[/bold cyan] — Analyze numeric features in depth: compute mean, std, skew, "
                "and detect outliers across all numeric columns.\n"
                "   Params:\n"
                "     – plots = True [dim]render visual distributions[/dim]\n"
                "     – limit = None [dim]number of features to include[/dim]\n"
                "     – columns = None [dim]select specific features[/dim]"
            ),
        },
        {
            "call": f"{instance_name}.analyze_categoricals()",
            "desc": (
                "Run me 👉 [bold cyan]{call}[/bold cyan] — Explore categorical variables: detect dominant values, "
                "distribution balance, and entropy of label sets.\n"
                "   Params:\n"
                "     – plots = True [dim]enable charts[/dim]\n"
                "     – limit = 10 [dim]max number of categories to inspect[/dim]"
            ),
        },
        {
            "call": f"{instance_name}.analyze_outliers()",
            "desc": (
                "Run me 👉 [bold cyan]{call}[/bold cyan] — Identify extreme numeric outliers using IQR thresholds and deviation metrics.\n"
                "   Params:\n"
                "     – plots = True [dim]enable histogram & boxplot display[/dim]\n"
                "     – limit = 10 [dim]restrict shown features[/dim]"
            ),
        },
        {
            "call": f"{instance_name}.analyze_missing()",
            "desc": (
                "Run me 👉 [bold cyan]{call}[/bold cyan] — Diagnose missing values: show rates, patterns, and co-missingness between columns.\n"
                "   Params:\n"
                "     – plots = True [dim]display missingness heatmap[/dim]\n"
                "     – top_n = 10 [dim]show top features with most missing data[/dim]"
            ),
        },
        {
            "call": f"{instance_name}.analyze_relations()",
            "desc": (
                "Run me 👉 [bold cyan]{call}[/bold cyan] — Examine feature relationships: Pearson/Spearman correlation, "
                "mutual information, and redundancy groups.\n"
                "   Params:\n"
                "     – limit = 100 [dim]max pairs to consider[/dim]\n"
                "     – sort_metric = 'max_combined' [dim]sorting key[/dim]\n"
                "     – show_plots = True [dim]render correlation plots[/dim]"
            ),
        },
    ]

    for m in methods:
        console.print(m["desc"].format(call=m["call"]))
