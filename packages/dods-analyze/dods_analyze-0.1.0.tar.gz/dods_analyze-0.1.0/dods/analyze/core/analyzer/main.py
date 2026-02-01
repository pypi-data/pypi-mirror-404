# dods/analyze/core/analyzer/main.py


"""
DataAnalyzer — central orchestrator for full dataset analysis.

Now uses:
- compute_all_stats() for feature metrics
- ThresholdEngine for flagging
- RelationEngine for correlation/group analysis
- AnalyzerBase._update_info() for dataset summary
"""

import pandas as pd
import logging
from typing import Any, Dict

from dods.analyze.core.analyzer.info_utils import update_info
from dods.analyze.core.base import AnalyzerBase
from dods.analyze.core.analyzer.stats_compute import compute_all_stats
from dods.analyze.core.analyzer.threshold_engine import ThresholdEngine
#from dods.analyze.core.analyzer.relations_engine import RelationEngine
from dods.analyze.core.analyzer.relations.engine import RelationEngine
from dods.analyze.core.analyzer.summary import render_summary

from dods.analyze.core.analyzer.deep_analysis import analyze_distributions, analyze_categoricals, analyze_outliers, analyze_relations, analyze_missing
from dods.analyze.core.analyzer.relations.config import RelationParams

from dods.analyze.core.analyzer.plot_config import (
    build_distribution_configs,
    build_outlier_configs,
    build_missing_configs,
    build_flag_configs,
    build_correlation_configs,
)

# (Plot configs & deep analysis imports bleiben, falls du sie später brauchst)
# from dods.analyze.core.analyzer.plot_config import (
#     build_distribution_configs,
#     build_outlier_configs,
#     build_missing_configs,
#     build_flag_configs,
#     build_correlation_configs,
# )

logger = logging.getLogger(__name__)


