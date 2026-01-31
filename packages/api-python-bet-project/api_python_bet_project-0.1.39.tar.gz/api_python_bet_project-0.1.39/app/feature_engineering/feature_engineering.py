# feature_engineering.py
# - MatchStatsCalculator: feature builder for matches, callable from main.py without interactive prompts.

import os
import numpy as np
import pandas as pd
from typing import Dict, List
from processing.teams.teams import enrich_with_geographic_and_temporal_features

class MatchStatsCalculator:
    """
    Build rolling-average and streak features for football matches across seasons.
    Designed to be driven from main.py (no interactive input).
    """

    def __init__(
        self,
        matches_csv_path: str,
        stadiums_csv_path: str,
        dataset_global_csv_path: str,
        comp_type: str,
        comp_country: str,
        features_config: Dict[str, any],
    ):
        self.matches_csv_path = matches_csv_path
        self.stadiums_csv_path = stadiums_csv_path
        self.columns_to_copy = features_config["fbref_informations"]
        self.comp_type = comp_type
        self.comp_country = comp_country
        self.columns_to_work = {
            metric: (config["thresholds"], config["operators"])
            for metric, config in features_config["fbref_features"].items()
        }
        self.existing_csv = dataset_global_csv_path

    # ----------------------------- Core stats -----------------------------
    def pythagorean_expectation(self, goals_for: float, goals_against: float, exponent: float = 1.7) -> float:
        """
        Compute Pythagorean win% expectation for a team based on goals for and against.
        This returns an estimated probability of "winning" a match.

        Args:
            goals_for: Average goals scored per match in the window
            goals_against: Average goals conceded per match in the window
            exponent: Sport-specific exponent (~1.7 for football)

        Returns:
            Win probability in [0,1] or np.nan if not computable
        """
        
        if not (np.isfinite(goals_for) and np.isfinite(goals_against)):
            return np.nan

        a = goals_for ** exponent
        b = goals_against ** exponent
        denom = a + b
        if denom <= 0:
            return np.nan
        return float(a / denom)

    def compute_pythagorean_features(self,
                                    df: pd.DataFrame,
                                    team: str,
                                    current_date: pd.Timestamp,
                                    location: str,
                                    windows=(5, 18)) -> dict:
        """
        Same idea as antes, pero:
        - si no hay partidos en la ventana, coverage_ratio = np.nan (no 0.0)
        - si no hay suficientes datos para momentum, momentum = np.nan
        """

        out = {}
        df = df.copy()
        df["date_of_match"] = pd.to_datetime(df["date_of_match"], errors="coerce")

        if location == "home":
            base = df[
                (df["date_of_match"] < current_date) &
                (df["home_team_name"] == team)
            ].sort_values("date_of_match")
            gf_col = "home_goals"
            ga_col = "away_goals"
            role_suffix = "_home"

        elif location == "away":
            base = df[
                (df["date_of_match"] < current_date) &
                (df["away_team_name"] == team)
            ].sort_values("date_of_match")
            gf_col = "away_goals"
            ga_col = "home_goals"
            role_suffix = "_away"

        else:
            return {}

        def clamp_tail(matches: pd.DataFrame, w: int):
            w = int(w)
            while w > 0:
                if len(matches) >= w:
                    return matches.tail(w), w
                w -= 1
            return matches.head(0), 0

        pytha_by_w = {}
        cov_by_w = {}

        for w in windows:
            sub, cov = clamp_tail(base, w)

            if cov == 0 or len(sub) == 0:  # Added len(sub) == 0 check
                winrate = np.nan
                cov_ratio = np.nan
            else:
                # Convert to numeric and handle empty results
                gf_series = pd.to_numeric(sub[gf_col], errors="coerce")
                ga_series = pd.to_numeric(sub[ga_col], errors="coerce")
                
                # Filter out NaN values
                gf_series = gf_series.dropna()
                ga_series = ga_series.dropna()
                
                # Check if we have valid data after dropping NaN
                if len(gf_series) == 0 or len(ga_series) == 0:
                    winrate = np.nan
                    cov_ratio = np.nan
                else:
                    gf_mean = gf_series.mean()
                    ga_mean = ga_series.mean()

                    winrate = self.pythagorean_expectation(
                        gf_mean, ga_mean
                    )

                    cov_ratio = cov / float(w)

            out[f"pytha_winrate{role_suffix}_w{w}"] = winrate
            out[f"pytha_coverage_ratio{role_suffix}_w{w}"] = cov_ratio

            pytha_by_w[w] = winrate
            cov_by_w[w] = cov

        # momentum (w5 - w18) solo tiene sentido si tengo las dos winrates
        if 5 in pytha_by_w and 18 in pytha_by_w:
            short_w = pytha_by_w[5]
            long_w = pytha_by_w[18]
            if np.isfinite(short_w) and np.isfinite(long_w):
                out[f"pytha_momentum{role_suffix}"] = float(short_w - long_w)
            else:
                out[f"pytha_momentum{role_suffix}"] = np.nan
        else:
            out[f"pytha_momentum{role_suffix}"] = np.nan

        return out
    
    def feature_engineering(
        self,
        column,
        team1,
        current_date,
        location,
        team2=None,
        between_mode=False,
        df=None,
        windows=(2, 5, 9, 14, 18),
        streak_thresholds_ops=None,
        streak_h2h=True,
        return_streaks=True,
    ):
        """
        Build the full feature block for a metric column and multiple windows,
        add cross-window derivatives, and compute streaks:
        - Legacy streaks vs fixed thresholds (values+operators you provide)
        - New streaks vs opponent's same column (swap home<->away)

        Everything derives FROM the provided `column` (e.g., 'home_possession' or 'away_xg').

        Returns
        -------
        dict
            Flat dict with per-window features, cross-window derivatives, and (optionally) streaks.
        """

        # -------- Helpers --------------------------------------------------------
        def swap_home_away(col: str) -> str:
            """Swap 'home' <-> 'away' substrings in the column name."""
            if "home" in col:
                return col.replace("home", "away")
            if "away" in col:
                return col.replace("away", "home")
            return col  # neutral column, no role to swap

        def clamp_window(matches: pd.DataFrame, w: int):
            """Apply fallback: try w, if not enough rows decrease until fits. Return (tail_df, coverage)."""
            w = int(w) if w is not None else 0
            while w > 0:
                if len(matches) >= w:
                    return matches.tail(w), w
                w -= 1
            return matches.head(0), 0

        def linear_trend(values: np.ndarray) -> float:
            """OLS slope over indices 0..n-1; returns nan for <2 points or if all nan."""
            n = len(values)
            if n < 2:
                return np.nan
            x = np.arange(n, dtype=float)
            y = np.asarray(values, dtype=float)
            mask = ~np.isnan(y)
            x, y = x[mask], y[mask]
            if len(y) < 2:
                return np.nan
            xm, ym = x.mean(), y.mean()
            denom = ((x - xm) ** 2).sum()
            if denom == 0:
                return np.nan
            return float(((x - xm) * (y - ym)).sum() / denom)

        def safe_mean(arr) -> float:
            arr = np.asarray(arr, dtype=float)
            valid_values = arr[~np.isnan(arr)]
            
            if len(valid_values) == 0:
                return np.nan
            
            return float(np.mean(valid_values))

        def safe_std(arr, ddof=0) -> float:
            """Calcula desviación estándar de forma segura"""
            arr = np.asarray(arr, dtype=float)
            # Filtrar valores válidos
            valid_values = arr[~np.isnan(arr)]
            
            if len(valid_values) <= ddof:  # Necesitas más valores que grados de libertad
                return np.nan
            
            return float(np.std(valid_values, ddof=ddof))

        # For legacy streaks vs value: accept both word and symbol operators
        def normalize_op(op_str: str) -> str:
            m = {
                "==": "eq",
                "=": "eq",
                "eq": "eq",
                ">": "gt",
                "gt": "gt",
                "<": "lt",
                "lt": "lt",
                ">=": "ge",
                "ge": "ge",
                "<=": "le",
                "le": "le",
            }
            return m.get(str(op_str).strip().lower(), None)

        # -------- Load & guards --------------------------------------------------
        if df is None or df.empty:
            df = self.get_dataframe()
        if df is None or df.empty:
            return {}

        df = df.copy()
        df["date_of_match"] = pd.to_datetime(df["date_of_match"], errors="coerce")
        current_date = pd.to_datetime(current_date, errors="coerce")

        windows = tuple(sorted(set(int(w) for w in windows if w and int(w) > 0)))

        # Base filter for team1 matches (role-aware) for all per-window features
        if location == "home":
            base = df[
                (df["date_of_match"] < current_date) & (df["home_team_name"] == team1)
            ].sort_values("date_of_match")
        elif location == "away":
            base = df[
                (df["date_of_match"] < current_date) & (df["away_team_name"] == team1)
            ].sort_values("date_of_match")
        else:  # both
            base = df[
                (df["date_of_match"] < current_date)
                & ((df["home_team_name"] == team1) | (df["away_team_name"] == team1))
            ].sort_values("date_of_match")

        swapped_col = swap_home_away(column)
        role_suffix = f"_{location}" if location in {"home", "away"} else "_both"

        # Metric name prefix (remove role tokens for cleaner naming)
        prefix = column.replace("home_", "").replace("away_", "")
        metric_prefix = prefix if prefix != column else column  # if neutral, keep as-is

        # Storage for cross-window derivatives
        per_w_team_for = {}
        per_w_matchup_diff = {}

        result = {}

        # -------- Per-window block (Point 2) -------------------------------------
        for w in windows:
            w_suffix = f"_w{w}"

            base_w, coverage = clamp_window(base, w)

            # team_for
            if coverage > 0 and column in base_w.columns:
                team_for_vals = pd.to_numeric(
                    base_w[column], errors="coerce"
                ).to_numpy()
                team_for = safe_mean(team_for_vals)
            else:
                team_for_vals = np.array([], dtype=float)
                team_for = np.nan

            # team_against (swap home<->away)
            if coverage > 0 and swapped_col in base_w.columns and swapped_col != column:
                team_against_vals = pd.to_numeric(
                    base_w[swapped_col], errors="coerce"
                ).to_numpy()
                team_against = safe_mean(team_against_vals)
            else:
                team_against_vals = np.array([], dtype=float)
                team_against = np.nan

            team_net = (
                float(team_for - team_against)
                if np.isfinite(team_for) and np.isfinite(team_against)
                else np.nan
            )

            # opp_allowed (role-exact proxy using swapped side in these same matches)
            if (
                location in {"home", "away"}
                and coverage > 0
                and swapped_col in base_w.columns
                and swapped_col != column
            ):
                opp_allowed = safe_mean(
                    pd.to_numeric(base_w[swapped_col], errors="coerce").to_numpy()
                )
            else:
                opp_allowed = np.nan

            matchup_diff = (
                float(team_for - opp_allowed)
                if np.isfinite(team_for) and np.isfinite(opp_allowed)
                else np.nan
            )
            matchup_ratio = (
                float(team_for / (opp_allowed + 1e-9))
                if np.isfinite(team_for) and np.isfinite(opp_allowed)
                else np.nan
            )

            # rival_avg (opposite side across team1's last matches)
            rival_side = (
                safe_mean(team_against_vals) if team_against_vals.size else np.nan
            )
            rival_gap = (
                float(team_for - rival_side)
                if np.isfinite(team_for) and np.isfinite(rival_side)
                else np.nan
            )

            # H2H (optional)
            if between_mode:
                if team2 is None:
                    raise ValueError(
                        "You must provide team2 when using between_mode=True."
                    )
                h2h = df[
                    (df["date_of_match"] < current_date)
                    & (
                        (
                            (df["home_team_name"] == team1)
                            & (df["away_team_name"] == team2)
                        )
                        | (
                            (df["home_team_name"] == team2)
                            & (df["away_team_name"] == team1)
                        )
                    )
                ].sort_values("date_of_match")
                h2h_w, h2h_cov = clamp_window(h2h, w)
                if h2h_cov > 0:
                    vals_for, vals_against = [], []
                    for _, r in h2h_w.iterrows():
                        if r["home_team_name"] == team1:
                            v_for = pd.to_numeric(
                                pd.Series([r.get(column, np.nan)]), errors="coerce"
                            ).iloc[0]
                            v_against = pd.to_numeric(
                                pd.Series([r.get(swapped_col, np.nan)]), errors="coerce"
                            ).iloc[0]
                        else:
                            v_for = pd.to_numeric(
                                pd.Series([r.get(swapped_col, np.nan)]), errors="coerce"
                            ).iloc[0]
                            v_against = pd.to_numeric(
                                pd.Series([r.get(column, np.nan)]), errors="coerce"
                            ).iloc[0]
                        vals_for.append(v_for)
                        vals_against.append(v_against)
                    h2h_for = safe_mean(vals_for)
                    h2h_against = safe_mean(vals_against)
                    h2h_net = (
                        float(h2h_for - h2h_against)
                        if np.isfinite(h2h_for) and np.isfinite(h2h_against)
                        else np.nan
                    )
                else:
                    h2h_for = h2h_against = h2h_net = np.nan
            else:
                h2h_for = h2h_against = h2h_net = np.nan

            # stability (std), trend (slope)
            if coverage > 0 and column in base_w.columns:
                seq_vals = pd.to_numeric(base_w[column], errors="coerce").to_numpy()
                stability = safe_std(seq_vals, ddof=0)
                trend = linear_trend(seq_vals)
            else:
                stability = trend = np.nan

            # z-score vs baseline w=18 (same role)
            if len(base) > 0 and column in base.columns:
                base18, cov18 = clamp_window(base, 18)
                if cov18 > 0:
                    bvals = pd.to_numeric(base18[column], errors="coerce").to_numpy()
                    bmean = safe_mean(bvals)
                    bstd = safe_std(bvals, ddof=0)
                    if (
                        np.isfinite(team_for)
                        and np.isfinite(bmean)
                        and np.isfinite(bstd)
                        and bstd > 0
                    ):
                        zscore = float((team_for - bmean) / bstd)
                    else:
                        zscore = np.nan
                else:
                    zscore = np.nan
            else:
                zscore = np.nan

            # Save per-window results
            k = f"{metric_prefix}"
            result[f"{k}_team_for{role_suffix}{w_suffix}"] = team_for
            result[f"{k}_team_against{role_suffix}{w_suffix}"] = team_against
            result[f"{k}_team_net{role_suffix}{w_suffix}"] = team_net

            result[f"{k}_opp_allowed{role_suffix}{w_suffix}"] = opp_allowed
            result[f"{k}_matchup_diff{role_suffix}{w_suffix}"] = matchup_diff
            result[f"{k}_matchup_ratio{role_suffix}{w_suffix}"] = matchup_ratio

            result[f"{k}_rival_side{role_suffix}{w_suffix}"] = rival_side
            result[f"{k}_rival_gap{role_suffix}{w_suffix}"] = rival_gap

            result[f"{k}_h2h_for{role_suffix}{w_suffix}"] = h2h_for
            result[f"{k}_h2h_against{role_suffix}{w_suffix}"] = h2h_against
            result[f"{k}_h2h_net{role_suffix}{w_suffix}"] = h2h_net

            result[f"{k}_stability{role_suffix}{w_suffix}"] = stability
            result[f"{k}_trend{role_suffix}{w_suffix}"] = trend
            result[f"{k}_zscore{role_suffix}{w_suffix}"] = zscore
            result[f"{k}_coverage{role_suffix}{w_suffix}"] = int(coverage)

            per_w_team_for[w] = team_for
            per_w_matchup_diff[w] = matchup_diff

        # -------- Cross-window derivatives (Point 3) ------------------------------
        if 5 in per_w_team_for and 18 in per_w_team_for:
            result[f"{metric_prefix}_mom_5_18{role_suffix}"] = (
                per_w_team_for[5] - per_w_team_for[18]
                if np.isfinite(per_w_team_for[5]) and np.isfinite(per_w_team_for[18])
                else np.nan
            )
        else:
            result[f"{metric_prefix}_mom_5_18{role_suffix}"] = np.nan

        if 9 in per_w_team_for and 18 in per_w_team_for:
            result[f"{metric_prefix}_mom_9_18{role_suffix}"] = (
                per_w_team_for[9] - per_w_team_for[18]
                if np.isfinite(per_w_team_for[9]) and np.isfinite(per_w_team_for[18])
                else np.nan
            )
        else:
            result[f"{metric_prefix}_mom_9_18{role_suffix}"] = np.nan

        if 5 in per_w_team_for and 9 in per_w_team_for:
            result[f"{metric_prefix}_accel_5_9{role_suffix}"] = (
                per_w_team_for[5] - per_w_team_for[9]
                if np.isfinite(per_w_team_for[5]) and np.isfinite(per_w_team_for[9])
                else np.nan
            )
        else:
            result[f"{metric_prefix}_accel_5_9{role_suffix}"] = np.nan

        stab_set = [
            per_w_team_for[w]
            for w in (5, 9, 14, 18)
            if w in per_w_team_for and np.isfinite(per_w_team_for[w])
        ]
        result[f"{metric_prefix}_stab_mix_5_9_14_18{role_suffix}"] = (
            float(np.std(stab_set, ddof=0)) if len(stab_set) >= 2 else np.nan
        )

        mix_set = [
            per_w_matchup_diff[w]
            for w in (5, 9, 18)
            if w in per_w_matchup_diff and np.isfinite(per_w_matchup_diff[w])
        ]
        result[f"{metric_prefix}_matchup_mix_5_9_18{role_suffix}"] = (
            float(np.mean(mix_set)) if len(mix_set) >= 1 else np.nan
        )

        # -------- Streaks (legacy thresholds + vs opponent) ----------------------
        if return_streaks:
            # Choose the dataset for streaks: H2H only or full base matches
            if streak_h2h:
                if team2 is None:
                    raise ValueError("You must provide team2 when streak_h2h=True.")
                streak_df = df[
                    (df["date_of_match"] < current_date)
                    & (
                        (
                            (df["home_team_name"] == team1)
                            & (df["away_team_name"] == team2)
                        )
                        | (
                            (df["home_team_name"] == team2)
                            & (df["away_team_name"] == team1)
                        )
                    )
                ].sort_values("date_of_match", ascending=False)
            else:
                streak_df = base.sort_values("date_of_match", ascending=False)

            # Legacy streaks vs thresholds (if provided)
            if streak_thresholds_ops is not None:
                values, ops = streak_thresholds_ops
                if len(values) != len(ops):
                    raise ValueError(
                        "streak_thresholds_ops must be like [[values...], [ops...]] with same length."
                    )
                col_num = (
                    pd.to_numeric(streak_df[column], errors="coerce")
                    if column in streak_df.columns
                    else None
                )
                col_raw = streak_df[column] if column in streak_df.columns else None

                def compare_val(x_num, x_raw, op_norm, val):
                    # Numeric path when possible
                    if (
                        x_num is not None
                        and pd.notna(x_num)
                        and isinstance(val, (int, float, np.number))
                    ):
                        if op_norm == "eq":
                            return x_num == float(val)
                        if op_norm == "gt":
                            return x_num > float(val)
                        if op_norm == "lt":
                            return x_num < float(val)
                        if op_norm == "ge":
                            return x_num >= float(val)
                        if op_norm == "le":
                            return x_num <= float(val)
                    # Fallback: raw equality only
                    if x_raw is None or pd.isna(x_raw):
                        return False
                    return (x_raw == val) if op_norm == "eq" else False

                for v, op in zip(values, ops):
                    op_norm = normalize_op(op)
                    key = f"{metric_prefix}_streak_{op_norm}_{str(v).replace(' ','_')}{role_suffix}"
                    if (
                        streak_df.empty
                        or column not in streak_df.columns
                        or op_norm is None
                    ):
                        result[key] = 0
                        continue
                    s = 0
                    for i in range(len(streak_df)):
                        x_num = (
                            float(col_num.iloc[i])
                            if col_num is not None and pd.notna(col_num.iloc[i])
                            else np.nan
                        )
                        x_raw = col_raw.iloc[i] if col_raw is not None else np.nan
                        if pd.isna(x_num) and (x_raw is None or pd.isna(x_raw)):
                            break
                        if compare_val(x_num, x_raw, op_norm, v):
                            s += 1
                        else:
                            break
                    result[key] = int(s)

            # New: streaks vs opponent's same column (swap home<->away)
            opp_col = swap_home_away(column)
            keys_map = {
                "gt": f"{metric_prefix}_streak_gt_opponent{role_suffix}",
                "lt": f"{metric_prefix}_streak_lt_opponent{role_suffix}",
                "ge": f"{metric_prefix}_streak_ge_opponent{role_suffix}",
                "le": f"{metric_prefix}_streak_le_opponent{role_suffix}",
                "eq": f"{metric_prefix}_streak_eq_opponent{role_suffix}",
            }
            if (
                not streak_df.empty
                and opp_col != column
                and opp_col in streak_df.columns
                and column in streak_df.columns
            ):
                a = pd.to_numeric(streak_df[column], errors="coerce").to_numpy()
                b = pd.to_numeric(streak_df[opp_col], errors="coerce").to_numpy()

                def streak_of(pred):
                    s = 0
                    for ai, bi in zip(a, b):
                        if np.isnan(ai) or np.isnan(bi):
                            break
                        if pred(ai, bi):
                            s += 1
                        else:
                            break
                    return int(s)

                result[keys_map["gt"]] = streak_of(lambda x, y: x > y)
                result[keys_map["lt"]] = streak_of(lambda x, y: x < y)
                result[keys_map["ge"]] = streak_of(lambda x, y: x >= y)
                result[keys_map["le"]] = streak_of(lambda x, y: x <= y)
                result[keys_map["eq"]] = streak_of(lambda x, y: x == y)
            else:
                for k in keys_map.values():
                    result[k] = 0

        return result

    def feature_engineering_bis(self,
                            base_features: dict,
                            role_suffix: str,
                            tag_suffix: str,
                            windows=(5, 18)):
        """
        We now standardize:
        - If coverage == 0 -> coverage_ratio = np.nan (not 0.0)
        - attack_index / defense_index / balance_index stay numéricos reales.
        - matchup_diff_momentum stays np.nan if unavailable.
        """

        short_w, long_w = windows[0], windows[-1]

        # 1) Build coverage_ratio_* safely
        for feat_key, feat_val in list(base_features.items()):
            for w in windows:
                cov_pattern = f"_coverage{role_suffix}_w{w}{tag_suffix}"
                if feat_key.endswith(cov_pattern):
                    ratio_key = feat_key.replace("_coverage", "_coverage_ratio")

                    # feat_val aquí es coverage (cuántos partidos efectivos)
                    # si coverage == 0 -> NaN, no 0.0
                    if np.isfinite(feat_val) and feat_val > 0 and w > 0:
                        base_features[ratio_key] = float(feat_val) / float(w)
                    else:
                        base_features[ratio_key] = np.nan

            # 2) attack_index / defense_index / balance_index
            # We build them per window, but only if we can infer the base metric.
            # We detect team_for / team_against / team_net patterns.
            # Example:
            #   "<metric>_team_for_home_w5_global"
            #   "<metric>_team_against_home_w5_global"
            #   "<metric>_team_net_home_w5_global"
            # We'll reconstruct those keys systematically instead of guessing metric.
        # We'll do a second pass after collecting metric prefixes:

        # Collect all metric prefixes for which we saw "team_for"
        metric_info = {}  # metric_prefix -> {w: {for, against, net, matchup_diff}}
        for feat_key, feat_val in base_features.items():
            # detect patterns:
            # "<metric>_team_for{role_suffix}_w{w}{tag_suffix}"
            for w in windows:
                suffix_for = f"_team_for{role_suffix}_w{w}{tag_suffix}"
                suffix_against = f"_team_against{role_suffix}_w{w}{tag_suffix}"
                suffix_net = f"_team_net{role_suffix}_w{w}{tag_suffix}"
                suffix_matchup = f"_matchup_diff{role_suffix}_w{w}{tag_suffix}"

                if feat_key.endswith(suffix_for):
                    metric_prefix = feat_key[: -len(suffix_for)]
                    metric_info.setdefault(metric_prefix, {}).setdefault(w, {})["for"] = feat_val

                if feat_key.endswith(suffix_against):
                    metric_prefix = feat_key[: -len(suffix_against)]
                    metric_info.setdefault(metric_prefix, {}).setdefault(w, {})["against"] = feat_val

                if feat_key.endswith(suffix_net):
                    metric_prefix = feat_key[: -len(suffix_net)]
                    metric_info.setdefault(metric_prefix, {}).setdefault(w, {})["net"] = feat_val

                if feat_key.endswith(suffix_matchup):
                    metric_prefix = feat_key[: -len(suffix_matchup)]
                    metric_info.setdefault(metric_prefix, {}).setdefault(w, {})["matchup"] = feat_val

        # Now build derived features from metric_info
        for metric_prefix, win_dict in metric_info.items():
            # For each window we can compute "attack_index", "defense_index", "balance_index"
            #   attack_index_wX  = team_for_wX
            #   defense_index_wX = - team_against_wX   (lower conceded => higher score)
            #   balance_index_wX = attack_index_wX + defense_index_wX
            for w, vals in win_dict.items():
                team_for_val = vals.get("for", np.nan)
                team_against_val = vals.get("against", np.nan)

                # attack_index
                base_features[
                    f"{metric_prefix}_attack_index{role_suffix}_w{w}{tag_suffix}"
                ] = float(team_for_val) if np.isfinite(team_for_val) else np.nan

                # defense_index (note the minus sign)
                defense_idx = (
                    -float(team_against_val) if np.isfinite(team_against_val) else np.nan
                )
                base_features[
                    f"{metric_prefix}_defense_index{role_suffix}_w{w}{tag_suffix}"
                ] = defense_idx

                # balance_index
                if np.isfinite(team_for_val) and np.isfinite(defense_idx):
                    base_features[
                        f"{metric_prefix}_balance_index{role_suffix}_w{w}{tag_suffix}"
                    ] = float(team_for_val) + float(defense_idx)
                else:
                    base_features[
                        f"{metric_prefix}_balance_index{role_suffix}_w{w}{tag_suffix}"
                    ] = np.nan

            # matchup_diff_momentum (short_w - long_w)
            short_val = win_dict.get(short_w, {}).get("matchup", np.nan)
            long_val = win_dict.get(long_w, {}).get("matchup", np.nan)
            mom_key = f"{metric_prefix}_matchup_diff_momentum{role_suffix}{tag_suffix}"
            if np.isfinite(short_val) and np.isfinite(long_val):
                base_features[mom_key] = float(short_val - long_val)
            else:
                base_features[mom_key] = np.nan

        # done; base_features is modified in-place
        return base_features

    # ------------------------------ Updates -------------------------------
    def update_columns(
        self, 
        combined_df: pd.DataFrame,
        choice_2=None, 
        start_index_global=0
    ):
        """
        Calculate features for specified rows in the dataset.
        Now properly handles three datasets with different lengths.
        
        Args:
            combined_df: Global dataset
            choice_2: Number of new rows to process
            start_index_global: Starting index for global dataset
        """

        df = combined_df.copy()

        if df.empty:
            print("[INFO] No data in DataFrame; skipping feature building.")
            self.new_df = pd.DataFrame()
            return

        # Normalize dates
        if "date_of_match" in df.columns:
            df["date_of_match"] = pd.to_datetime(df["date_of_match"], errors="coerce")

        # Check if competition column exists
        if "competition" not in df.columns:
            print("[WARNING] 'competition' column not found. Will only generate global features.")
            has_competition = False
        else:
            has_competition = True

        # Prepare indices for each dataset
        if choice_2 is not None:
            # Índices para GLOBAL dataset
            end_index_global = start_index_global + choice_2
            indices_global = list(range(start_index_global, end_index_global))
            
        else:
            indices_global = list(range(len(df)))

        # =========================================================================
        # ENRIQUECIMIENTO CON FEATURES GEOGRÁFICAS Y TEMPORALES
        # =========================================================================
        print("\n[FEATURES] Enriching with geographic and temporal features...")

        df = enrich_with_geographic_and_temporal_features(
            df_matches=df,
            df_all_matches=combined_df,
            stadiums_path=self.stadiums_csv_path,
            historical_matches_path=self.matches_csv_path,
            verbose=True
        )

        print("[FEATURES] Geographic and temporal features added successfully\n")

        # =========================================================================
        # PROCESAMIENTO DE FEATURES
        # =========================================================================
        # Storage separado para cada dataset
        new_values_global = {}

        home_away_location = ["home", "away"]

        # Iterate using GLOBAL dataset indices
        for i, df_idx_global in enumerate(indices_global):

            # Work with the row from GLOBAL dataset
            row_df = df.iloc[[df_idx_global]].copy()
            
            # Update row after calculating distances
            row = row_df.iloc[0]

            current_date = pd.to_datetime(row.get("date_of_match", None), errors="coerce")

            if pd.isna(current_date):
                print(f"  [WARNING] Row {df_idx_global}: Invalid date, skipping")
                continue

            competition = row.get("competition", None) if has_competition else None

            for home_away in home_away_location:
                if home_away == "home":
                    team = row.get("home_team_name", None)
                    vs_team = row.get("away_team_name", None)
                else:
                    team = row.get("away_team_name", None)
                    vs_team = row.get("home_team_name", None)

                if not team or not vs_team:
                    continue

                # Loop over metrics
                for base_metric, (values, operators) in self.columns_to_work.items():
                    metric_column = f"{home_away}_{base_metric}"

                    # ============================================================
                    # 1. GLOBAL FEATURES
                    # ============================================================
                    try:
                        features_global = self.feature_engineering(
                            column=metric_column,
                            team1=team,
                            team2=vs_team,
                            current_date=current_date,
                            location=home_away,
                            df=df,
                            windows=(2, 5, 9, 14, 18),
                            between_mode=True,
                            streak_thresholds_ops=[values, operators],
                            streak_h2h=True,
                            return_streaks=True,
                        )

                        role_suffix = f"_{home_away}"
                        features_global = self.feature_engineering_bis(
                            base_features=features_global,
                            role_suffix=role_suffix,
                            tag_suffix="_global",
                            windows=(5, 18),
                        )

                        for col_name, val in features_global.items():
                            new_col_name = f"{col_name}_global" if not col_name.endswith("_global") else col_name
                            # Guardar en los 3 datasets con SUS índices correspondientes
                            new_values_global.setdefault(new_col_name, {})[df_idx_global] = val

                    except Exception as e:
                        print(f"  [ERROR] Row {df_idx_global}, {home_away} {base_metric} (global): {e}")

                    # ============================================================
                    # 2. COMPETITION-SPECIFIC FEATURES
                    # ============================================================
                    if has_competition and competition:
                        try:
                            df_comp = df[df["competition"] == competition].copy()

                            features_comp = self.feature_engineering(
                                column=metric_column,
                                team1=team,
                                team2=vs_team,
                                current_date=current_date,
                                location=home_away,
                                df=df_comp,
                                windows=(2, 5, 9, 14, 18),
                                between_mode=True,
                                streak_thresholds_ops=[values, operators],
                                streak_h2h=True,
                                return_streaks=True,
                            )

                            role_suffix = f"_{home_away}"
                            features_comp = self.feature_engineering_bis(
                                base_features=features_comp,
                                role_suffix=role_suffix,
                                tag_suffix="_comp",
                                windows=(5, 18),
                            )

                            for col_name, val in features_comp.items():
                                new_col_name = f"{col_name}_comp" if not col_name.endswith("_comp") else col_name
                                new_values_global.setdefault(new_col_name, {})[df_idx_global] = val

                        except Exception as e:
                            print(f"  [ERROR] Row {df_idx_global}, {home_away} {base_metric} (comp): {e}")

                # ============================================================
                # 3. PYTHAGOREAN FEATURES (global)
                # ============================================================
                try:
                    pytha_global = self.compute_pythagorean_features(
                        df=df,
                        team=team,
                        current_date=current_date,
                        location=home_away,
                        windows=(5, 18),
                    )
                    for col_name, val in pytha_global.items():
                        new_col_name = f"{col_name}_global"
                        new_values_global.setdefault(new_col_name, {})[df_idx_global] = val
                except Exception as e:
                    print(f"  [ERROR] Row {df_idx_global}, {home_away} Pythagorean (global): {e}")

                # ============================================================
                # 4. PYTHAGOREAN FEATURES (competition-specific)
                # ============================================================
                if has_competition and competition:
                    try:
                        df_comp = df[df["competition"] == competition].copy()
                        pytha_comp = self.compute_pythagorean_features(
                            df=df_comp,
                            team=team,
                            current_date=current_date,
                            location=home_away,
                            windows=(5, 18),
                        )
                        for col_name, val in pytha_comp.items():
                            new_col_name = f"{col_name}_comp"
                            new_values_global.setdefault(new_col_name, {})[df_idx_global] = val
                    except Exception as e:
                        print(f"  [ERROR] Row {df_idx_global}, {home_away} Pythagorean (comp): {e}")

        # =========================================================================
        # ACTUALIZAR LOS 3 DATAFRAMES CON SUS RESPECTIVOS VALORES
        # =========================================================================
        
        # Convertir a DataFrames
        new_values_df_global = pd.DataFrame.from_dict(new_values_global, orient="columns")

        # Identificar columnas faltantes
        missing_cols_global = [col for col in new_values_df_global.columns if col not in df.columns]

        # Agregar todas las columnas faltantes de una vez usando concat
        if missing_cols_global:
            missing_df = pd.DataFrame(np.nan, index=df.index, columns=missing_cols_global)
            df = pd.concat([df, missing_df], axis=1)

        # =========================================================================
        # Actualizar valores en cada DataFrame
        # =========================================================================
        
        # Actualizar valores en GLOBAL
        for col in new_values_df_global.columns:
            for idx in new_values_df_global.index:
                if idx in df.index:
                    df.at[idx, col] = new_values_df_global.at[idx, col]
        
        basic_cols = [col for col in self.columns_to_copy if col in df.columns]
        feature_cols = [col for col in df.columns if col not in basic_cols]
        ordered_cols = basic_cols + feature_cols
        
        df = df[ordered_cols]

        # Guardar los 3 DataFrames
        df.to_csv(self.existing_csv, index=False)

    def data_update_dataset(
        self, match_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Update dataset with new matches and calculate features.

        Args:
            match_df: DataFrame with newly scraped matches

        Returns:
            DataFrame with new matches and calculated features
        """

        # =========================================================================
        # 1. Load existing dataset
        # =========================================================================
        
        # GLOBAL dataset
        if os.path.exists(self.existing_csv):
            existing_df = pd.read_csv(self.existing_csv, low_memory=False)
            original_length = len(existing_df)
        else:
            existing_df = pd.DataFrame()
            original_length = 0

        # =========================================================================
        # 2. Extract only needed columns from match_df
        # =========================================================================
        available_cols = [c for c in self.columns_to_copy if c in match_df.columns]

        if not available_cols:
            print("[ERROR] No columns from columns_to_copy found in match_df")
            self.new_df = pd.DataFrame()
            return self.new_df

        new_rows = match_df[available_cols].copy()

        # =========================================================================
        # 3. Check if there are actually new matches
        # =========================================================================
        if new_rows.empty:
            self.new_df = pd.DataFrame()
            return self.new_df

        # =========================================================================
        # 4. Normalize dates
        # =========================================================================
        if "date_of_match" in new_rows.columns:
            new_rows["date_of_match"] = pd.to_datetime(
                new_rows["date_of_match"], errors="coerce"
            )

        # =========================================================================
        # 5. Alinear columnas ANTES de concatenar
        # =========================================================================
        # Obtener todas las columnas únicas
        all_cols = list(set(
            existing_df.columns.tolist() + 
            new_rows.columns.tolist()
        ))
        
        # Agregar columnas faltantes a cada DataFrame
        missing_cols_existing = [col for col in all_cols if col not in existing_df.columns]
        if missing_cols_existing:
            missing_df = pd.DataFrame(np.nan, index=existing_df.index, columns=missing_cols_existing)
            existing_df = pd.concat([existing_df, missing_df], axis=1)

        missing_cols_new = [col for col in all_cols if col not in new_rows.columns]
        if missing_cols_new:
            missing_df = pd.DataFrame(np.nan, index=new_rows.index, columns=missing_cols_new)
            new_rows = pd.concat([new_rows, missing_df], axis=1)
        
        # =========================================================================
        # 6. Concatenar con columnas alineadas
        # =========================================================================
        if existing_df.empty:
            combined_df_global = new_rows[all_cols].copy()
        else:
            combined_df_global = pd.concat([existing_df[all_cols], new_rows[all_cols]], ignore_index=True)

        # Columnas básicas (de columns_to_copy) que deben ir primero
        basic_cols = [col for col in self.columns_to_copy if col in combined_df_global.columns]
        
        # Columnas de features (el resto)
        feature_cols = [col for col in combined_df_global.columns if col not in basic_cols]
        
        # Orden deseado: básicas primero, features después
        ordered_cols = basic_cols + feature_cols
        
        # Reordenar los 3 DataFrames
        combined_df_global = combined_df_global[ordered_cols]

        # =========================================================================
        # 8. Calcular features SOLO para nuevas filas en el dataset
        # =========================================================================
        start_index_global = original_length
        choice_2 = len(new_rows)

        # Llamar update_columns con los índices correctos para el dataset
        self.update_columns(
            combined_df_global,
            choice_2=choice_2, 
            start_index_global=start_index_global
        )

        return new_rows