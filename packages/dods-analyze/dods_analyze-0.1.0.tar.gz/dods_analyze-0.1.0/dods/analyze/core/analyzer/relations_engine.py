# dods/analyze/core/analyzer/relations_engine.py
"""
RelationEngine — compute and classify feature relationships (v3)

Neu:
- Pearson & Spearman nur auf numerischen Spalten (Matrix auf alle Features reindiziert)
- MI (hybrid): num–num (kNN), cat–cat (diskret), cat–num (binned) — alles normalisiert in [0..1]
- Zwei Redundanz-Clusterings: Pearson-basiert (linear), MI-basiert (semantisch, alle Typen)
- Robuste Fallbacks für kleine / leere Matrizen
- Mehr Parameter: mi_n_bins, mi_top_categories
"""

from __future__ import annotations

import logging
from itertools import combinations
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import skew
from sklearn.feature_selection import mutual_info_regression
from sklearn.metrics import mutual_info_score
from sklearn.preprocessing import KBinsDiscretizer, StandardScaler
from scipy.cluster.hierarchy import linkage, fcluster


class RelationEngine:
    """Analyze relationships among features using Pearson, Spearman and (hybrides) MI."""

    def __init__(self, **params):
        defaults = {
            # Correlation settings
            "pearson_threshold": 0.5,
            "group_threshold": 0.82,    # je höher, desto kleinere Gruppen (0.82 ~ r>=0.82)
            "mi_max_pairs": 300,        # Performance-Schutz für große D
            "subsample": 10_000,        # Sampling für MI/kNN
            "iso_threshold": 0.15,

            # Distribution & Outlier (nur numerisch)
            "outlier_iqr_factor": 3.0,
            "outlier_flag_threshold": 0.03,
            "skew_flag_threshold": 1.0,

            # MI (neu)
            "mi_knn_neighbors": 5,
            "mi_n_bins": 20,            # für Diskretisierung bei MI-Normalisierung & cat–num
            "mi_top_categories": 30,    # Kappung von zu feingranularen Kategorien

            # Klassifikation
            "classify_low_pearson_monotone": 0.3,
            "classify_low_pearson_nonlinear": 0.2,
            "classify_spearman_monotone": 0.6,
            "classify_mi_complex": 0.05,
            "classify_linear_weak": 0.3,
            "classify_linear_strong": 0.7,
        }
        self.params = {**defaults, **params}

        # Storage
        self.relations: Dict[str, Any] = {}
        self.distribution: Dict[str, Any] = {}
        self.pair_types: List[Dict[str, Any]] = []
        self.groups: Dict[str, Any] = {}
        self.summary: Dict[str, Any] = {}
        self.isolated: List[str] = []

        # Logging
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            fmt = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
            handler.setFormatter(logging.Formatter(fmt, "%H:%M:%S"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    # ==================================================================
    # Public API
    # ==================================================================
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Pipeline:
        - Pearson/Spearman auf numerischen Spalten (auf alle Features reindiziert)
        - MI (hybrid) über alle Feature-Typen (num–num, cat–cat, cat–num)
        - Redundanzgruppen separat für Pearson (linear) und MI (semantisch)
        - Distribution (numerisch), Isolation, Summary
        """
        self.logger.info("🚀 Starting feature relation analysis...")

        if df.empty:
            self.logger.warning("Empty DataFrame provided.")
            return {}

        all_features = df.columns
        df_num = df.select_dtypes(include="number")

        # Pearson/Spearman
        if df_num.empty:
            self.logger.warning("No numeric columns found for correlation. Skipping Pearson/Spearman.")
            pearson = pd.DataFrame(index=all_features, columns=all_features, dtype=float)
            spearman = pd.DataFrame(index=all_features, columns=all_features, dtype=float)
        else:
            pearson_num = df_num.corr(method="pearson")
            spearman_num = df_num.corr(method="spearman")
            pearson = pearson_num.reindex(index=all_features, columns=all_features)
            spearman = spearman_num.reindex(index=all_features, columns=all_features)

        # Distribution (numerisch)
        self.distribution = self._compute_distribution(df_num)

        # MI über alle Features (hybrid)
        mi = self._compute_mi_hybrid(df)

        # Pairs & Typisierung (alle Paare, r/rho ggf. NaN)
        self.pair_types = self._build_pair_types(pearson, spearman, mi)

        # Gruppen
        self.groups = {
            "pearson": self._build_groups_with_stats(pearson),
            "mi": self._build_groups_with_stats(mi),
        }

        # Isolierte (nur aus Pearson sinnvoll)
        self.isolated = self._find_isolated(pearson)

        # Summary
        self.summary = self._build_summary(pearson)
        self.summary.update({
            "n_groups_pearson": len(self.groups["pearson"]),
            "n_groups_mi": len(self.groups["mi"]),
        })

        # Bundle
        self.relations = {
            "pearson": pearson,
            "spearman": spearman,
            "mi_knn": mi,
            "distribution": self.distribution,
            "pairs": self.pair_types,
            "groups": self.groups,
            "isolated": self.isolated,
            "summary": self.summary,
        }

        self.logger.info("✅ Relation analysis completed.")
        return self.relations

    # ==================================================================
    # Distribution (numeric)
    # ==================================================================
    def _compute_distribution(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Skewness, Outlier-Ratio, Unique-Count, Index-Heuristik je numerischer Spalte."""
        out: Dict[str, Dict[str, Any]] = {}
        n = len(df)
        if df.empty:
            return out

        for col in df.columns:
            vals = df[col].dropna().to_numpy()
            if len(vals) < 3:
                continue

            q1, q3 = np.percentile(vals, [25, 75])
            iqr = q3 - q1
            factor = self.params["outlier_iqr_factor"]
            lower, upper = q1 - factor * iqr, q3 + factor * iqr
            outlier_ratio = float(np.mean((vals < lower) | (vals > upper)))

            nunique = int(len(np.unique(vals)))
            unique_ratio = nunique / n if n else 0.0

            diffs = np.diff(vals)
            is_monotonic_seq = bool(np.all(diffs >= 0) or np.all(diffs <= 0))

            vmin, vmax = np.min(vals), np.max(vals)
            span = (vmax - vmin) if vmax != vmin else 1.0
            range_density = nunique / span

            is_index_like = bool(unique_ratio > 0.9 and is_monotonic_seq and range_density > 0.5)

            out[col] = {
                "skew": float(skew(vals)),
                "outlier_ratio": outlier_ratio,
                "nunique": nunique,
                "is_index_like": is_index_like,
                "is_constant": bool(nunique == 1),
            }
        return out

    # ==================================================================
    # MI (hybrid): num–num, cat–cat, cat–num
    # ==================================================================
    # ==================================================================
    # MI (hybrid): num–num, cat–cat, cat–num — robust gegen NaNs
    # ==================================================================
    def _compute_mi_hybrid(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Liefert eine symmetrische MI-Matrix (0..1) über alle Feature-Typen.
        - num–num: kNN-MI (sklearn) + Normalisierung über entropiebasierte Diskretisierung
        - cat–cat: mutual_info_score + Normalisierung über sqrt(Hx * Hy)
        - cat–num: num wird gebinnt, dann mutual_info_score + Normalisierung
        - robust gegen NaNs (füllt numerische Werte medianweise nur für Binning)
        """
        p = self.params

        # Sampling
        n_samples = min(len(df), p["subsample"])
        df_s = df.sample(n_samples, random_state=42) if len(df) > n_samples else df

        # Typen
        is_num = df_s.dtypes.apply(lambda dt: pd.api.types.is_numeric_dtype(dt))
        feats = df_s.columns.tolist()

        # -----------------------------------------------------------
        # Numerische Features: skalieren + diskretisieren
        # -----------------------------------------------------------
        scaler = StandardScaler()
        num_scaled: dict[str, np.ndarray] = {}
        num_binned: dict[str, np.ndarray] = {}

        if is_num.any():
            df_num = df_s.loc[:, is_num].dropna(axis=1, how="all")
            if not df_num.empty:
                # Scaler ignoriert NaNs intern -> ersetzt nachher
                arr_scaled = scaler.fit_transform(df_num.fillna(df_num.median(numeric_only=True)))
                for i, c in enumerate(df_num.columns):
                    num_scaled[c] = arr_scaled[:, i]

                # Diskretisierung (robust gegen NaNs)
                disc = KBinsDiscretizer(
                    n_bins=p["mi_n_bins"],
                    encode="ordinal",
                    strategy="quantile",
                )
                # Nur medianfüllen für Diskretisierung
                df_num_filled = df_num.fillna(df_num.median(numeric_only=True))
                try:
                    arr_binned = disc.fit_transform(df_num_filled.values)
                    for i, c in enumerate(df_num.columns):
                        num_binned[c] = arr_binned[:, i].astype(int)
                except Exception as e:
                    self.logger.warning(f"⚠️ KBinsDiscretizer failed: {e}")
                    for c in df_num.columns:
                        num_binned[c] = pd.qcut(
                            df_num_filled[c],
                            q=min(p['mi_n_bins'], max(2, df_num_filled[c].nunique())),
                            labels=False,
                            duplicates='drop'
                        ).fillna(0).astype(int).to_numpy()

        # -----------------------------------------------------------
        # Kategorische Features: codes
        # -----------------------------------------------------------
        cat_codes: dict[str, np.ndarray] = {}
        top_k = int(p["mi_top_categories"])
        for c in df_s.columns[~is_num]:
            s = df_s[c].astype("object").astype(str).fillna("__nan__")
            vc = s.value_counts()
            if len(vc) > top_k:
                keep = set(vc.head(top_k - 1).index)
                s = s.where(s.isin(keep), other="__other__")
            cat_codes[c] = pd.factorize(s, sort=False)[0].astype(int)

        # -----------------------------------------------------------
        # MI-Matrix (symmetrisch)
        # -----------------------------------------------------------
        mi = pd.DataFrame(0.0, index=feats, columns=feats, dtype=float)
        pairs = list(combinations(feats, 2))[: p["mi_max_pairs"]]

        def _entropy_from_codes(z: np.ndarray) -> float:
            return float(mutual_info_score(z, z))

        for a, b in pairs:
            try:
                a_is_num = bool(is_num.get(a, False))
                b_is_num = bool(is_num.get(b, False))

                # num–num
                if a_is_num and b_is_num and a in num_scaled and b in num_scaled:
                    x = np.nan_to_num(num_scaled[a]).reshape(-1, 1)
                    y = np.nan_to_num(num_scaled[b])
                    mi_val = float(
                        mutual_info_regression(
                            x,
                            y,
                            n_neighbors=p["mi_knn_neighbors"],
                            random_state=42,
                        )[0]
                    )
                    x_disc = num_binned[a]
                    y_disc = num_binned[b]
                    hx = _entropy_from_codes(x_disc)
                    hy = _entropy_from_codes(y_disc)
                    denom = np.sqrt(hx * hy)
                    mi_norm = mi_val / denom if denom > 0 else 0.0

                # cat–cat
                elif (not a_is_num) and (not b_is_num) and a in cat_codes and b in cat_codes:
                    x = cat_codes[a]
                    y = cat_codes[b]
                    mi_raw = float(mutual_info_score(x, y))
                    hx = _entropy_from_codes(x)
                    hy = _entropy_from_codes(y)
                    denom = np.sqrt(hx * hy)
                    mi_norm = mi_raw / denom if denom > 0 else 0.0

                # cat–num
                elif a_is_num != b_is_num:
                    if a_is_num:
                        num_name, cat_name = a, b
                    else:
                        num_name, cat_name = b, a

                    if num_name in num_binned and cat_name in cat_codes:
                        xn = num_binned[num_name]
                        xc = cat_codes[cat_name]
                        mi_raw = float(mutual_info_score(xn, xc))
                        hx = _entropy_from_codes(xn)
                        hy = _entropy_from_codes(xc)
                        denom = np.sqrt(hx * hy)
                        mi_norm = mi_raw / denom if denom > 0 else 0.0
                    else:
                        mi_norm = 0.0
                else:
                    mi_norm = 0.0

                mi.at[a, b] = mi.at[b, a] = mi_norm

            except Exception as e:
                self.logger.debug(f"MI failed for {a}-{b}: {e}")
                continue

        np.fill_diagonal(mi.values, 0.0)
        return mi


    # ==================================================================
    # Pairs / Typisierung
    # ==================================================================
    def _build_pair_types(self, pearson: pd.DataFrame, spearman: pd.DataFrame, mi: pd.DataFrame) -> List[Dict[str, Any]]:
        feats = pearson.index.tolist() if not pearson.empty else mi.index.tolist()
        pairs: List[Dict[str, Any]] = []

        for a, b in combinations(feats, 2):
            r = self._safe_get(pearson, a, b)
            rho = self._safe_get(spearman, a, b)
            mival = self._safe_get(mi, a, b)

            rtype = self._classify_relation(r, rho, mival)
            flags = self._detect_flags(a, b)
            pairs.append(dict(a=a, b=b, pearson=r, spearman=rho, mi=mival, type=rtype, flags=flags))
        return pairs

    def _classify_relation(self, r: float | None, rho: float | None, mi: float | None) -> str:
        p = self.params
        r_abs = abs(r) if pd.notna(r) else 0.0
        rho_abs = abs(rho) if pd.notna(rho) else 0.0
        mi_val = mi if pd.notna(mi) else 0.0

        if r_abs >= p["classify_linear_strong"]:
            return "strong linear"
        elif r_abs >= p["classify_linear_weak"]:
            return "weak linear"
        elif r_abs < p["classify_low_pearson_monotone"] and rho_abs >= p["classify_spearman_monotone"]:
            return "monotone nonlinear"
        elif r_abs < p["classify_low_pearson_nonlinear"] and mi_val > p["classify_mi_complex"]:
            return "complex nonlinear"
        else:
            return "independent"

    def _detect_flags(self, a: str, b: str) -> List[str]:
        flags: List[str] = []
        p = self.params
        for f in (a, b):
            d = self.distribution.get(f, {})
            if not d:
                continue
            if d.get("is_index_like"):
                flags.append("IDX")
            if d.get("is_constant"):
                flags.append("CONST")
            if d.get("skew", 0) > p["skew_flag_threshold"]:
                flags.append("SKEW")
            if d.get("outlier_ratio", 0) > p["outlier_flag_threshold"]:
                flags.append("OUT")
        return sorted(set(flags))

    # ==================================================================
    # Gruppen (mit Kennzahlen)
    # ==================================================================
    def _build_groups_with_stats(self, corr_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Clustert auf |corr| und liefert Gruppen inkl. avg/min/max |corr|.
        Ignoriert all-NaN Zeilen/Spalten & degenerate Fälle.
        """
        if corr_df is None or corr_df.empty or corr_df.shape[0] < 2:
            return []

        dist = 1 - corr_df.abs()
        dist = dist.dropna(axis=0, how="all").dropna(axis=1, how="all")

        if dist.empty or not np.isfinite(dist.values).any():
            return []

        # Falls Matrix praktisch Null ist (alles 0 → keine Distanzen)
        if np.allclose(np.nan_to_num(dist.values), 0):
            return []

        # Diagonale = 0
        np.fill_diagonal(dist.values, 0.0)

        try:
            Z = linkage(dist, method="average")
            labels = fcluster(Z, t=(1 - self.params["group_threshold"]), criterion="distance")
        except ValueError as e:
            self.logger.warning(f"⚠️ Skipping grouping (degenerate matrix): {e}")
            return []

        groups: List[Dict[str, Any]] = []
        cols = dist.columns.to_numpy()
        for lbl in np.unique(labels):
            members = cols[labels == lbl].tolist()
            if len(members) <= 1:
                continue
            # Kennzahlen
            vals = []
            for i, a in enumerate(members):
                for b in members[i + 1:]:
                    v = abs(corr_df.at[a, b]) if (a in corr_df.columns and b in corr_df.columns) else np.nan
                    if pd.notna(v):
                        vals.append(v)
            if len(vals) == 0:
                continue
            groups.append({
                "features": members,
                "avg_corr": float(np.mean(vals)),
                "min_corr": float(np.min(vals)),
                "max_corr": float(np.max(vals)),
            })

        groups.sort(key=lambda g: g["avg_corr"], reverse=True)
        return groups

    # ==================================================================
    # Isolation & Summary
    # ==================================================================
    def _find_isolated(self, pearson: pd.DataFrame) -> List[str]:
        if pearson is None or pearson.empty:
            return []
        iso = []
        for col in pearson.columns:
            col_series = pearson[col].abs().drop(labels=[col], errors="ignore")
            max_abs = col_series.max() if not col_series.empty else 0.0
            if pd.isna(max_abs) or max_abs < self.params["iso_threshold"]:
                iso.append(col)
        return iso

    def _build_summary(self, pearson: pd.DataFrame) -> Dict[str, Any]:
        if pearson is None or pearson.empty:
            return {
                "n_features": 0,
                "n_groups": 0,
                "n_isolated": len(self.isolated),
                "avg_abs_corr": 0.0,
                "strong_rel_density": 0.0,
            }
        abs_corr = pearson.abs()
        tri = abs_corr.where(np.triu(np.ones(abs_corr.shape), 1).astype(bool))
        vals = tri.stack()
        avg_abs_corr = float(vals.mean()) if not vals.empty else 0.0
        strong_density = float((vals > self.params["pearson_threshold"]).mean()) if not vals.empty else 0.0
        return {
            "n_features": int((~pearson.isna().all()).sum()),
            "n_groups": len(self.groups.get("pearson", [])),
            "n_isolated": len(self.isolated),
            "avg_abs_corr": avg_abs_corr,
            "strong_rel_density": strong_density,
        }

    # ==================================================================
    # Helpers
    # ==================================================================
    @staticmethod
    def _safe_get(df: pd.DataFrame, a: str, b: str) -> float | None:
        try:
            return float(df.at[a, b])
        except Exception:
            return np.nan


