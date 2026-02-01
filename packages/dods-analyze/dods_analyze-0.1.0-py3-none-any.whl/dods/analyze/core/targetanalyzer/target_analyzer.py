# dods/analyze/core/targetanalyzer/target_analyzer.py

from __future__ import annotations
import pandas as pd

from dods.analyze.core.targetanalyzer.target_analyzer import TargetAnalyzer
from dods.analyze.core.analyzer.main import DataAnalyzer
from __future__ import annotations
import pandas as pd
from dods.analyze.core.analyzer.main import DataAnalyzer


class TargetAnalyzer(DataAnalyzer):
    """
    High-level analyzer specialized for analyzing a target variable 
    (either numerical or categorical) within a dataset.

    This class can be initialized in two modes:
    1. Fresh analysis mode: pass a pandas DataFrame.
       Example: TargetAnalyzer(df, "target")
    2. Reuse mode: pass an existing DataAnalyzer instance to reuse
       precomputed metadata and relations.
       Example: TargetAnalyzer(existing_analyzer, "target")

    Parameters
    ----------
    source : pd.DataFrame | DataAnalyzer
        Either a raw DataFrame or an existing DataAnalyzer.
    target_col : str
        The name of the target column to analyze.

    Raises
    ------
    TypeError
        If `source` is neither a pandas DataFrame nor a DataAnalyzer.
    """

    def __init__(self, source, target_col: str):
        # Case 1: reuse from existing DataAnalyzer
        if isinstance(source, DataAnalyzer):
            # copy all attributes (meta, info, relations, df, etc.)
            self.__dict__.update(source.__dict__)
            self.df = source.df
            if hasattr(self, "logger"):
                self.logger.info(
                    f"[TargetAnalyzer] Reusing existing DataAnalyzer instance with {len(self.df)} rows."
                )
        # Case 2: fresh initialization from DataFrame
        elif isinstance(source, pd.DataFrame):
            super().__init__(source)
            if hasattr(self, "logger"):
                self.logger.info(
                    f"[TargetAnalyzer] Initialized new DataAnalyzer for dataset with {len(self.df)} rows."
                )
        else:
            raise TypeError(
                f"TargetAnalyzer expects a DataFrame or DataAnalyzer, got {type(source).__name__}"
            )

        # Target setup
        if target_col not in self.df.columns:
            raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

        self.target_col = target_col
        self.target = self.df[target_col]
        self.target_type = self._infer_target_type()

        if hasattr(self, "logger"):
            self.logger.info(
                f"[TargetAnalyzer] Target column: '{self.target_col}' "
                f"(type: {self.target_type}, non-null: {self.target.notna().sum()})"
            )

    # ---------------------------------------------------------
    # Internal utilities
    # ---------------------------------------------------------

    def _infer_target_type(self) -> str:
        """
        Infer the type of the target variable.

        Returns
        -------
        str
            "binary", "numerical", or "categorical"
        """
        series = self.target.dropna()
        if series.dtype.kind in "if":  # integer or float
            if series.nunique() <= 2:
                return "binary"
            return "numerical"
        return "categorical"



# from __future__ import annotations
# import pandas as pd

# from dods.analyze.core.analyzer.main import DataAnalyzer

# class TargetAnalyzer(DataAnalyzer):
#   """Analyzer for target variable analysis in datasets. (numerical or categorical)"""

#   def __init__(self, df, target_col: str):
#     super().__init__(df)
#     self.target_col = target_col
#     self.target = df[target_col]
#     self.target_type = self._infer_target_type()


#   def _infer_target_type(self) -> str:
#     """Infer the type of the target variable (numerical or categorical)."""
#     series = self.target.dropna()
#     if series.dtype.kind in "if":
#       if series.nunique()<=2:
#         return "binary"
#       return "numerical"
#     else:
#       return "categorical"
      
#   def analyze_meta(self):
#       """Return metadata summary for the target column (from FeatureStats)."""
#       if not hasattr(self, "meta") or self.target_col not in self.meta:
#           return {
#               "target_col": self.target_col,
#               "type": self.target_type,
#               "meta": None,
#               "info": self.info if hasattr(self, "info") else None,
#           }

#       fs = self.meta[self.target_col]
#       return {
#           "target_col": self.target_col,
#           "type": self.target_type,
#           "meta": fs.to_dict(),
#           "info": self.info if hasattr(self, "info") else None,  # dataset-level summary
#       }



