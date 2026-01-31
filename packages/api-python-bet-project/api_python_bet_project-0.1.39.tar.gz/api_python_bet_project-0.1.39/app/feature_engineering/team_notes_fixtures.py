"""
Team notes from raw CSVs (fresh each run, uses last match):
- Outfield per90 with your core metrics by 5 role buckets (CD/FB/MF/WG/ST)
- GK robust features (psxG-GA/90, save%, claims%, sweeper, distribution) + keeper country kept
- Strict LT/ST windows (LT=18, ST=5) with z-score by role and subset + shrink to global
- Dynamic minutes expectation by team (rolling last 8 team matches)
- Formation -> role slots + depth weights
- Availability (external injured+suspended) + AUTO-SUSPENSIONS by competition (YC multiples of 5, RC diff)
- Country change penalty (blended while adapting), age curve by role
- Writes 8 notes + unavailable counts directly into df_matches
"""

from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import pandas as pd
import re
from collections import Counter

from utils.format import normalize_name

# ===========================
# Configuration
# ===========================

CORE_METRICS_BY_ROLE: Dict[str, List[str]] = {
    "CD": [
        "PlayersTackles+Interceptions",
        "PlayersClearances",
        "PlayersAerialsWon",
        "PlayersShotsBlocked",
        "PlayersBallsBlocked",
    ],
    "FB": [
        "PlayersDistanceProgression",
        "PlayersCrosses",
        "PlayersTackles+Interceptions",
        "PlayersDribblesCompleted",
        "PlayersAwayPenaltyAreaTouches",
        "PlayersAttemptedDribbles",
        "PlayersBallsBlocked",
        "PlayersShotsBlocked",
        "PlayersClearances",
    ],
    "MF": [
        "PlayersDistanceProgression",
        "PlayersLiveBallPasses",
        "PlayersKeyPasses",
        "PlayersTackles+Interceptions",
        "PlayersBallCarries",
        "PlayersDistanceCarried",
        "PlayersThroughPasses",
        "PlayersExpectedAssistance",
        "PlayersDeadBallPasses",
        "PlayersBallsBlocked",
        "PlayersShotsBlocked",
        "PlayersClearances",
    ],
    "WG": [
        "PlayersExpectedAssistance",
        "PlayersKeyPasses",
        "PlayersCrosses",
        "PlayersDribblesCompleted",
        "PlayersAwayPenaltyAreaTouches",
        "PlayersForwardCarries",
        "PlayersShots",
        "PlayersShotsOnTarget",
        "PlayersDistanceProgression",
        "PlayersThroughPasses",
        "PlayersBallCarries",
        "PlayersDistanceCarried",
        "PlayersAttemptedDribbles",
    ],
    "ST": [
        "PlayersShots",
        "PlayersShotsOnTarget",
        "PlayersExpectedAssistance",
        "PlayersKeyPasses",
        "PlayersAwayPenaltyAreaTouches",
        "PlayersThroughPasses",
        "PlayersDribblesCompleted",
        "PlayersAttemptedDribbles",
        "PlayersAerialsWon",
    ],
}
OUTFIELD_BASE_METRICS: List[str] = sorted({m for ms in CORE_METRICS_BY_ROLE.values() for m in ms})

KEEPER_BASE_METRICS: List[str] = [
    "KeepersShotsOnTargetAgainst",
    "KeepersGoalsAgainst",
    "KeepersSaved",
    "KeepersxG",
    "KeepersPasses",
    "KeepersAttemptedPasses",
    "KeepersPassesDistance",
    "KeepersPassesLaunched",
    "KeepersAttemptedPassesLaunched",
    "KeepersAttemptedKicks",
    "KeepersKicksDistance",
    "KeepersCrosses",
    "KeepersCrossesStopped",
    "KeepersActionsOutsideArea",
    "KeepersDistanceActionsArea",
    "Keepers%Saved",
    "Keepers%CompletedPasses",
    "Keepers%CompletedPassesLaunched",
    "Keepers%Kicks",
    "Keepers%CrossesStopped",
]

KEEPER_CORE_NAMES: List[str] = [
    "gk_psxg_minus_ga_per90",
    "gk_save_pct",
    "gk_claims_per90",
    "gk_claims_pct",
    "gk_actions_outside_area_per90",
    "gk_distance_actions_area_per90",
    "gk_passes_per90",
    "gk_launches_per90",
    "gk_passes_distance_per90",
    "gk_kicks_distance_per90",
]

DEFAULT_DEPTH_WEIGHTS = [1.0, 0.7, 0.4, 0.2]
ST_MAX_MATCHES = 5
LT_MAX_MATCHES = 18
ROLLING_MINUTES_WINDOW = 8
M_SHRINK = 4
LEAGUE_FACTOR_DEFAULT = 0.95
COUNTRY_FACTOR_DEFAULT = 0.90
AGE_PEAKS = {"ST": (24, 27), "WG": (24, 27), "MF": (26, 29), "FB": (26, 29), "CD": (28, 32), "GK": (28, 32)}

# ===========================
# Helpers
# ===========================

def normalize_role(position: str) -> str:
    p = (position or "").strip().upper()
    if p in {"CB","RCB","LCB","CBR","CBL","SW"}: return "CD"
    if p in {"RB","LB","RWB","LWB","FB","RFB","LFB","WB"}: return "FB"
    if p in {"DM","CDM","CM","RCM","LCM","MC","AM","CAM","6","8","10"}: return "MF"
    if p in {"LW","RW","WF","W","LWF","RWF","LM","RM"}: return "WG"
    if p in {"FW","CF","ST","9","SS"}: return "ST"
    return "MF"

def pick_team_name_column(df: pd.DataFrame) -> Optional[str]:
    for c in ["team_name","name","club","squad","Equipo","equipo","TeamName","Club","Squad","team"]:
        if c in df.columns:
            return c
    return None

def pick_country_column(df: pd.DataFrame, is_gk: bool=False) -> Optional[str]:
    cands = (["country","Country","PlayersCountry","PlayersNationality"]
             if not is_gk else ["country","Country","KeepersCountry","KeepersNationality"])
    for c in cands:
        if c in df.columns:
            return c
    return None

def latest_country_for_player(df_all: pd.DataFrame, slug: str, is_gk: bool=False) -> Optional[str]:
    ccol = pick_country_column(df_all, is_gk=is_gk)
    if not ccol: return None
    d = df_all[df_all["player_slug"] == slug]
    if d.empty: return None
    return str(d[ccol].dropna().astype(str).tail(1).iloc[0])

def age_factor(age: Optional[float], role_bucket: str) -> float:
    if age is None or pd.isna(age): return 1.0
    rb = "GK" if role_bucket == "GK" else (role_bucket if role_bucket in AGE_PEAKS else "MF")
    lo, hi = AGE_PEAKS[rb]; a = float(age)
    if a < lo: return max(0.85, 1.0 - 0.01*(lo - a))
    if a > hi: return max(0.85, 1.0 - 0.01*(a - hi))
    return 1.0

def parse_formation_slots(formation: str) -> Dict[str, int]:
    """
    Parse formation string to role slots.
    Handles both 3-line (4-3-3) and 4-line (4-2-3-1, 4-4-1-1) formations.
    
    Args:
        formation: Formation string (e.g., "4-3-3", "4-2-3-1", "3-5-2")
    
    Returns:
        Dict with role buckets: GK, CD, FB, MF, WG, ST
    
    Examples:
        "4-3-3" → {"GK":1, "CD":2, "FB":2, "MF":3, "WG":2, "ST":1}
        "4-2-3-1" → {"GK":1, "CD":2, "FB":2, "MF":5, "WG":0, "ST":1}
        "4-4-1-1" → {"GK":1, "CD":2, "FB":2, "MF":5, "WG":0, "ST":1}
        "3-5-2" → {"GK":1, "CD":1, "FB":2, "MF":5, "WG":1, "ST":1}
    """
    if not formation:
        return {"GK":1,"CD":2,"FB":2,"MF":3,"WG":2,"ST":1}
    
    nums = [int(x) for x in re.findall(r"\d+", formation)]
    
    if len(nums) < 2:
        return {"GK":1,"CD":2,"FB":2,"MF":3,"WG":2,"ST":1}
    
    defenders = nums[0]
    
    # Check if it's a 4-line formation (has 4 numbers)
    if len(nums) == 4:
        # 4-line formation: Def-DM-AM-FW (e.g., 4-2-3-1, 4-4-1-1)
        dm = nums[1]           # Defensive midfielders
        am = nums[2]           # Attacking midfielders / wingers
        forwards = nums[3]     # Strikers
        
        # Combine all midfielders
        mids = dm + am
        
    elif len(nums) == 3:
        # 3-line formation: Def-Mid-Fwd (e.g., 4-3-3, 4-4-2)
        mids = nums[1]
        forwards = nums[2]
        
    else:
        # Fallback for unusual formats
        mids = nums[1] if len(nums) > 1 else 3
        forwards = max(1, 10 - defenders - mids)
    
    # Parse defenders into center backs and fullbacks
    cd = max(2, defenders - 2)  # At least 2 center backs
    fb = defenders - cd          # Remaining defenders are fullbacks
    
    # Parse forwards into wingers and strikers
    if forwards >= 3:
        wg = forwards - 1  # Most are wingers
        st = 1             # One striker
    elif forwards == 2:
        wg = 1
        st = 1
    else:  # forwards == 1 or 0
        wg = 0
        st = max(1, forwards)
    
    return {"GK":1, "CD":cd, "FB":fb, "MF":mids, "WG":wg, "ST":st}

