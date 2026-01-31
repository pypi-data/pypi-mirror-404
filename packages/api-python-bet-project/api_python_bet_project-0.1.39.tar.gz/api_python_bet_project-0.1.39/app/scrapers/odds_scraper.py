import os
import requests
import pandas as pd
from bs4 import BeautifulSoup

TEAM_NAME_MAPPING = {
    "Leganes": "Leganes",
    "Alaves": "Alaves",
    "Valencia": "Valencia",
    "Las Palmas": "Las_Palmas",
    "Celta": "Celta_Vigo",
    "Sociedad": "Real_Sociedad",
    "Ath Madrid": "Atletico_Madrid",
    "Sevilla": "Sevilla",
    "Espanol": "Espanyol",
    "Ath Bilbao": "Athletic_Club",
    "Getafe": "Getafe",
    "Barcelona": "Barcelona",
    "Betis": "Real_Betis",
    "La Coruna": "Deportivo_La_Coruna",
    "Real Madrid": "Real_Madrid",
    "Levante": "Levante",
    "Villarreal": "Villarreal",
    "Malaga": "Malaga",
    "Eibar": "Eibar",
    "Girona": "Girona",
    "Granada": "Granada",
    "Vallecano": "Rayo_Vallecano",
    "Almeria": "Almeria",
    "Mallorca": "Mallorca",
    "Valladolid": "Valladolid"
}

RENAME_MAP = {
    "B365H": "b365_odd_home", "B365D": "b365_odd_draw", "B365A": "b365_odd_away",
    "BWH": "bwin_odd_home", "BWD": "bwin_odd_draw", "BWA": "bwin_odd_away",
    "IWH": "iw_odd_home", "IWD": "iw_odd_draw", "IWA": "iw_odd_away",
    "PSH": "ps_odd_home", "PSD": "ps_odd_draw", "PSA": "ps_odd_away",
    "WHH": "wh_odd_home", "WHD": "wh_odd_draw", "WHA": "wh_odd_away",
    "VCH": "vc_odd_home", "VCD": "vc_odd_draw", "VCA": "vc_odd_away",
    "MaxH": "max_odd_home", "MaxD": "max_odd_draw", "MaxA": "max_odd_away",
    "AvgH": "avg_odd_home", "AvgD": "avg_odd_draw", "AvgA": "avg_odd_away"
}

ODDS_COLS = list(RENAME_MAP.keys())

# Define prefix list for reusable filtering
ODDS_PREFIXES = ["b365", "bwin", "iw", "ps", "wh", "vc", "max", "avg"]

def get_short_season_code(season):
    # Convert season string like '2024-2025' to short format '2425' for football-data URL
    return season[2:4] + season[-2:]

# Scrape football-data.co.uk to find the URL for the betting CSV file for the given season
def download_betting_csv(season):
    short_code = get_short_season_code(season)
    url = "https://www.football-data.co.uk/spainm.php"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Loop through all anchor tags to find the one matching La Liga betting CSV for the season
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if f"mmz4281/{short_code}/SP1.csv" in href:
            return f"https://www.football-data.co.uk/{href}"
    return None

def process_odds_for_season(season):
    matches_path = f"app/database/{season}/matches_{season}.csv"
    betting_path = f"app/database/{season}/betting_{season}.csv"

    betting_url = download_betting_csv(season)
    if not betting_url:
        print("No valid betting.csv URL found.")
        return

    os.makedirs(os.path.dirname(betting_path), exist_ok=True)
    try:
        print(f"Downloading betting data from {betting_url}")
        response = requests.get(betting_url)
        with open(betting_path, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Failed to download betting CSV: {e}")
        return

    try:
        betting_df = pd.read_csv(betting_path)
        matches_df = pd.read_csv(matches_path)
    except Exception as e:
        print(f"Error loading CSVs: {e}")
        return

    # Normalize team names
    betting_df["HomeTeam"] = betting_df["HomeTeam"].replace(TEAM_NAME_MAPPING)
    betting_df["AwayTeam"] = betting_df["AwayTeam"].replace(TEAM_NAME_MAPPING)

    # Extract relevant columns
    base_cols = ["HomeTeam", "AwayTeam", "Date"]
    available_cols = base_cols + [col for col in ODDS_COLS if col in betting_df.columns]
    betting_df = betting_df[available_cols].copy()

    # Rename columns
    betting_df.rename(columns=RENAME_MAP, inplace=True)

    # Fill missing odds with mean across other available odds of same type (home, draw, away)
    # For each outcome (home, draw, away), fill missing odds with the row-wise mean of other available odds
    for outcome in ["home", "draw", "away"]:
        odd_cols = [col for col in betting_df.columns if col.endswith(f"_odd_{outcome}")]
        row_means = betting_df[odd_cols].mean(axis=1, skipna=True)
        for col in odd_cols:
            betting_df[col] = betting_df[col].fillna(row_means)

    # Remove existing odds columns in match data to avoid duplicates
    for col in betting_df.columns:
        if any(col.startswith(prefix) for prefix in ODDS_PREFIXES):
            if col in matches_df.columns:
                matches_df.drop(columns=col, inplace=True)

    # Merge betting odds with the match dataset based on team names
    merged = matches_df.merge(
        betting_df,
        how="left",
        left_on=["home_team_name", "away_team_name"],
        right_on=["HomeTeam", "AwayTeam"]
    )

    merged.drop(columns=["HomeTeam", "AwayTeam", "Date"], inplace=True)
    merged.to_csv(matches_path, index=False)
    print(f"Match data updated with all odds and probabilities: {matches_path}")
