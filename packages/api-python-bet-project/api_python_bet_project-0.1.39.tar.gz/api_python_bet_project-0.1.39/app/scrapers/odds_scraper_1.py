# odds_scraper_1.py

import os
from datetime import datetime
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup


class Odds_betting:
    """
    Download Bwin odds for La Liga from football-data.co.uk, transform them into
    implied probabilities, and merge into matches_<season>.csv.

    - Season format expected: 'YYYY-YYYY' (e.g., '2024-2025')
    - Writes results back into ../database/<season>/matches_<season>.csv
    """

    def __init__(self, last_season: str):
        self.last_season = last_season
        self.betting_url: Optional[str] = None
        self.matches_filename: Optional[str] = None
        self.betting_filename: Optional[str] = None
        self.betting_data: Optional[pd.DataFrame] = None
        self.match_data: Optional[pd.DataFrame] = None

        # Mapping from football-data names to your dataset team names
        self.team_name_mapping = {
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
            "Valladolid": "Valladolid",
            "Oviedo": "Oviedo",
            "Sociedad": "Real_Sociedad",
            "Osasuna": "Osasuna",
        }

    # ------------------------------ helpers ------------------------------

    @staticmethod
    def _req(url: str) -> requests.Response:
        """HTTP GET with default headers."""
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Connection": "keep-alive",
        }
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp

    @staticmethod
    def _to_yyyy_mm_dd(x: str) -> Optional[str]:
        """
        Try to normalize various football-data date formats to 'YYYY-MM-DD'.
        football-data typically uses 'DD/MM/YY' or 'DD/MM/YYYY'.
        """
        if pd.isna(x):
            return None
        s = str(x).strip()
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        # give up
        return None

    # ------------------------------ pipeline -----------------------------

    def load_data(self):
        """Find season CSV URL, download it, and load betting + matches CSVs."""
        # Build short season code: "2024-2025" → "2425"
        short_season = self.last_season[2:4] + self.last_season[-2:]

        # Source index page
        base_url = "https://www.football-data.co.uk/spainm.php"

        # Discover the CSV URL for La Liga (SP1) matching the short season code
        try:
            response = self._req(base_url)
        except Exception as e:
            print(f"❌ Failed to fetch index page: {e}")
            self.betting_data = pd.DataFrame()
            return

        soup = BeautifulSoup(response.text, "html.parser")
        self.betting_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # football-data structure: mmz4281/<YYYY seasons like 2425>/SP1.csv
            if f"mmz4281/{short_season}/SP1.csv" in href:
                self.betting_url = f"https://www.football-data.co.uk/{href}"
                break

        # Local paths
        self.matches_filename = (
            f"app/data/raw/{self.last_season}/matches_{self.last_season}.csv"
        )
        self.betting_filename = (
            f"app/data/raw/{self.last_season}/betting_{self.last_season}.csv"
        )

        # Download betting CSV
        if self.betting_url:
            os.makedirs(os.path.dirname(self.betting_filename), exist_ok=True)
            try:
                print(f"⬇️ Downloading betting data from {self.betting_url}")
                resp = self._req(self.betting_url)
                with open(self.betting_filename, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Betting CSV saved to: {self.betting_filename}")
            except Exception as e:
                print(f"❌ Failed to download or save CSV: {e}")
                self.betting_data = pd.DataFrame()
                return
        else:
            print("❌ No valid betting.csv URL found for this season.")
            self.betting_data = pd.DataFrame()
            return

        # Read CSVs
        try:
            self.betting_data = pd.read_csv(self.betting_filename)
        except Exception as e:
            print(f"❌ Error loading betting CSV: {e}")
            self.betting_data = pd.DataFrame()

        try:
            self.match_data = pd.read_csv(self.matches_filename)
        except Exception as e:
            print(f"❌ Error loading matches CSV: {e}")
            self.match_data = pd.DataFrame()

    def rename_teams(self):
        """Map football-data team names to your dataset naming."""
        if self.betting_data is None or self.betting_data.empty:
            print("⚠️ Warning: betting_data is empty.")
            return
        if (
            "HomeTeam" not in self.betting_data.columns
            or "AwayTeam" not in self.betting_data.columns
        ):
            print("❌ Columns 'HomeTeam'/'AwayTeam' not found in betting data.")
            return

        self.betting_data["HomeTeam"] = self.betting_data["HomeTeam"].replace(
            self.team_name_mapping
        )
        self.betting_data["AwayTeam"] = self.betting_data["AwayTeam"].replace(
            self.team_name_mapping
        )

    def extract_odds_columns(self):
        """Keep only the required columns if present."""
        if self.betting_data is None or self.betting_data.empty:
            print("⚠️ Warning: betting_data is empty.")
            return

        required_columns = ["Date", "HomeTeam", "AwayTeam", "BWH", "BWD", "BWA"]
        available = [c for c in required_columns if c in self.betting_data.columns]

        if not all(c in available for c in ["HomeTeam", "AwayTeam"]):
            print("❌ Missing essential columns in betting CSV.")
            self.betting_data = pd.DataFrame()
            return

        self.betting_data = self.betting_data[available].copy()

        # Normalize date if present
        if "Date" in self.betting_data.columns:
            self.betting_data["Date"] = self.betting_data["Date"].apply(
                self._to_yyyy_mm_dd
            )

    def compute_probabilities(self):
        """Convert Bwin odds to implied probabilities (margin-adjusted)."""
        if self.betting_data is None or self.betting_data.empty:
            print("⚠️ Warning: betting_data is empty, cannot compute probabilities.")
            return

        for col in ["BWH", "BWD", "BWA"]:
            if col not in self.betting_data.columns:
                self.betting_data[col] = pd.NA

        if self.betting_data[["BWH", "BWD", "BWA"]].isnull().any().any():
            print("⚠️ Warning: Some Bwin odds are missing (BWH, BWD, BWA).")

        # Store raw odds
        self.betting_data["odd_home"] = pd.to_numeric(
            self.betting_data.get("BWH"), errors="coerce"
        )
        self.betting_data["odd_draw"] = pd.to_numeric(
            self.betting_data.get("BWD"), errors="coerce"
        )
        self.betting_data["odd_away"] = pd.to_numeric(
            self.betting_data.get("BWA"), errors="coerce"
        )

        # Compute inverse probabilities
        with pd.option_context("mode.use_inf_as_na", True):
            self.betting_data["prob_home"] = 1.0 / self.betting_data["odd_home"]
            self.betting_data["prob_draw"] = 1.0 / self.betting_data["odd_draw"]
            self.betting_data["prob_away"] = 1.0 / self.betting_data["odd_away"]

        total_prob = (
            self.betting_data["prob_home"]
            + self.betting_data["prob_draw"]
            + self.betting_data["prob_away"]
        )

        # Normalize to remove overround
        self.betting_data["prob_home"] = self.betting_data["prob_home"] / total_prob
        self.betting_data["prob_draw"] = self.betting_data["prob_draw"] / total_prob
        self.betting_data["prob_away"] = self.betting_data["prob_away"] / total_prob

    def _merge_try_by_teams_and_date(self, merge_data: pd.DataFrame) -> pd.DataFrame:
        """Primary merge: (home, away, date) if 'date_of_match' exists in matches."""
        if self.match_data is None or self.match_data.empty:
            return pd.DataFrame()

        merged = self.match_data.copy()

        # Ensure date_of_match is normalized yyyy-mm-dd if present
        if "date_of_match" in merged.columns:
            merged["date_of_match"] = pd.to_datetime(
                merged["date_of_match"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

        # Try exact merge on names + date
        if "date_of_match" in merged.columns and "Date" in merge_data.columns:
            merged = merged.merge(
                merge_data,
                how="left",
                left_on=["home_team_name", "away_team_name", "date_of_match"],
                right_on=["HomeTeam", "AwayTeam", "Date"],
            )
        else:
            # Fallback to names only
            merged = merged.merge(
                merge_data,
                how="left",
                left_on=["home_team_name", "away_team_name"],
                right_on=["HomeTeam", "AwayTeam"],
            )
        return merged

    def merge_with_match_data(self):
        """Attach Bwin odds and probabilities to matches CSV."""
        if (
            self.betting_data is None
            or self.betting_data.empty
            or self.match_data is None
            or self.match_data.empty
        ):
            print("❌ Error: betting_data or match_data is empty.")
            return

        # Map of renames for the final columns
        rename_map = {
            "prob_home": "bwin_prob_home",
            "prob_draw": "bwin_prob_draw",
            "prob_away": "bwin_prob_away",
            "odd_home": "bwin_odd_home",
            "odd_draw": "bwin_odd_draw",
            "odd_away": "bwin_odd_away",
        }
        all_cols = list(rename_map.keys())

        # Drop if already present (to avoid duplicate columns)
        for c in rename_map.values():
            if c in self.match_data.columns:
                self.match_data.drop(columns=c, inplace=True)

        # Prepare merge frame
        merge_data = self.betting_data[
            ["HomeTeam", "AwayTeam"]
            + (["Date"] if "Date" in self.betting_data.columns else [])
            + all_cols
        ].copy()
        merge_data = merge_data.rename(columns=rename_map)

        # Attempt merge (home, away, date) first; fallback to (home, away)
        merged = self._merge_try_by_teams_and_date(merge_data)

        # Clean helper columns
        to_drop = [c for c in ["HomeTeam", "AwayTeam", "Date"] if c in merged.columns]
        if to_drop:
            merged.drop(columns=to_drop, inplace=True)

        self.match_data = merged

    def save_updated_data(self):
        """Save merged matches file back to disk."""
        if self.match_data is None or self.matches_filename is None:
            print("❌ Error: match_data or matches_filename not set.")
            return
        os.makedirs(os.path.dirname(self.matches_filename), exist_ok=True)
        self.match_data.to_csv(self.matches_filename, index=False)
        print(f"✅ Data with Bwin probabilities saved to {self.matches_filename}")

    # ------------------------------ runner -------------------------------

    def process_odds(self):
        """Run the complete pipeline."""
        self.load_data()
        self.rename_teams()
        self.extract_odds_columns()
        self.compute_probabilities()
        self.merge_with_match_data()
        self.save_updated_data()
