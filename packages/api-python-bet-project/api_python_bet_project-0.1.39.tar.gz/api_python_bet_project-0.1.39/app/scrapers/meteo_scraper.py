from __future__ import annotations

from typing import Dict, Literal, Optional, Tuple
import pandas as pd
import requests

# =============================================================================
# 0) Constants
# =============================================================================

FEATURE_COLS = [
    "temp_c",
    "humidity_pct",
    "precip_mm",
    "pressure_hpa",
    "wind_speed_ms",
    "cloud_cover_pct",
]

# You were missing this constant in your snippet
HOURLY_VARS = (
    "temperature_2m,relative_humidity_2m,precipitation,"
    "pressure_msl,surface_pressure,wind_speed_10m,cloud_cover"
)

# =============================================================================
# 1) Datetime helpers
# =============================================================================

def _build_dt_iso_utc_from_match_cols(date_of_match, hour_of_the_match) -> str:
    """
    hour_of_the_match is ALWAYS in UTC+1 (fixed offset).
    Returns dt in UTC ISO format ending with 'Z', floored to the hour.
    """
    d = pd.to_datetime(date_of_match).date()

    if isinstance(hour_of_the_match, (int, float)) and not pd.isna(hour_of_the_match):
        h, m, s = int(hour_of_the_match), 0, 0
    else:
        t = str(hour_of_the_match).strip()
        if ":" not in t:
            h, m, s = int(t), 0, 0
        else:
            parts = t.split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            s = int(parts[2]) if len(parts) > 2 else 0

    # UTC+1 fixed offset (no DST)
    dt_local = pd.Timestamp(d.year, d.month, d.day, h, m, s).tz_localize("Etc/GMT-1")
    dt_utc = dt_local.tz_convert("UTC").floor("h")
    return dt_utc.isoformat().replace("+00:00", "Z")

def _parse_dt_to_utc_hour(dt_iso: str) -> pd.Timestamp:
    return pd.to_datetime(dt_iso, utc=True, errors="raise").floor("h")

# =============================================================================
# 2) Open-Meteo request helper
# =============================================================================

def _openmeteo_get(url: str, params: dict) -> dict:
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# =============================================================================
# 3) API calls (past + future)
# =============================================================================

def get_past_weather_features(
    latitude: float,
    longitude: float,
    dt_iso: str,
    source: Literal["auto", "archive", "forecast"] = "auto",
    timezone: str = "UTC",
    auto_archive_older_than_hours: int = 48,
) -> Dict[str, Optional[float]]:
    dt_utc = _parse_dt_to_utc_hour(dt_iso)
    day = dt_utc.strftime("%Y-%m-%d")

    if source == "auto":
        now_utc = pd.Timestamp.now(tz="UTC")
        age_hours = (now_utc - dt_utc).total_seconds() / 3600.0
        chosen = "archive" if age_hours > auto_archive_older_than_hours else "forecast"
    else:
        chosen = source

    base_url = (
        "https://archive-api.open-meteo.com/v1/archive"
        if chosen == "archive"
        else "https://api.open-meteo.com/v1/forecast"
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": day,
        "end_date": day,
        "hourly": HOURLY_VARS,
        "timezone": timezone,
    }

    data = _openmeteo_get(base_url, params)

    if "hourly" not in data or "time" not in data["hourly"]:
        raise RuntimeError(f"Unexpected API response structure: {data.keys()}")

    df = pd.DataFrame(data["hourly"])

    # Keep timezone="UTC" to make matching reliable
    df["time"] = pd.to_datetime(df["time"], utc=True)
    row = df.loc[df["time"] == dt_utc]

    if row.empty:
        raise ValueError(f"No hourly data found for {dt_iso} at ({latitude}, {longitude}).")

    raw = row.iloc[0].to_dict()
    pressure = raw.get("pressure_msl") if raw.get("pressure_msl") is not None else raw.get("surface_pressure")

    return {
        "temp_c": raw.get("temperature_2m"),
        "humidity_pct": raw.get("relative_humidity_2m"),
        "precip_mm": raw.get("precipitation"),
        "pressure_hpa": pressure,
        "wind_speed_ms": raw.get("wind_speed_10m"),
        "cloud_cover_pct": raw.get("cloud_cover"),
    }

