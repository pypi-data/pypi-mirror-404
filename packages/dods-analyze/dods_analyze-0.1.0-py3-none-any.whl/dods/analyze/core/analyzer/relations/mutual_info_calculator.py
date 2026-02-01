# dods/analyze/core/analyzer/relations/mutual_info_calculator.py
import numpy as np
import pandas as pd
import logging
from itertools import combinations
from sklearn.feature_selection import mutual_info_regression
from sklearn.metrics import mutual_info_score
from sklearn.preprocessing import KBinsDiscretizer, StandardScaler
from typing import Dict, Any

from .config import RelationParams


class MutualInfoCalculator:
    """Compute a symmetric Mutual Information (MI) matrix between all feature pairs.

    Handles:
        - num–num (kNN MI, normalized)
        - cat–cat (entropy-based MI)
        - cat–num (binned hybrid MI)

    Normalizes all MI values to [0..1].
    """

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def compute(self, df: pd.DataFrame, params: RelationParams) -> pd.DataFrame:
        """Compute normalized hybrid MI matrix for all feature pairs."""
        self.logger.info("Calculating hybrid mutual information matrix...")

        if df.empty:
            self.logger.warning("Empty DataFrame provided for MI calculation.")
            return pd.DataFrame()

        p = params
        n_samples = min(len(df), p.subsample)
        df_s = df.sample(n_samples, random_state=42) if len(df) > n_samples else df.copy()

        is_num = df_s.dtypes.apply(lambda dt: pd.api.types.is_numeric_dtype(dt))
        feats = df_s.columns.tolist()

        # Scale and discretize numeric columns
        num_scaled: Dict[str, np.ndarray] = {}
        num_binned: Dict[str, np.ndarray] = {}

        if is_num.any():
            df_num = df_s.loc[:, is_num].dropna(axis=1, how="all")
            if not df_num.empty:
                scaler = StandardScaler()
                arr_scaled = scaler.fit_transform(df_num.fillna(df_num.median(numeric_only=True)))
                for i, c in enumerate(df_num.columns):
                    num_scaled[c] = arr_scaled[:, i]

                disc = KBinsDiscretizer(
                    n_bins=p.mi_n_bins, encode="ordinal", strategy="quantile"
                )
                df_num_filled = df_num.fillna(df_num.median(numeric_only=True))
                try:
                    arr_binned = disc.fit_transform(df_num_filled.values)
                    for i, c in enumerate(df_num.columns):
                        num_binned[c] = arr_binned[:, i].astype(int)
                except Exception as e:
                    self.logger.warning(f"KBinsDiscretizer failed: {e}")
                    for c in df_num.columns:
                        num_binned[c] = pd.qcut(
                            df_num_filled[c],
                            q=min(p.mi_n_bins, max(2, df_num_filled[c].nunique())),
                            labels=False,
                            duplicates="drop",
                        ).fillna(0).astype(int).to_numpy()

        # Encode categorical columns
        cat_codes: Dict[str, np.ndarray] = {}
        top_k = int(p.mi_top_categories)
        for c in df_s.columns[~is_num]:
            s = df_s[c].astype("object").astype(str).fillna("__nan__")
            vc = s.value_counts()
            if len(vc) > top_k:
                keep = set(vc.head(top_k - 1).index)
                s = s.where(s.isin(keep), other="__other__")
            cat_codes[c] = pd.factorize(s, sort=False)[0].astype(int)

        # Compute MI matrix
        mi = pd.DataFrame(0.0, index=feats, columns=feats, dtype=float)
        pairs = list(combinations(feats, 2))[: p.mi_max_pairs]

        def entropy_from_codes(z: np.ndarray) -> float:
            return float(mutual_info_score(z, z))

        for a, b in pairs:
            try:
                a_is_num = bool(is_num.get(a, False))
                b_is_num = bool(is_num.get(b, False))

                if a_is_num and b_is_num and a in num_scaled and b in num_scaled:
                    x = np.nan_to_num(num_scaled[a]).reshape(-1, 1)
                    y = np.nan_to_num(num_scaled[b])
                    mi_val = float(
                        mutual_info_regression(
                            x, y, n_neighbors=p.mi_knn_neighbors, random_state=42
                        )[0]
                    )
                    hx = entropy_from_codes(num_binned[a])
                    hy = entropy_from_codes(num_binned[b])
                    denom = np.sqrt(hx * hy)
                    mi_norm = mi_val / denom if denom > 0 else 0.0

                elif (not a_is_num) and (not b_is_num):
                    x, y = cat_codes[a], cat_codes[b]
                    mi_raw = float(mutual_info_score(x, y))
                    hx, hy = entropy_from_codes(x), entropy_from_codes(y)
                    denom = np.sqrt(hx * hy)
                    mi_norm = mi_raw / denom if denom > 0 else 0.0

                elif a_is_num != b_is_num:
                    num_name, cat_name = (a, b) if a_is_num else (b, a)
                    if num_name in num_binned and cat_name in cat_codes:
                        xn, xc = num_binned[num_name], cat_codes[cat_name]
                        mi_raw = float(mutual_info_score(xn, xc))
                        hx, hy = entropy_from_codes(xn), entropy_from_codes(xc)
                        denom = np.sqrt(hx * hy)
                        mi_norm = mi_raw / denom if denom > 0 else 0.0
                    else:
                        mi_norm = 0.0
                else:
                    mi_norm = 0.0

                mi.at[a, b] = mi.at[b, a] = mi_norm

            except Exception as e:
                self.logger.debug(f"MI failed for {a}-{b}: {e}")

        np.fill_diagonal(mi.values, 0.0)
        self.logger.info("Mutual Information matrix computed successfully.")
        return mi