class DataAnalyzer(AnalyzerBase):
    """
    DataAnalyzer — central orchestrator for full dataset analysis.

    Quick start
    ----------
    >>> import pandas as pd
    >>> from dods.analyze.core.analyzer.main import DataAnalyzer
    >>>
    >>> df = pd.read_csv("data.csv")
    >>> dfa = DataAnalyzer(df)
    >>> dfa.summary()
    >>>
    >>> # Deep analysis (optional)
    >>> dfa.analyze_distributions()
    >>> dfa.analyze_missing()
    >>> dfa.analyze_outliers()
    >>> dfa.analyze_relations()
    >>>
    >>> # Curated method overview
    >>> DataAnalyzer.help()
    """


    def __init__(self, df: pd.DataFrame, auto_analyze: bool = True, params: Dict[str, Any] | None = None):
        """
        Parameters
        ----------
        df : pd.DataFrame
            Input dataset to analyze.
        auto_analyze : bool
            If True, runs the full pipeline on init.
        params : dict, optional
            Optional configuration parameters for RelationEngine (thresholds, MI bins, etc.)
        """
        super().__init__()
        self.df = df

        # Core data containers
        self.meta: Dict[str, Any] = {}
        self.info: Dict[str, Any] = {}
        self.relations: Dict[str, Any] = {}
        self.plot_configs: Dict[str, Any] = {}
        self.name = "analyzer"


        # Engines
        self.threshold_engine = ThresholdEngine(self.thresholds_by_type)
        self.relation_engine = RelationEngine(params=RelationParams(**(params or {})))

        if auto_analyze:
            self.analyze()



    @classmethod
    def help(cls) -> None:
        """Print a curated overview of the most commonly used methods."""
        print(
            f"{cls.__name__} — quick methods\n"
            "\n"
            "Summary:\n"
            "  dfa.summary()\n"
            "\n"
            "Deep analysis:\n"
            "  dfa.analyze_distributions(plots=True, limit=None, columns=None)\n"
            "  dfa.analyze_categoricals(**kwargs)\n"
            "  dfa.analyze_outliers(**kwargs)\n"
            "  dfa.analyze_relations(**kwargs)\n"
            "  dfa.analyze_missing(**kwargs)\n"
        )

    # ------------------------------------------------------------------
    # Main orchestration
    # ------------------------------------------------------------------
    def analyze(self) -> "DataAnalyzer":
        """Run full analysis pipeline with logging and error isolation."""
        logger.info("🚀 Starting dataset analysis (%d rows, %d columns)", *self.df.shape)

        try:
            # 1️⃣ Compute base feature stats
            self.meta = compute_all_stats(self.df)
            logger.info("✅ Computed feature statistics for %d columns", len(self.meta))

            # 2️⃣ Apply threshold flags
            self.threshold_engine.apply_to_meta(self.meta)
            logger.info("✅ Applied thresholds and flags")

            # 3️⃣ Compute feature relations (Pearson, Spearman, MI, groups)
            self.relations = self.relation_engine.analyze(self.df)
            logger.info("✅ Computed feature relations")

            # 4️⃣ Update dataset summary info
            self.info = update_info(meta=self.meta, df=self.df, thresholds_by_type=self.thresholds_by_type, logger=self.logger)
            logger.info("✅ Dataset info updated")

            #(Optional: Plot configs – später reaktivieren)
            self.plot_configs = {
                "distribution": build_distribution_configs(self.meta, self.info),
                "outliers": build_outlier_configs(self.meta),
                "missing": build_missing_configs(self.meta),
                "flags": build_flag_configs(self.meta),
                "correlation": build_correlation_configs(self.meta, self.df),
            }
            logger.info("✅ Plot configurations built")

        except Exception as e:
            logger.exception("❌ DataAnalyzer failed: %s", e)
            raise

        logger.info("🎯 Dataset analysis complete.")
        return self

    # ------------------------------------------------------------------
    # DataFrame outputs
    # ------------------------------------------------------------------
    def get_info_df(self) -> pd.DataFrame:
        """Return dataset-level summary info as one-row DataFrame."""
        return pd.DataFrame([self.info]) if self.info else pd.DataFrame()

    def get_meta_df(self) -> pd.DataFrame:
        """Return per-feature metadata as DataFrame (each column as one row)."""
        if not self.meta:
            return pd.DataFrame()
        records = [fs.to_dict() for fs in self.meta.values()]
        return pd.DataFrame.from_records(records)

    def get_relations_summary_df(self) -> pd.DataFrame:
        """Return summarized relation info (summary + groups + top_pairs)."""
        if not self.relations:
            return pd.DataFrame()

        summary = self.relations.get("summary", {})
        groups = self.relations.get("groups", [])
        df_groups = pd.DataFrame(groups) if groups else pd.DataFrame()
        df_summary = pd.DataFrame([summary])
        return pd.concat([df_summary, df_groups], axis=1)

    # ------------------------------------------------------------------
    # Summary view (console)
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Summary view (console)
    # ------------------------------------------------------------------
    def summary(self):
        """
        Smart summary method:
        - Tries to infer instance variable name (e.g. 'dfa')
        - Falls back to 'analyzer'
        - Renders full dataset summary via summaries.render_summary()
        """
        import inspect
        from dods.analyze.core.analyzer.summary import render_summary

        # ✅ Try to infer variable name from caller's local scope
        if not getattr(self, "name", None) or self.name == "analyzer":
            try:
                frame = inspect.currentframe().f_back
                for var_name, var_value in frame.f_locals.items():
                    if var_value is self:
                        self.name = var_name
                        break
                else:
                    self.name = "analyzer"
            except Exception:
                self.name = "analyzer"

        # ✅ Delegate to the summary renderer
        render_summary(self)


    def analyze_distributions(self, plots=True, limit=None, columns=None):
        """Numeric feature distribution analysis."""
        from dods.analyze.core.analyzer.deep_analysis.distributions import analyze_distributions
        return analyze_distributions(self, limit=limit, columns=columns, plots=plots)        
    def analyze_categoricals(self, **kwargs):
        """Categorical feature deep analysis."""
        from dods.analyze.core.analyzer.deep_analysis.categoricals import analyze_categoricals
        return analyze_categoricals(self, **kwargs)
    
    def analyze_outliers(self, **kwargs):
        """Outlier analysis for numeric features."""
        from dods.analyze.core.analyzer.deep_analysis.outliers import analyze_outliers
        return analyze_outliers(self, **kwargs)
    
    def analyze_relations(self, **kwargs):
        """Feature relationship analysis."""
        from dods.analyze.core.analyzer.deep_analysis.relations import analyze_relations
        return analyze_relations(self, **kwargs)

    def analyze_missing(self, **kwargs):
        """Missing value analysis."""
        from dods.analyze.core.analyzer.deep_analysis.missing import analyze_missing
        return analyze_missing(self, **kwargs)
    




# # dods/analyze/core/analyzer/main.py
# import pandas as pd
# import numpy as np
# import logging
# from typing import Any, Dict
# from dods.analyze.core.analyzer.summary import *

# #from dods.analyze.core.analyzer.deep_analysis import analyze_distributions
# #     analyze_categoricals,
# #     analyze_outliers,
# #     analyze_missing,
# #     analyze_correlations,
# # )