def get_future_weather_features(
    latitude: float,
    longitude: float,
    dt_iso: str,
    timezone: str = "UTC",
    forecast_days: int = 16,
) -> Dict[str, Optional[float]]:
    dt_utc = _parse_dt_to_utc_hour(dt_iso)
    day = dt_utc.strftime("%Y-%m-%d")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": day,
        "end_date": day,
        "hourly": HOURLY_VARS,
        "timezone": timezone,
        "forecast_days": forecast_days,
    }

    data = _openmeteo_get(url, params)

    df = pd.DataFrame(data["hourly"])

    # Keep timezone="UTC" to make matching reliable
    df["time"] = pd.to_datetime(df["time"], utc=True)
    row = df.loc[df["time"] == dt_utc]

    if row.empty:
        raise ValueError(
            f"No forecast hourly data found for {dt_iso} at ({latitude}, {longitude}). "
            f"Maybe outside horizon ({forecast_days} days)."
        )

    raw = row.iloc[0].to_dict()
    pressure = raw.get("pressure_msl") if raw.get("pressure_msl") is not None else raw.get("surface_pressure")

    return {
        "temp_c": raw.get("temperature_2m"),
        "humidity_pct": raw.get("relative_humidity_2m"),
        "precip_mm": raw.get("precipitation"),
        "pressure_hpa": pressure,
        "wind_speed_ms": raw.get("wind_speed_10m"),
        "cloud_cover_pct": raw.get("cloud_cover"),
    }

# =============================================================================
# 4) DataFrame wrapper (auto past vs future)
# =============================================================================

def add_weather_features_auto_past_future(
    matches_df: pd.DataFrame,
    *,
    api_timezone: str = "UTC",
    forecast_days: int = 16,
    cache: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Expected columns:
      - latitude
      - longitude
      - date_of_match
      - hour_of_the_match  (UTC+1 fixed offset)

    Logic per row:
      - if match datetime (UTC) < now -> get_weather_features(..., source="archive")
      - else                          -> get_future_weather_features(...)
    """

    required = ["latitude", "longitude", "date_of_match", "hour_of_the_match"]
    missing = [c for c in required if c not in matches_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = matches_df.copy()

    # Build UTC datetime string per row (Z)
    out["dt_iso_utc"] = out.apply(
        lambda r: _build_dt_iso_utc_from_match_cols(r["date_of_match"], r["hour_of_the_match"]),
        axis=1,
    )

    now_utc = pd.Timestamp.now(tz="UTC")

    # Cache by (lat, lon, day, used_fn)
    local_cache: Dict[Tuple[float, float, str, str], Dict[str, Optional[float]]] = {}

    def _cache_key(lat: float, lon: float, dt_iso_utc: str, used: str) -> Tuple[float, float, str, str]:
        day = pd.to_datetime(dt_iso_utc, utc=True).strftime("%Y-%m-%d")
        return (round(lat, 5), round(lon, 5), day, used)

    features_rows = []

    for idx, r in out.iterrows():
        lat = float(r["latitude"])
        lon = float(r["longitude"])
        dt_iso = r["dt_iso_utc"]
        dt_utc = pd.to_datetime(dt_iso, utc=True)

        used = "future" if dt_utc >= now_utc else "past"
        key = _cache_key(lat, lon, dt_iso, used)

        if cache and key in local_cache:
            feats = local_cache[key]
        else:
            try:
                if used == "past":
                    feats = get_past_weather_features(
                        latitude=lat,
                        longitude=lon,
                        dt_iso=dt_iso,
                        source="archive",
                        timezone=api_timezone,
                    )
                else:
                    feats = get_future_weather_features(
                        latitude=lat,
                        longitude=lon,
                        dt_iso=dt_iso,
                        timezone=api_timezone,
                        forecast_days=forecast_days,
                    )
            except Exception as e:
                if verbose:
                    print(f"[weather] row={idx} used={used} dt={dt_iso} lat={lat} lon={lon} -> ERROR: {e}")
                feats = {c: None for c in FEATURE_COLS}

            if cache:
                local_cache[key] = feats

        features_rows.append(feats)

    feats_df = pd.DataFrame(features_rows, index=out.index)
    out = pd.concat([out, feats_df], axis=1)
    return out