def winsorize(series: pd.Series, lo: float=0.01, hi: float=0.99) -> pd.Series:
    qlo, qhi = series.quantile(lo), series.quantile(hi)
    return series.clip(lower=qlo, upper=qhi)

def z_by_role(df_role: pd.DataFrame, cols: List[str], role_col: str="role_bucket") -> pd.DataFrame:
    out = df_role.copy()
    for c in cols:
        mu = out.groupby(role_col)[c].transform("mean")
        sd = out.groupby(role_col)[c].transform("std").replace(0, np.nan).fillna(1.0)
        out[f"z_{c}"] = (out[c] - mu) / sd
    return out

def transfer_blend_factor(n_new_matches: int, cap: int=6) -> float:
    return min(1.0, max(0.0, n_new_matches/float(cap)))

def count_matches_with_team(df_all: pd.DataFrame, slug: str, team: str, since: Optional[str]=None) -> int:
    d = df_all[(df_all["player_slug"]==slug) & (df_all["team_name"].astype(str)==str(team))]
    if since and ("match_date" in d.columns or "date" in d.columns):
        col = "match_date" if "match_date" in d.columns else "date"
        d = d[d[col] >= since]
    return int(len(d))

# ===========================
# Loading & feature builders
# ===========================

def load_outfield(players_csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(players_csv_path, low_memory=False)
    if "Players" not in df.columns and "layers" in df.columns:
        df = df.rename(columns={"layers": "Players"})
    df["player_slug"] = df["Players"].astype(str).map(normalize_name)
    if "Position" not in df.columns: df["Position"] = ""
    df["role_bucket"] = df["Position"].map(normalize_role)
    if "PlayersMinutes" not in df.columns: df["PlayersMinutes"] = 0.0
    tcol = pick_team_name_column(df)
    if tcol and tcol != "team_name": df = df.rename(columns={tcol: "team_name"})
    if "team" not in df.columns: df["team"] = ""
    # ensure base metric columns
    for m in OUTFIELD_BASE_METRICS:
        if m not in df.columns: df[m] = 0.0
    # new cards + gameweek
    for c in ["PlayersYellowCards","PlayersRedCards","gameweek","competition_type"]:
        if c not in df.columns:
            df[c] = 0
    # parse datetime if present
    for dc in ["match_date","date","timestamp"]:
        if dc in df.columns:
            try: df[dc] = pd.to_datetime(df[dc], utc=True, errors="coerce")
            except Exception: pass
    return df

def add_per90_outfield(df: pd.DataFrame, winsor: bool=True, lo: float=0.01, hi: float=0.99) -> pd.DataFrame:
    g = df.copy()
    denom = g["PlayersMinutes"].fillna(0.0).clip(lower=1.0)
    factor = 90.0 / denom
    for m in OUTFIELD_BASE_METRICS:
        col = f"{m}_per90"
        g[col] = g[m].astype(float).fillna(0.0) * factor
        if winsor:
            g[col] = winsorize(g[col], lo=lo, hi=hi)
    return g

def load_keepers(keepers_csv_path: str) -> pd.DataFrame:
    gk = pd.read_csv(keepers_csv_path, low_memory=False)
    if "Keepers" in gk.columns and "Players" not in gk.columns:
        gk = gk.rename(columns={"Keepers": "Players"})
    gk["player_slug"] = gk["Players"].astype(str).map(normalize_name)
    gk["role_bucket"] = "GK"
    tcol = pick_team_name_column(gk)
    if tcol and tcol != "team_name": gk = gk.rename(columns={tcol: "team_name"})
    if "team" not in gk.columns: gk["team"] = ""
    if "KeepersMinutes" not in gk.columns: gk["KeepersMinutes"] = 0.0
    for c in ["PlayersYellowCards","PlayersRedCards","gameweek","competition_type"]:
        if c not in gk.columns:
            gk[c] = 0
    for dc in ["match_date","date","timestamp"]:
        if dc in gk.columns:
            try: gk[dc] = pd.to_datetime(gk[dc], utc=True, errors="coerce")
            except Exception: pass
    for c in KEEPER_BASE_METRICS:
        if c not in gk.columns: gk[c] = 0.0
    ccol = pick_country_column(gk, is_gk=True)
    if ccol and ccol != "country":
        gk = gk.rename(columns={ccol: "country"})
    return gk

def build_keeper_core(gk: pd.DataFrame) -> pd.DataFrame:
    g = gk.copy()
    denom = g["KeepersMinutes"].fillna(0.0).clip(lower=1.0)
    factor = 90.0 / denom
    if "Keepers%Saved" in g.columns and g["Keepers%Saved"].notna().any():
        g["gk_save_pct"] = g["Keepers%Saved"].astype(float)/100.0
    else:
        g["gk_save_pct"] = (g["KeepersSaved"].astype(float) /
                            g["KeepersShotsOnTargetAgainst"].replace(0, np.nan)).fillna(0.0)
    if "Keepers%CrossesStopped" in g.columns and g["Keepers%CrossesStopped"].notna().any():
        g["gk_claims_pct"] = g["Keepers%CrossesStopped"].astype(float)/100.0
    else:
        g["gk_claims_pct"] = (g["KeepersCrossesStopped"].astype(float) /
                              g["KeepersCrosses"].replace(0, np.nan)).fillna(0.0)
    def p90(col): return g[col].astype(float) * factor if col in g.columns else 0.0 * factor
    g["gk_psxg_minus_ga_per90"]         = p90("KeepersxG") - p90("KeepersGoalsAgainst")
    g["gk_claims_per90"]                = p90("KeepersCrossesStopped")
    g["gk_actions_outside_area_per90"]  = p90("KeepersActionsOutsideArea")
    g["gk_distance_actions_area_per90"] = p90("KeepersDistanceActionsArea")
    g["gk_passes_per90"]                = p90("KeepersPasses")
    g["gk_launches_per90"]              = p90("KeepersPassesLaunched")
    g["gk_passes_distance_per90"]       = p90("KeepersPassesDistance")
    g["gk_kicks_distance_per90"]        = p90("KeepersKicksDistance")
    keep_cols = ["Players","player_slug","team_name","team","KeepersMinutes","role_bucket","country",
                 "PlayersYellowCards","PlayersRedCards","gameweek","competition_type"] + KEEPER_CORE_NAMES
    for c in keep_cols:
        if c not in g.columns:
            g[c] = 0 if c in {"PlayersYellowCards","PlayersRedCards","gameweek"} else ""
    return g[keep_cols]

# ===========================
# IS computation (unchanged core)
# ===========================

def _subset_mask(df: pd.DataFrame, competition: Optional[str], venue: Optional[str]) -> pd.Series:
    m = pd.Series(True, index=df.index)
    if competition is not None and "competition_type" in df.columns:
        m &= df["competition_type"].astype(str) == str(competition)
    if venue is not None and "team" in df.columns:
        m &= df["team"].str.lower() == venue.lower()
    return m

def _last_k_mean(df: pd.DataFrame, k: int, group_cols: List[str], value_cols: List[str], order_col: Optional[str]) -> pd.DataFrame:
    if order_col and order_col in df.columns:
        df = df.sort_values(order_col)
    pieces = []
    for _, g in df.groupby(group_cols, group_keys=False):
        gg = g.tail(k)
        if gg.empty: continue
        pieces.append(gg.groupby(group_cols).mean(numeric_only=True))
    if not pieces:
        idx = pd.MultiIndex.from_frame(df[group_cols].drop_duplicates())
        return pd.DataFrame(index=idx, columns=value_cols)
    out = pd.concat(pieces, axis=0).groupby(level=list(range(len(group_cols)))).mean(numeric_only=True)
    for c in value_cols:
        if c not in out.columns: out[c] = np.nan
    return out[value_cols]

def _compute_outfield_IS_for_subset(dfp: pd.DataFrame, competition: Optional[str], venue: Optional[str],
                                    order_col: Optional[str]) -> pd.DataFrame:
    mask = _subset_mask(dfp, competition, venue)
    sub = dfp[mask].copy()
    if sub.empty:
        return pd.DataFrame(columns=["player_slug","role_bucket","IS"]).astype({"player_slug":str,"role_bucket":str})
    per90_cols = sorted({f"{m}_per90" for ms in CORE_METRICS_BY_ROLE.values() for m in ms if f"{m}_per90" in sub.columns})
    if not per90_cols:
        out = sub[["player_slug","role_bucket"]].drop_duplicates().copy(); out["IS"]=0.0; return out
    group_cols = ["player_slug","role_bucket"]
    LT = _last_k_mean(sub[per90_cols + group_cols + ([order_col] if order_col in sub.columns else [])],
                      LT_MAX_MATCHES, group_cols, per90_cols, order_col)
    ST = _last_k_mean(sub[per90_cols + group_cols + ([order_col] if order_col in sub.columns else [])],
                      ST_MAX_MATCHES, group_cols, per90_cols, order_col)
    def _z(frame: pd.DataFrame, tag: str) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(columns=["player_slug","role_bucket",f"IS_{tag}"]).set_index(["player_slug","role_bucket"])
        Z = frame.reset_index()
        Z = z_by_role(Z, per90_cols, role_col="role_bucket")
        Z[f"IS_{tag}"] = Z[[f"z_{c}" for c in per90_cols if f"z_{c}" in Z.columns]].mean(axis=1)
        return Z.set_index(["player_slug","role_bucket"])[[f"IS_{tag}"]]
    LTz = _z(LT,"LT"); STz = _z(ST,"ST")
    idx = set(LTz.index) | set(STz.index)
    if not idx:
        out = sub[["player_slug","role_bucket"]].drop_duplicates().copy(); out["IS"]=0.0; return out
    idx = pd.MultiIndex.from_tuples(list(idx), names=["player_slug","role_bucket"])
    comb = pd.DataFrame(index=idx).join(LTz, how="left").join(STz, how="left")
    comb["IS"] = np.where(comb["IS_LT"].notna() & comb["IS_ST"].notna(),
                          0.6*comb["IS_LT"] + 0.4*comb["IS_ST"],
                          comb["IS_LT"].fillna(0.0) + comb["IS_ST"].fillna(0.0))
    return comb.reset_index()[["player_slug","role_bucket","IS"]]

def _compute_gk_IS_for_subset(dfg: pd.DataFrame, competition: Optional[str], venue: Optional[str],
                              order_col: Optional[str]) -> pd.DataFrame:
    mask = _subset_mask(dfg, competition, venue)
    sub = dfg[mask].copy()
    if sub.empty:
        return pd.DataFrame(columns=["player_slug","role_bucket","IS"]).astype({"player_slug":str,"role_bucket":str})
    value_cols = [c for c in KEEPER_CORE_NAMES if c in sub.columns]
    if not value_cols:
        out = sub[["player_slug","role_bucket"]].drop_duplicates().copy(); out["IS"]=0.0; return out
    group_cols = ["player_slug","role_bucket"]
    LT = _last_k_mean(sub[value_cols + group_cols + ([order_col] if order_col in sub.columns else [])],
                      LT_MAX_MATCHES, group_cols, value_cols, order_col)
    ST = _last_k_mean(sub[value_cols + group_cols + ([order_col] if order_col in sub.columns else [])],
                      ST_MAX_MATCHES, group_cols, value_cols, order_col)
    def _z(frame: pd.DataFrame, tag: str) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(columns=["player_slug","role_bucket",f"IS_{tag}"]).set_index(["player_slug","role_bucket"])
        Z = frame.reset_index()
        for c in value_cols:
            mu, sd = Z[c].mean(), Z[c].std(ddof=0)
            Z[f"z_{c}"] = (Z[c] - mu) / (sd if sd > 1e-9 else 1.0)
        Z[f"IS_{tag}"] = Z[[f"z_{c}" for c in value_cols]].mean(axis=1)
        return Z.set_index(["player_slug","role_bucket"])[[f"IS_{tag}"]]
    LTz = _z(LT,"LT"); STz = _z(ST,"ST")
    idx = set(LTz.index) | set(STz.index)
    if not idx:
        out = sub[["player_slug","role_bucket"]].drop_duplicates().copy(); out["IS"]=0.0; return out
    idx = pd.MultiIndex.from_tuples(list(idx), names=["player_slug","role_bucket"])
    comb = pd.DataFrame(index=idx).join(LTz, how="left").join(STz, how="left")
    comb["IS"] = np.where(comb["IS_LT"].notna() & comb["IS_ST"].notna(),
                          0.6*comb["IS_LT"] + 0.4*comb["IS_ST"],
                          comb["IS_LT"].fillna(0.0) + comb["IS_ST"].fillna(0.0))
    return comb.reset_index()[["player_slug","role_bucket","IS"]]

def _subset_IS(players_p90: pd.DataFrame, gk_core: pd.DataFrame,
               competition: Optional[str], venue: Optional[str],
               order_col: Optional[str]) -> pd.DataFrame:
    outfield = _compute_outfield_IS_for_subset(players_p90, competition, venue, order_col)
    gk = _compute_gk_IS_for_subset(gk_core, competition, venue, order_col)
    return pd.concat([outfield, gk], ignore_index=True)

# ===========================
# Minutes, availability, transfers
# ===========================

def rolling_minutes_expectation(df_team: pd.DataFrame, player_slug: str, window_matches: int=ROLLING_MINUTES_WINDOW) -> Tuple[float,float,float,float]:
    d = df_team[df_team["player_slug"] == player_slug].copy()
    if d.empty: return 0.0,0.0,0.0,0.0
    date_col = "match_date" if "match_date" in d.columns else ("date" if "date" in d.columns else None)
    if date_col: d = d.sort_values(date_col)
    d = d.tail(window_matches)
    mins = d["PlayersMinutes"].fillna(0.0).astype(float)
    is_start = (mins >= 60).astype(float)
    is_sub = (mins < 60).astype(float)
    if len(d) == 0: return 0.0,0.0,0.0,0.0
    p_start = is_start.mean()
    mu_min_start = mins[is_start > 0].mean() if (is_start > 0).any() else 75.0
    p_sub = is_sub.mean()
    mu_min_sub = mins[is_sub > 0].mean() if (is_sub > 0).any() else 20.0
    return float(p_start), float(mu_min_start), float(p_sub), float(mu_min_sub)

def is_unavailable_for_team(slug: str,
                            team_name: str,
                            unavailable_list: List[str],
                            transfers_in: Dict[str, Dict],
                            transfers_out: Dict[str, Dict]) -> bool:
    s = normalize_name(slug)
    if s in set(unavailable_list): return True
    if s in transfers_in:
        new_team = str(transfers_in[s].get("new_team",""))
        if new_team and new_team != str(team_name): return True
    if s in transfers_out:
        old_team = str(transfers_out[s].get("old_team",""))
        if old_team == str(team_name): return True
    return False

# ===========================
# Auto-suspensions by competition (NEW)
# ===========================

def _auto_suspended_from_df(df: pd.DataFrame,
                            slug_col: str="player_slug",
                            comp_col: str="competition_type",
                            gw_col: str="gameweek",
                            yc_col: str="PlayersYellowCards",
                            rc_col: str="PlayersRedCards") -> Dict[str, set]:
    """
    Build a dict {competition: set(slug)} of players auto-suspended:
      - If last row GW==1 -> ignore past (no suspension here).
      - Yellow cards: if last YC is a positive multiple of 5 -> suspended.
      - Red cards: if last RC - previous RC >= 1 -> suspended (needs previous row).
    """
    out: Dict[str, set] = {}
    if not all(c in df.columns for c in [slug_col, comp_col, gw_col, yc_col, rc_col]):
        return out
    # Work per (slug, competition)
    df2 = df[[slug_col, comp_col, gw_col, yc_col, rc_col]].copy()
    # Make sure gameweek is numeric, missing -> very small to be last sorted by date if needed
    df2[gw_col] = pd.to_numeric(df2[gw_col], errors="coerce")
    # If there is no sensible GW, we will fallback to ordering by index
    for (slug, comp), g in df2.groupby([slug_col, comp_col], dropna=False):
        if g.empty: continue
        gg = g.sort_values(gw_col if g[gw_col].notna().any() else rc_col).copy()
        last = gg.tail(1).iloc[0]
        # If last gameweek == 1 -> no suspension from history
        try:
            if int(last[gw_col]) == 1:
                continue
        except Exception:
            pass
        # Yellow rule
        yc = pd.to_numeric(last[yc_col], errors="coerce")
        yc_flag = bool((not pd.isna(yc)) and yc > 0 and (int(yc) % 5 == 0))
        # Red rule (need previous)
        rc_flag = False
        if len(gg) >= 2:
            prev = gg.tail(2).head(1).iloc[0]
            rc_last = pd.to_numeric(last[rc_col], errors="coerce")
            rc_prev = pd.to_numeric(prev[rc_col], errors="coerce")
            if not pd.isna(rc_last) and not pd.isna(rc_prev):
                rc_flag = (int(rc_last) - int(rc_prev)) >= 1
        # Mark
        if yc_flag or rc_flag:
            out.setdefault(str(comp), set()).add(str(slug))
    return out

def build_auto_suspensions_by_competition(players_df: pd.DataFrame, gk_df: pd.DataFrame) -> Dict[str, set]:
    """
    Merge auto-suspensions from outfield and keepers into a dict:
      {competition: set(slugs_suspended)}
    """
    out = {}
    # Outfield
    sus_p = _auto_suspended_from_df(players_df, slug_col="player_slug",
                                    comp_col="competition_type", gw_col="gameweek",
                                    yc_col="PlayersYellowCards", rc_col="PlayersRedCards")
    # Keepers
    sus_k = _auto_suspended_from_df(gk_df, slug_col="player_slug",
                                    comp_col="competition_type", gw_col="gameweek",
                                    yc_col="PlayersYellowCards", rc_col="PlayersRedCards")
    # Merge sets
    comps = set(sus_p.keys()) | set(sus_k.keys())
    for c in comps:
        out[c] = set()
        if c in sus_p: out[c] |= sus_p[c]
        if c in sus_k: out[c] |= sus_k[c]
    return out

# ===========================
# Team note assembly (unchanged)
# ===========================

def team_note_for_context(team_name: str,
                          competition: Optional[str],
                          venue: Optional[str],
                          formation: str,
                          players_p90: pd.DataFrame,
                          gk_core: pd.DataFrame,
                          is_cache: Dict[Tuple[Optional[str], Optional[str]], pd.DataFrame],
                          unavailable_list: List[str],
                          transfers_in: Dict[str, Dict],
                          transfers_out: Dict[str, Dict],
                          depth_weights: List[float]) -> float:
    key = (competition, venue)
    if key not in is_cache:
        order_col = "match_date" if "match_date" in players_p90.columns else ("date" if "date" in players_p90.columns else None)
        is_cache[key] = _subset_IS(players_p90, gk_core, competition, venue, order_col)
    is_tab = is_cache[key]

    team_rows = players_p90[players_p90["team_name"].astype(str) == str(team_name)]
    team_gk_rows = gk_core[gk_core["team_name"].astype(str) == str(team_name)]

    candidate_slugs = set(team_rows["player_slug"].dropna().tolist())
    for s, info in (transfers_in or {}).items():
        if str(info.get("new_team","")) == str(team_name):
            candidate_slugs.add(normalize_name(s))

    slots = parse_formation_slots(formation)
    contributions: List[Tuple[str,str,float]] = []

    for slug in candidate_slugs:
        if is_unavailable_for_team(slug, team_name, unavailable_list, transfers_in, transfers_out):
            continue
        tr = team_rows[team_rows["player_slug"] == slug]
        if not tr.empty:
            role = tr["role_bucket"].tail(1).iloc[0]
            age_series = tr["PlayersAge"] if "PlayersAge" in tr.columns else pd.Series([], dtype=float)
        else:
            anyr = players_p90[players_p90["player_slug"] == slug]
            role = anyr["role_bucket"].tail(1).iloc[0] if not anyr.empty else "MF"
            age_series = anyr["PlayersAge"] if "PlayersAge" in anyr.columns else pd.Series([], dtype=float)
        age_val = float(age_series.dropna().tail(1).iloc[0]) if not age_series.empty else None

        row_is = is_tab[is_tab["player_slug"] == slug]
        IS = float(row_is["IS"].iloc[0]) if not row_is.empty else 0.0

        p_start, mu_start, p_sub, mu_sub = rolling_minutes_expectation(team_rows, slug, window_matches=ROLLING_MINUTES_WINDOW)
        exp_min = p_start * mu_start + (1 - p_start) * p_sub * mu_sub

        if slug in (transfers_in or {}):
            info = transfers_in[slug] or {}
            new_team = str(info.get("new_team",""))
            if new_team == str(team_name):
                lam = transfer_blend_factor(count_matches_with_team(players_p90, slug, new_team, since=info.get("transfer_date")))
                lf = float(info.get("league_factor", LEAGUE_FACTOR_DEFAULT))
                origin = info.get("origin_country")
                new_cty = latest_country_for_player(players_p90, slug, is_gk=False)
                cf_base = float(info.get("country_factor", COUNTRY_FACTOR_DEFAULT)) if (origin and new_cty and str(origin).lower()!=str(new_cty).lower()) else 1.0
                cf = 1.0 - (1.0 - cf_base) * (1.0 - lam)
                IS = lam*IS + (1-lam)*(lf*IS)
                IS *= cf
                if lam == 0.0 and exp_min > 0.0: exp_min *= 0.6

        alpha_age = age_factor(age_val, role)
        E_next = IS * alpha_age * (exp_min / 90.0)
        contributions.append((slug, role, float(E_next)))

    gk_best = 0.0
    gk_slugs = set(team_gk_rows["player_slug"].dropna().tolist())
    for slug in gk_slugs:
        if is_unavailable_for_team(slug, team_name, unavailable_list, transfers_in, transfers_out):
            continue
        row_is = is_tab[is_tab["player_slug"] == slug]
        IS = float(row_is["IS"].iloc[0]) if not row_is.empty else 0.0
        gk_team_for_minutes = team_gk_rows.rename(columns={"KeepersMinutes":"PlayersMinutes"})
        p_start, mu_start, p_sub, mu_sub = rolling_minutes_expectation(gk_team_for_minutes, slug, window_matches=ROLLING_MINUTES_WINDOW)
        exp_min = p_start*mu_start + (1-p_start)*p_sub*mu_sub
        age_ser = team_gk_rows.loc[team_gk_rows["player_slug"] == slug, "KeepersAge"] if "KeepersAge" in team_gk_rows.columns else pd.Series([], dtype=float)
        age_val = float(age_ser.tail(1).iloc[0]) if not age_ser.empty else None
        alpha_age = age_factor(age_val, "GK")

        if slug in (transfers_in or {}):
            info = transfers_in[slug] or {}
            new_team = str(info.get("new_team",""))
            if new_team == str(team_name):
                lam = transfer_blend_factor(count_matches_with_team(gk_core, slug, new_team, since=info.get("transfer_date")))
                lf = float(info.get("league_factor", LEAGUE_FACTOR_DEFAULT))
                origin = info.get("origin_country")
                new_cty = latest_country_for_player(gk_core, slug, is_gk=True)
                cf_base = float(info.get("country_factor", COUNTRY_FACTOR_DEFAULT)) if (origin and new_cty and str(origin).lower()!=str(new_cty).lower()) else 1.0
                cf = 1.0 - (1.0 - cf_base) * (1.0 - lam)
                IS = lam*IS + (1-lam)*(lf*IS)
                IS *= cf
                if lam == 0.0 and exp_min > 0.0: exp_min *= 0.6

        gk_best = max(gk_best, IS * alpha_age * (exp_min / 90.0))

    total = 0.0
    slots = parse_formation_slots(formation)
    for role in ["CD","FB","MF","WG","ST"]:
        k = slots.get(role, 0)
        if k <= 0: continue
        vals = sorted([e for (_, r, e) in contributions if r == role], reverse=True)
        for i in range(min(k, len(vals))):
            w = depth_weights[i] if i < len(depth_weights) else depth_weights[-1]
            total += w * vals[i]
    total += gk_best
    return float(total)

def count_team_unavailable(team_name: str,
                           players_p90: pd.DataFrame,
                           gk_core: pd.DataFrame,
                           unavailable_list: List[str],
                           transfers_in: Dict[str, Dict],
                           transfers_out: Dict[str, Dict]) -> int:
    team_players = set(players_p90.loc[players_p90["team_name"].astype(str)==str(team_name), "player_slug"].dropna().tolist())
    team_gks = set(gk_core.loc[gk_core["team_name"].astype(str)==str(team_name), "player_slug"].dropna().tolist())
    candidates = set.union(team_players, team_gks)
    for s, info in (transfers_in or {}).items():
        if str(info.get("new_team","")) == str(team_name):
            candidates.add(normalize_name(s))
    for s, info in (transfers_out or {}).items():
        if str(info.get("old_team","")) == str(team_name):
            candidates.discard(normalize_name(s))
    unavail = set(normalize_name(x) for x in (unavailable_list or []))
    return int(len(candidates & unavail))

def get_most_used_formation(df_matches, past_matches):
    """
    For each team in df_matches, finds their most used formation in the last 5 matches
    of the same competition. In case of tie, returns the most recent formation.
    
    Returns:
        Dict[str, str]: Dictionary with team_name as key and formation as value
    """
    
    team_formations = {}
    
    # Process each match to get unique teams
    for idx, row in df_matches.iterrows():
        home_team = row['home_team_name']
        away_team = row['away_team_name']
        competition = row['competition']
        match_date = row['date_of_match']
        
        # Process home team if not already processed
        if home_team not in team_formations:
            # Find last 5 matches for home team in this competition
            team_matches = past_matches[
                (
                    ((past_matches['home_team_name'] == home_team) | 
                     (past_matches['away_team_name'] == home_team))
                ) &
                (past_matches['competition'] == competition) &
                (past_matches['date_of_match'] < match_date)
            ].sort_values('date_of_match', ascending=False).head(5)
            
            if not team_matches.empty:
                formations = []
                for _, match in team_matches.iterrows():
                    # Check if team played as home or away
                    if match['home_team_name'] == home_team:
                        formation = match['home_team_formation']
                    else:
                        formation = match['away_team_formation']
                    
                    # Only add non-null formations
                    if pd.notna(formation):
                        formations.append(formation)
                
                if formations:
                    # Count formations
                    formation_counts = Counter(formations)
                    max_count = max(formation_counts.values())
                    
                    # Get formations with max count
                    most_used = [f for f, count in formation_counts.items() if count == max_count]
                    
                    # If tie, get the most recent one
                    if len(most_used) > 1:
                        # Most recent is the first in our list (already sorted descending)
                        chosen_formation = formations[0] if formations[0] in most_used else most_used[0]
                    else:
                        chosen_formation = most_used[0]
                    
                    team_formations[home_team] = chosen_formation
        
        # Process away team if not already processed
        if away_team not in team_formations:
            # Find last 5 matches for away team in this competition
            team_matches = past_matches[
                (
                    ((past_matches['home_team_name'] == away_team) | 
                     (past_matches['away_team_name'] == away_team))
                ) &
                (past_matches['competition'] == competition) &
                (past_matches['date_of_match'] < match_date)
            ].sort_values('date_of_match', ascending=False).head(5)
            
            if not team_matches.empty:
                formations = []
                for _, match in team_matches.iterrows():
                    # Check if team played as home or away
                    if match['home_team_name'] == away_team:
                        formation = match['home_team_formation']
                    else:
                        formation = match['away_team_formation']
                    
                    # Only add non-null formations
                    if pd.notna(formation):
                        formations.append(formation)
                
                if formations:
                    # Count formations
                    formation_counts = Counter(formations)
                    max_count = max(formation_counts.values())
                    
                    # Get formations with max count
                    most_used = [f for f, count in formation_counts.items() if count == max_count]
                    
                    # If tie, get the most recent one
                    if len(most_used) > 1:
                        # Most recent is the first in our list (already sorted descending)
                        chosen_formation = formations[0] if formations[0] in most_used else most_used[0]
                    else:
                        chosen_formation = most_used[0]
                    
                    team_formations[away_team] = chosen_formation
    
    return team_formations

# ===========================
# Data Cleaning
# ===========================

def keep_last_n_matches_by_competition(
    df: pd.DataFrame,
    n_matches: int = 18,
    reference_date: Optional[str] = None,
    max_days_old: int = 365,
    competition_col: str = 'competition',
    date_col: str = 'date_of_match'
) -> pd.DataFrame:
    """
    Keep only the last N matches per player per competition, excluding old matches.
    
    Args:
        df: DataFrame with player data
        n_matches: Number of recent matches to keep per player per competition
        reference_date: Reference date to filter old matches (format: 'YYYY-MM-DD')
                       If None, uses today's date
        max_days_old: Maximum age of matches to keep (default: 365 days = 1 year)
        competition_col: Name of competition column
        date_col: Name of date column (default: 'date_of_match')
    
    Returns:
        Filtered DataFrame with:
        - Only matches within max_days_old from reference_date
        - Only last n_matches per player per competition
    """
    if df.empty or 'player_slug' not in df.columns:
        return df
    
    if competition_col not in df.columns:
        print(f"Warning: No '{competition_col}' column found, skipping competition filter")
        return df
    
    if date_col not in df.columns:
        print(f"Warning: No '{date_col}' column found, skipping date filter")
        return df
    
    # Convert date column to datetime
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Set reference date
    if reference_date is None:
        ref_date = pd.Timestamp.now()
    else:
        ref_date = pd.to_datetime(reference_date)
    
    # Calculate cutoff date (reference_date - max_days_old)
    cutoff_date = ref_date - pd.Timedelta(days=max_days_old)
    
    initial_rows = len(df)
    
    # Filter 1: Remove matches older than max_days_old
    df = df[df[date_col] >= cutoff_date]
    removed_by_date = initial_rows - len(df)
    
    if removed_by_date > 0:
        print(f"  Filtered out {removed_by_date} rows older than {cutoff_date.date()} (>{max_days_old} days old)")
    
    # Sort by competition, player, and date (most recent last)
    df = df.sort_values([competition_col, 'player_slug', date_col])
    
    # Filter 2: Keep last n_matches per player per competition
    before_match_filter = len(df)
    df = df.groupby(['player_slug', competition_col]).tail(n_matches)
    removed_by_match_limit = before_match_filter - len(df)
    
    if removed_by_match_limit > 0:
        print(f"  Filtered out {removed_by_match_limit} rows exceeding {n_matches} matches per player per competition")
    
    print(f"  Final: {initial_rows} → {len(df)} rows (removed {initial_rows - len(df)} total)")
    
    return df.reset_index(drop=True)


# ===========================
# Transfer Application
# ===========================

def build_transfers_dicts_from_dataframe(
    transfers_df: pd.DataFrame,
    teams_csv_path: str,
) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """
    Convert a transfers dataframe to the transfers_in and transfers_out dictionaries.
    
    Args:
        transfers_df: DataFrame with columns:
            - player_name: Name of the player
            - old_team: Previous team name
            - new_team: New team name
            - transfer_nature: Type of transfer
            - transfer_date (optional): Date of transfer
        teams_csv_path: Path to teams CSV to look up countries
    
    Returns:
        Tuple of (transfers_in, transfers_out) dictionaries
    """
    if transfers_df.empty:
        return {}, {}
    
    # Load teams data to get countries
    teams_df = pd.read_csv(teams_csv_path)
    teams_name_col = pick_team_name_column(teams_df)
    
    # Find country column
    teams_country_col = None
    for col in ['country', 'Country', 'nation', 'Nation', 'pais', 'Pais']:
        if col in teams_df.columns:
            teams_country_col = col
            break
    
    # Create mapping of normalized team name -> country
    team_to_country = {}
    if teams_name_col and teams_country_col:
        for _, row in teams_df.iterrows():
            team_name = str(row[teams_name_col])
            country = str(row[teams_country_col])
            team_to_country[normalize_name(team_name)] = country
    
    transfers_in = {}
    transfers_out = {}
    
    for _, transfer in transfers_df.iterrows():
        player_name = str(transfer.get('player_name', '')).strip()
        old_team = str(transfer.get('old_team', '')).strip()
        new_team = str(transfer.get('new_team', '')).strip()
        transfer_nature = str(transfer.get('transfer_nature', '')).strip()
        transfer_date = transfer.get('transfer_date', None)
        
        if not player_name:
            continue
        
        # Skip retirements/career breaks
        if transfer_nature in ['Retired', 'Career break', 'Retirement', 'retired', 'career break']:
            continue
        
        player_slug = normalize_name(player_name)
        old_team_norm = normalize_name(old_team)
        new_team_norm = normalize_name(new_team)
        
        # Get countries
        old_country = team_to_country.get(old_team_norm)
        new_country = team_to_country.get(new_team_norm)
        
        # Build transfers_in entry (player arriving at new_team)
        transfers_in[player_slug] = {
            'new_team': new_team,
            'old_team': old_team,
            'transfer_date': transfer_date,
            'origin_country': old_country,
            'league_factor': LEAGUE_FACTOR_DEFAULT,
            'country_factor': COUNTRY_FACTOR_DEFAULT if (old_country and new_country and old_country != new_country) else 1.0,
        }
        
        # Build transfers_out entry (player leaving old_team)
        transfers_out[player_slug] = {
            'old_team': old_team,
            'new_team': new_team,
            'transfer_date': transfer_date,
        }
    
    return transfers_in, transfers_out


def apply_transfers_from_dataframe(
    transfers_df: pd.DataFrame,
    players_csv_path: str,
    keepers_csv_path: str,
    teams_csv_path: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply transfers from a dataframe directly to player and keeper CSVs.
    
    Args:
        transfers_df: DataFrame with columns:
            - player_name: Name of the player
            - old_team: Previous team name
            - new_team: New team name
            - transfer_nature: Type of transfer (e.g., "Retired", "Career break", "Transfer", etc.)
        players_csv_path: Path to the outfield players CSV
        keepers_csv_path: Path to the keepers CSV
        teams_csv_path: Path to the teams CSV (to check country changes)
    
    Returns:
        Tuple of (updated_players_df, updated_keepers_df)
    
    Logic:
        - If transfer_nature is "Retired" or "Career break": Remove all rows for that player
        - Otherwise: Update all rows where player has old_team to new_team
        - Detects country changes by looking up teams in teams_csv_path
        - Team names are normalized for matching
    """
    # Load the CSVs
    players_df = pd.read_csv(players_csv_path)
    keepers_df = pd.read_csv(keepers_csv_path)
    teams_df = pd.read_csv(teams_csv_path)
    
    # Get team column name for each dataframe
    players_team_col = pick_team_name_column(players_df)
    keepers_team_col = pick_team_name_column(keepers_df)
    
    if not players_team_col:
        raise ValueError("Could not find team name column in players CSV")
    if not keepers_team_col:
        raise ValueError("Could not find team name column in keepers CSV")
    
    # Find team name and country columns in teams CSV
    teams_name_col = pick_team_name_column(teams_df)
    if not teams_name_col:
        raise ValueError("Could not find team name column in teams CSV")
    
    # Find country column in teams CSV
    teams_country_col = None
    for col in ['country', 'Country', 'nation', 'Nation', 'pais', 'Pais']:
        if col in teams_df.columns:
            teams_country_col = col
            break
    
    if not teams_country_col:
        raise ValueError("Could not find country column in teams CSV")
    
    # Create a mapping of normalized team name -> country
    team_to_country = {}
    for _, row in teams_df.iterrows():
        team_name = str(row[teams_name_col])
        country = str(row[teams_country_col])
        team_to_country[normalize_name(team_name)] = country
    
    # Process each transfer
    for _, transfer in transfers_df.iterrows():
        player_name = str(transfer.get('player_name', '')).strip()
        old_team = str(transfer.get('old_team', '')).strip()
        new_team = str(transfer.get('new_team', '')).strip()
        transfer_nature = str(transfer.get('transfer_nature', '')).strip()
        
        if not player_name:
            continue
        
        # Normalize names
        player_slug = normalize_name(player_name)
        old_team_norm = normalize_name(old_team)
        new_team_norm = normalize_name(new_team)
        
        # Check if player is retiring or taking a career break
        if transfer_nature in ['Retired', 'Career break', 'Retirement', 'retired', 'career break']:
            # Remove all rows for this player from both dataframes
            print(f"Removing {player_name} (slug: {player_slug}) - {transfer_nature}")
            
            # Remove from players
            if 'player_slug' in players_df.columns:
                initial_count = len(players_df)
                players_df = players_df[players_df['player_slug'] != player_slug]
                removed_count = initial_count - len(players_df)
                if removed_count > 0:
                    print(f"  Removed {removed_count} rows from players CSV")
            
            # Remove from keepers
            if 'player_slug' in keepers_df.columns:
                initial_count = len(keepers_df)
                keepers_df = keepers_df[keepers_df['player_slug'] != player_slug]
                removed_count = initial_count - len(keepers_df)
                if removed_count > 0:
                    print(f"  Removed {removed_count} rows from keepers CSV")
        
        else:
            # Regular transfer - update team name
            # Check if there's a country change
            old_country = team_to_country.get(old_team_norm, None)
            new_country = team_to_country.get(new_team_norm, None)
            
            country_change = False
            if old_country and new_country and old_country != new_country:
                country_change = True
                print(f"Transferring {player_name} from {old_team} ({old_country}) to {new_team} ({new_country}) - COUNTRY CHANGE")
            else:
                print(f"Transferring {player_name} from {old_team} to {new_team}")
            
            # Update in players dataframe
            if 'player_slug' in players_df.columns:
                # Find all rows for this player with the old team
                mask = (
                    (players_df['player_slug'] == player_slug) &
                    (players_df[players_team_col].apply(lambda x: normalize_name(str(x)) == old_team_norm))
                )
                updated_count = mask.sum()
                if updated_count > 0:
                    players_df.loc[mask, players_team_col] = new_team
                    print(f"  Updated {updated_count} rows in players CSV")
            
            # Update in keepers dataframe
            if 'player_slug' in keepers_df.columns:
                # Find all rows for this player with the old team
                mask = (
                    (keepers_df['player_slug'] == player_slug) &
                    (keepers_df[keepers_team_col].apply(lambda x: normalize_name(str(x)) == old_team_norm))
                )
                updated_count = mask.sum()
                if updated_count > 0:
                    keepers_df.loc[mask, keepers_team_col] = new_team
                    print(f"  Updated {updated_count} rows in keepers CSV")
    
    return players_df, keepers_df


# ===========================
# Public API
# ===========================

def compute_team_notes_for_fixtures(
    fixtures_df: pd.DataFrame,
    past_matches: pd.DataFrame,
    players_csv_path: str,
    keepers_csv_path: str,
    teams_csv_path: str,
    unavailable_list: List[str],
    transfers_df: Optional[pd.DataFrame] = None,
    depth_weights: Optional[List[float]] = None,
    reference_date: Optional[str] = None,
    max_matches_per_competition: int = 18,
    max_days_old: int = 365,
) -> pd.DataFrame:
    """
    Compute 8 notes per fixture (home/away × global/home × competition/home)
    and add home/away unavailable counts, using fresh CSV stats.
    Adds AUTO-SUSPENSIONS by competition from PlayersYellowCards / PlayersRedCards and gameweek rules.
    
    Args:
        fixtures_df: Fixtures to compute notes for
        past_matches: Historical matches for context
        players_csv_path: Path to outfield players CSV
        keepers_csv_path: Path to keepers CSV
        teams_csv_path: Path to teams CSV (for country lookups)
        unavailable_list: List of unavailable player slugs
        transfers_df: Optional DataFrame with transfers (player_name, old_team, new_team, transfer_nature, transfer_date)
                      If empty or None, no transfers are applied
        depth_weights: Optional depth weights for squad evaluation
        reference_date: Reference date for filtering old matches (format: 'YYYY-MM-DD')
                       If None, uses today's date
        max_matches_per_competition: Maximum number of matches to keep per player per competition (default: 18)
                                     Set to 0 to disable this filter
        max_days_old: Maximum age in days for matches to be considered (default: 365 = 1 year)
                     Matches older than (reference_date - max_days_old) are excluded
    
    Returns:
        fixtures_df with added team notes and unavailable counts
    """
    # Handle transfers if provided
    transfers_in = {}
    transfers_out = {}
    
    if transfers_df is not None and not transfers_df.empty:
        print(f"Processing {len(transfers_df)} transfers...")
        
        # First, apply transfers to update the CSVs
        players_raw, keepers_raw = apply_transfers_from_dataframe(
            transfers_df=transfers_df,
            players_csv_path=players_csv_path,
            keepers_csv_path=keepers_csv_path,
            teams_csv_path=teams_csv_path,
        )
        
        # Build the transfers dictionaries for adaptation logic
        transfers_in, transfers_out = build_transfers_dicts_from_dataframe(
            transfers_df=transfers_df,
            teams_csv_path=teams_csv_path,
        )
        
        print(f"Transfers applied: {len(transfers_in)} players affected")
    else:
        # Load raw datasets normally
        players_raw = load_outfield(players_csv_path)
        keepers_raw = load_keepers(keepers_csv_path)
    
    # NEW: Clean old matches - keep only recent data
    if max_matches_per_competition > 0 or max_days_old > 0:
        print(f"\nCleaning player data (max {max_matches_per_competition} matches per competition, max {max_days_old} days old)...")
        
        print("Filtering outfield players:")
        players_raw = keep_last_n_matches_by_competition(
            df=players_raw,
            n_matches=max_matches_per_competition,
            reference_date=reference_date,
            max_days_old=max_days_old,
        )
        
        print("Filtering keepers:")
        keepers_raw = keep_last_n_matches_by_competition(
            df=keepers_raw,
            n_matches=max_matches_per_competition,
            reference_date=reference_date,
            max_days_old=max_days_old,
        )

    # Build per90 outfield + GK core features
    players_p90 = add_per90_outfield(players_raw, winsor=True, lo=0.01, hi=0.99)
    gk_core = build_keeper_core(keepers_raw)

    # ---- NEW: build auto-suspensions per competition ----
    auto_susp_by_comp = build_auto_suspensions_by_competition(players_raw, keepers_raw)

    # Prepare output columns in fixtures_df
    for c in ["home_team","away_team","competition_type"]:
        if c not in fixtures_df.columns:
            fixtures_df[c] = ""
    note_cols = [
        "home_team_note","home_team_note_home","home_team_competition_note","home_team_competition_note_home",
        "away_team_note","away_team_note_away","away_team_competition_note","away_team_competition_note_away",
    ]
    for c in note_cols:
        if c not in fixtures_df.columns: fixtures_df[c] = np.nan
    if "home_unavailable_count" not in fixtures_df.columns: fixtures_df["home_unavailable_count"] = np.nan
    if "away_unavailable_count" not in fixtures_df.columns: fixtures_df["away_unavailable_count"] = np.nan

    # Cache IS tables by (competition, venue)
    is_cache: Dict[Tuple[Optional[str], Optional[str]], pd.DataFrame] = {}
    depth_w = depth_weights if depth_weights is not None else DEFAULT_DEPTH_WEIGHTS

    formation_by_team = get_most_used_formation(fixtures_df, past_matches)

    # Iterate fixtures and compute notes in place
    for idx, row in fixtures_df.iterrows():
        home = str(row["home_team"]); away = str(row["away_team"])
        comp = str(row["competition_type"])

        # Effective unavailable list for this competition = external list ∪ auto-suspensions(comp)
        comp_auto = set(auto_susp_by_comp.get(comp, set()))
        effective_unavailable = list(set(normalize_name(x) for x in (unavailable_list or [])) | comp_auto)

        home_form = formation_by_team.get(home, "4-3-3")
        away_form = formation_by_team.get(away, "4-3-3")

        # HOME notes
        fixtures_df.at[idx, "home_team_note"] = team_note_for_context(
            team_name=home, competition=None, venue=None, formation=home_form,
            players_p90=players_p90, gk_core=gk_core, is_cache=is_cache,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out,
            depth_weights=depth_w
        )
        fixtures_df.at[idx, "home_team_note_home"] = team_note_for_context(
            team_name=home, competition=None, venue="home", formation=home_form,
            players_p90=players_p90, gk_core=gk_core, is_cache=is_cache,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out,
            depth_weights=depth_w
        )
        fixtures_df.at[idx, "home_team_competition_note"] = team_note_for_context(
            team_name=home, competition=comp, venue=None, formation=home_form,
            players_p90=players_p90, gk_core=gk_core, is_cache=is_cache,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out,
            depth_weights=depth_w
        )
        fixtures_df.at[idx, "home_team_competition_note_home"] = team_note_for_context(
            team_name=home, competition=comp, venue="home", formation=home_form,
            players_p90=players_p90, gk_core=gk_core, is_cache=is_cache,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out,
            depth_weights=depth_w
        )

        # AWAY notes
        fixtures_df.at[idx, "away_team_note"] = team_note_for_context(
            team_name=away, competition=None, venue=None, formation=away_form,
            players_p90=players_p90, gk_core=gk_core, is_cache=is_cache,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out,
            depth_weights=depth_w
        )
        fixtures_df.at[idx, "away_team_note_away"] = team_note_for_context(
            team_name=away, competition=None, venue="away", formation=away_form,
            players_p90=players_p90, gk_core=gk_core, is_cache=is_cache,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out,
            depth_weights=depth_w
        )
        fixtures_df.at[idx, "away_team_competition_note"] = team_note_for_context(
            team_name=away, competition=comp, venue=None, formation=away_form,
            players_p90=players_p90, gk_core=gk_core, is_cache=is_cache,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out,
            depth_weights=depth_w
        )
        fixtures_df.at[idx, "away_team_competition_note_away"] = team_note_for_context(
            team_name=away, competition=comp, venue="away", formation=away_form,
            players_p90=players_p90, gk_core=gk_core, is_cache=is_cache,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out,
            depth_weights=depth_w
        )

        # Unavailable counts (use same effective_unavailable for this comp)
        fixtures_df.at[idx, "home_unavailable_count"] = count_team_unavailable(
            team_name=home, players_p90=players_p90, gk_core=gk_core,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out
        )
        fixtures_df.at[idx, "away_unavailable_count"] = count_team_unavailable(
            team_name=away, players_p90=players_p90, gk_core=gk_core,
            unavailable_list=effective_unavailable, transfers_in=transfers_in, transfers_out=transfers_out
        )

    return fixtures_df


# ============================================================================
# INTERNAL SUSPENSION CHECKER - Add this to your class
# ============================================================================

class _SuspensionChecker:
    """Internal class to check player suspensions"""
    
    def __init__(self, config: Dict[str, Any], competition_type: str):
        self.config = config
        self.competition_type = competition_type
    
    def get_suspended_players(
        self,
        players_df: pd.DataFrame,
        past_matches: pd.DataFrame,
        team_name: str
    ) -> Set[str]:
        """Get set of suspended players for a team"""
        suspended = set()
        
        team_players = players_df[players_df['team'] == team_name].copy()
        if team_players.empty:
            return suspended
        
        # Check yellow card suspensions
        yellow_suspended = self._check_yellow_suspensions(
            team_players, past_matches, team_name
        )
        suspended.update(yellow_suspended)
        
        # Check red card suspensions
        red_suspended = self._check_red_suspensions(
            team_players, past_matches, team_name
        )
        suspended.update(red_suspended)
        
        return suspended
    
    def _check_yellow_suspensions(
        self,
        team_players: pd.DataFrame,
        past_matches: pd.DataFrame,
        team_name: str
    ) -> Set[str]:
        """Check yellow card suspensions"""
        suspension_type = self.config["yellow_cards_suspensions"]["type"]
        
        if suspension_type == "cycle":
            return self._cycle_suspension(team_players)
        elif suspension_type == "milestones":
            return self._milestones_suspension(team_players, past_matches, team_name)
        
        return set()
    
    def _cycle_suspension(self, team_players: pd.DataFrame) -> Set[str]:
        """Cycle-based suspension (e.g., every 5 yellows)"""
        suspended = set()
        cards_per_suspension = self.config["yellow_cards_suspensions"]["cards_per_suspension"]
        
        yellow_col = (
            "PlayersYellowCards_league" if self.competition_type == "league"
            else "PlayersYellowCards_european"
        )
        
        if yellow_col not in team_players.columns:
            yellow_col = "PlayersYellowCards"
            if yellow_col not in team_players.columns:
                return suspended
        
        for _, player in team_players.iterrows():
            player_name = player['Players']
            yellow_cards = self._safe_int(player.get(yellow_col, 0))
            
            if yellow_cards > 0 and yellow_cards % cards_per_suspension == 0:
                suspended.add(player_name)
        
        return suspended
    
    def _milestones_suspension(
        self,
        team_players: pd.DataFrame,
        past_matches: pd.DataFrame,
        team_name: str
    ) -> Set[str]:
        """Milestones-based suspension"""
        yellow_col = (
            "PlayersYellowCards_league" if self.competition_type == "league"
            else "PlayersYellowCards_european"
        )
        
        if yellow_col not in team_players.columns:
            yellow_col = "PlayersYellowCards"
            if yellow_col not in team_players.columns:
                return set()
        
        # Check if milestones with cutoffs (Premier League style)
        if "milestones" in self.config["yellow_cards_suspensions"]:
            milestones = self.config["yellow_cards_suspensions"]["milestones"]
            if milestones and isinstance(milestones[0], dict):
                return self._milestones_with_cutoffs(
                    team_players, past_matches, team_name, yellow_col
                )
        
        # Check if milestones with repetition or simple
        if "milestones_cards" in self.config["yellow_cards_suspensions"]:
            return self._milestones_with_repetition(team_players, yellow_col)
        
        return set()
    
    def _milestones_with_cutoffs(
        self,
        team_players: pd.DataFrame,
        past_matches: pd.DataFrame,
        team_name: str,
        yellow_col: str
    ) -> Set[str]:
        """Premier League style: thresholds by team match number"""
        suspended = set()
        milestones = self.config["yellow_cards_suspensions"]["milestones"]
        
        # Count team's league fixtures
        team_matches = past_matches[
            ((past_matches['home_team'] == team_name) | 
             (past_matches['away_team'] == team_name)) &
            (past_matches['competition_type'] == 'league')
        ]
        team_match_count = len(team_matches)
        
        # Find applicable milestone
        applicable_milestone = None
        for milestone in sorted(milestones, key=lambda x: 
                               999 if x["cutoff_league_fixtures"] == "end_of_season" 
                               else x["cutoff_league_fixtures"]):
            cutoff = milestone["cutoff_league_fixtures"]
            if cutoff == "end_of_season" or team_match_count <= cutoff:
                applicable_milestone = milestone
                break
        
        if not applicable_milestone:
            return suspended
        
        for _, player in team_players.iterrows():
            player_name = player['Players']
            yellow_cards = self._safe_int(player.get(yellow_col, 0))
            
            if yellow_cards >= applicable_milestone["cards"]:
                suspended.add(player_name)
        
        return suspended
    
    def _milestones_with_repetition(
        self,
        team_players: pd.DataFrame,
        yellow_col: str
    ) -> Set[str]:
        """Milestones with optional repetition (Serie A / Champions style)"""
        suspended = set()
        milestones_cards = self.config["yellow_cards_suspensions"]["milestones_cards"]
        after_last = self.config["yellow_cards_suspensions"].get("after_last_milestone", None)
        
        for _, player in team_players.iterrows():
            player_name = player['Players']
            yellow_cards = self._safe_int(player.get(yellow_col, 0))
            
            if yellow_cards == 0:
                continue
            
            # Check if at exact milestone
            if yellow_cards in milestones_cards:
                suspended.add(player_name)
            # Check repetition after last milestone
            elif after_last and yellow_cards > max(milestones_cards):
                repeat_every = after_last["repeat_every_cards"]
                starting_after = after_last["starting_after_cards"]
                
                if yellow_cards > starting_after:
                    cards_after_start = yellow_cards - starting_after
                    if cards_after_start % repeat_every == 0:
                        suspended.add(player_name)
        
        return suspended
    
    def _check_red_suspensions(
        self,
        team_players: pd.DataFrame,
        past_matches: pd.DataFrame,
        team_name: str
    ) -> Set[str]:
        """Check red card suspensions (last 2 matches)"""
        suspended = set()
        
        # Filter matches for this team and competition
        team_matches = past_matches[
            ((past_matches['home_team'] == team_name) | 
             (past_matches['away_team'] == team_name)) &
            (past_matches['competition_type'] == self.competition_type)
        ].copy()
        
        if team_matches.empty:
            return suspended
        
        # Sort by date and get last 2 matches
        if 'date_of_match' in team_matches.columns:
            team_matches = team_matches.sort_values('date_of_match', ascending=False)
        
        last_2_matches = team_matches.head(2)
        
        if last_2_matches.empty:
            return suspended
        
        # Check each player for red cards
        for _, player in team_players.iterrows():
            player_name = player['Players']
            red_cards = self._safe_int(player.get('PlayersRedCards', 0))
            
            if red_cards > 0:
                # Simplified: if player has any red cards, assume recent
                # For accurate implementation, need match-level red card data
                suspended.add(player_name)
        
        return suspended
    
    @staticmethod
    def _safe_int(value) -> int:
        """Safely convert value to int"""
        try:
            return int(value) if pd.notna(value) else 0
        except (ValueError, TypeError):
            return 0


# ============================================================================
# MODIFIED compute_team_notes_for_fixtures FUNCTION
# ============================================================================

def compute_team_notes_for_fixtures(
    fixtures_df: pd.DataFrame,
    past_matches: pd.DataFrame,
    players_csv_path: str,
    keepers_csv_path: str,
    teams_csv_path: str,
    unavailable_list: List[str],
    transfers_df: Optional[pd.DataFrame] = None,
    depth_weights: Optional[List[float]] = None,
    # ========== NEW SUSPENSION PARAMETERS ==========
    apply_suspensions: bool = False,
    suspension_config: Optional[Dict[str, Any]] = None,
    # ===============================================
) -> pd.DataFrame:
    """
    Compute team notes for fixtures with optional suspension management.
    
    Args:
        ... (your existing parameters) ...
        apply_suspensions: Whether to apply suspension filtering (default: False)
        suspension_config: Suspension configuration dict (required if apply_suspensions=True)
                          Example:
                          {
                              "yellow_cards_suspensions": {
                                  "type": "cycle",
                                  "ban_matches": 1,
                                  "cards_per_suspension": 5,
                                  "cycle_resets_after_serving_ban": True,
                              },
                              "red_card_ban_matches": 1
                          }
    
    Returns:
        DataFrame with fixtures enriched with team notes
    """
    # Load player and keeper data
    players_df = pd.read_csv(players_csv_path)
    keepers_df = pd.read_csv(keepers_csv_path)
    
    # ========== SUSPENSION FILTERING ==========
    if apply_suspensions:
        # Validate config
        if suspension_config is None:
            raise ValueError("suspension_config is required when apply_suspensions=True")
        
        if "yellow_cards_suspensions" not in suspension_config:
            raise ValueError("suspension_config must contain 'yellow_cards_suspensions'")
        
        # Track all suspended players
        all_suspended_info = []
        
        # Process each fixture to find suspensions
        for idx, fixture in fixtures_df.iterrows():
            home_team = fixture['home_team']
            away_team = fixture['away_team']
            competition_type = fixture.get('competition_type', 'league')
            
            # Initialize suspension checker for this competition
            checker = _SuspensionChecker(suspension_config, competition_type)
            
            # Get suspended players for both teams
            home_suspended = checker.get_suspended_players(
                players_df=players_df,
                past_matches=past_matches,
                team_name=home_team
            )
            
            away_suspended = checker.get_suspended_players(
                players_df=players_df,
                past_matches=past_matches,
                team_name=away_team
            )
            
            # Log suspensions
            if home_suspended:
                print(f"🚫 {home_team} suspended: {', '.join(sorted(home_suspended))}")
            if away_suspended:
                print(f"🚫 {away_team} suspended: {', '.join(sorted(away_suspended))}")
            
            # Store suspension info for this fixture
            all_suspended_info.append({
                'fixture_idx': idx,
                'home_suspended': home_suspended,
                'away_suspended': away_suspended,
                'all_suspended': home_suspended.union(away_suspended)
            })
        
        # Filter out ALL suspended players from dataframes
        all_suspended_players = set()
        for info in all_suspended_info:
            all_suspended_players.update(info['all_suspended'])
        
        if all_suspended_players:
            print(f"\n📊 Total suspended players: {len(all_suspended_players)}")
            players_df = players_df[~players_df['Players'].isin(all_suspended_players)].copy()
            keepers_df = keepers_df[~keepers_df['Players'].isin(all_suspended_players)].copy()
        else:
            print(f"\n✅ No suspended players found")
    
    # ========== YOUR EXISTING COMPUTATION LOGIC ==========
    # Continue with your normal team notes computation using:
    # - players_df (now filtered if apply_suspensions=True)
    # - keepers_df (now filtered if apply_suspensions=True)
    # - All other parameters as before
    
    # Example placeholder (replace with your actual logic):
    result_df = fixtures_df.copy()
    
    # Add suspension info to results if enabled
    if apply_suspensions:
        result_df['home_suspended_count'] = 0
        result_df['away_suspended_count'] = 0
        result_df['home_suspended_players'] = ''
        result_df['away_suspended_players'] = ''
        
        for info in all_suspended_info:
            idx = info['fixture_idx']
            result_df.at[idx, 'home_suspended_count'] = len(info['home_suspended'])
            result_df.at[idx, 'away_suspended_count'] = len(info['away_suspended'])
            result_df.at[idx, 'home_suspended_players'] = ', '.join(sorted(info['home_suspended']))
            result_df.at[idx, 'away_suspended_players'] = ', '.join(sorted(info['away_suspended']))
    
    # ... rest of your computation ...
    
    return result_df