# from dods.analyze.core.base import AnalyzerBase
# from dods.analyze.core.analyzer.stats_compute import compute_all_stats
# from dods.analyze.core.analyzer.flags import assign_flags
# from dods.analyze.core.analyzer.plot_config import (
#     build_distribution_configs,
#     build_outlier_configs,
#     build_missing_configs,
#     build_flag_configs,
#     build_correlation_configs,
# )

# logger = logging.getLogger(__name__)

# class DataAnalyzer(AnalyzerBase):
#     """Central orchestrator for full dataset analysis."""

#     def __init__(self, df: pd.DataFrame, auto_analyze: bool = True):
#         super().__init__()
#         self.df = df
#         self.meta: Dict[str, Any] = {}
#         self.info: Dict[str, Any] = {}
#         self.plot_configs: Dict[str, Any] = {}
#         self.relations: Dict[str, Any] = {}
#         self.groups: list[set[str]] = []
#         self.recommendations: Dict[str, Any] = {}

#         if auto_analyze:
#             self.analyze()
#     def analyze(self):
#         """Run full analysis pipeline with logging and error isolation."""
#         logger.info("Starting dataset analysis (%d rows, %d columns)", *self.df.shape)

#         try:
#             # 1. Compute Stats
#             self.meta = compute_all_stats(self.df)
#             logger.info("Computed feature statistics for %d columns", len(self.meta))

#             # 2. Assign Flags
#             assign_flags(self.meta, self.info)
#             logger.info("Assigned feature flags")

#             # 3. Build Plot Configs
#             self.plot_configs = {
#                 "distribution": build_distribution_configs(self.meta, self.info),
#                 "outliers": build_outlier_configs(self.meta),
#                 "missing": build_missing_configs(self.meta),
#                 "flags": build_flag_configs(self.meta),
#                 "correlation": build_correlation_configs(self.meta, self.df),
#             }
#             logger.info("Built plot configurations")

#             # 4. Update summary info
#             self._update_info(self.meta, self.df)
#             logger.info("Finalized dataset summary")


#         except Exception as e:
#             logger.exception("DataAnalyzer failed: %s", e)
#             raise

#         return self



#     def get_info_df(self) -> pd.DataFrame:
#         """Return dataset-level summary info as one-row DataFrame."""
#         return pd.DataFrame([self.info])

#     def get_meta_df(self) -> pd.DataFrame:
#         """Return per-feature metadata as DataFrame (each column as one row)."""
#         if not self.meta:
#             return pd.DataFrame()
#         records = [fs.to_dict() for fs in self.meta.values()]
#         return pd.DataFrame.from_records(records)

#     def get_plot_config_df(self) -> pd.DataFrame:
#         """Flatten plot configurations into a DataFrame."""
#         if not self.plot_configs:
#             return pd.DataFrame()
#         rows = []
#         for group, configs in self.plot_configs.items():
#             for name, conf in configs.items():
#                 rows.append({
#                     "feature": name,
#                     "group": group,
#                     **conf["meta"],
#                     **conf.get("params", {}),
#                 })
#         return pd.DataFrame(rows)
    
#     # def summary(self):
#     #   print()
#     #   render_dataset_summary(self)
#     #   render_datetime_spans(self)
#     #   render_correlation_alerts(self)
#     #   render_cast_suggestions(self, limit=5)
#     #   render_numeric_table(self, limit=self.limits["numeric"])
#     #   render_symbol_legend()
#     #   render_categorical_table(self, limit=self.limits["categorical"])
#     #   render_flag_summary(self)
#     #   render_analysis_options()
#     #   print()

#     def analyze_distributions(self, plots=True, limit=None, columns=None):
#         """Numeric feature distribution analysis."""
#         from dods.analyze.core.analyzer.deep_analysis.distributions import analyze_distributions
#         return analyze_distributions(self, limit=limit, columns=columns, plots=plots)

#     def analyze_categoricals(self, **kwargs):
#         """Categorical feature deep analysis."""
#         from dods.analyze.core.analyzer.deep_analysis.categoricals import analyze_categoricals
#         return analyze_categoricals(self, **kwargs)
    
#     def analyze_outliers(self, **kwargs):
#         """Outlier analysis for numeric features."""
#         from dods.analyze.core.analyzer.deep_analysis.outliers import analyze_outliers
#         return analyze_outliers(self, **kwargs)
    
#     def analyze_missing(self, **kwargs):
#         """Missing value analysis."""
#         from dods.analyze.core.analyzer.deep_analysis.missing import analyze_missing
#         return analyze_missing(self, **kwargs)
    
#     def analyze_relations(self, **kwargs):
#         """Feature relationship analysis."""
#         from dods.analyze.core.analyzer.deep_analysis.relations import analyze_relations
#         return analyze_relations(self, **kwargs)