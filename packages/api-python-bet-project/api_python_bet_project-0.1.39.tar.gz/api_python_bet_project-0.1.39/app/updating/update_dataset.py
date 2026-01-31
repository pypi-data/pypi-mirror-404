"""
Dataset updater module.
Contains the DatasetUpdater class that orchestrates all data collection,
processing, and feature engineering steps.
"""

import os
from typing import Optional, List, Dict, Tuple, Any
import pandas as pd

# Import custom modules
from scrapers.sofascore_scraper import SofaScoreScraper
from utils.date import get_previous_days, validate_execution_day, season_from_date, sort_by_match_datetime
from processing.teams.teams import enrich_with_team_history, update_league_winners, update_european_winners
from utils.format import _format_paths
from processing.ranking.league_ranking import LeagueRanking

import traceback

class DatasetUpdater:
    """Main class to orchestrate the dataset update process."""

    def __init__(
        self,
        features_config: Dict[str, any],
        competitions_config: Dict[str, Dict],
        paths: Dict[str, str],
    ):
        """
        Initialize DatasetUpdater with configuration from Settings.

        Args:
            features_config: Configuration for feature engineering
            competitions_config: Configuration for competitions
            dataset_csv: Path to the dataset CSV file
        """
        self.fbref_informations = features_config['fbref_informations']
        self.fbref_work_features = features_config['fbref_work_features']
        self.ranking_informations = features_config['ranking_informations']
        self.teams_informations = features_config['teams_informations']
        self.competitions_config = competitions_config
        self.paths = paths

    def update_dataset(
        self, date: Optional[str] = None, competition: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Main method to update the dataset with new matches and features.

        Process:
        0. Validate execution day (must be Tuesday or Friday):
        - If date provided: Check if it's Tuesday or Friday
        - If no date: Use today and check if it's Tuesday or Friday
        - Friday: Get matches for Fri, Sat, Sun, Mon (4 days)
        - Tuesday: Get matches for Tue, Wed, Thu (3 days)
        - Other days: Return error message
        1. Iterate through competitions (all or specific one)
        2. For each competition:
        - Scrape match data from FBRef (leagues, cups, supercups, european, international)
        - Check for new teams and add them if needed (scraping Transfermarkt)
        - Calculate team rankings and trophy information
        - Organize matches by date and time
        3. Apply feature engineering (competition-specific and general)
        4. Append to existing CSV dataset

        Args:
            date: Date to process (format: YYYY-MM-DD). If None, uses today.
                Must be Tuesday or Friday.
            competition: Specific competition to update (None for all)

        Returns:
            DataFrame with updated match data and features

        Raises:
            ValueError: If the date is not a Tuesday or Friday
        """
        print(f"        Starting past data update process")

        # Step 0: Validate execution day
        try:
            execution_date = validate_execution_day(date)
        except ValueError as e:
            error_msg = str(e)
            print(f"ERROR: {error_msg}")
            raise

        # Determine date range based on validated day
        days = get_previous_days(execution_date)

        last_season = season_from_date(execution_date)

        # Step 1: Determine which competitions to process
        competitions_list = self._get_competitions(competition, last_season)

        # Define fixed paths BEFORE the loop (these don't have placeholders)
        matches_csv_path = self.paths["matches"]
        players_csv_path = self.paths["players"]
        keepers_csv_path = self.paths["keepers"]
        teams_csv_path = self.paths["teams"]
        
        # Ensure parent folders exist for fixed paths
        for _p in [matches_csv_path, players_csv_path, keepers_csv_path, teams_csv_path]:
            _parent = os.path.dirname(_p)
            if _parent:
                os.makedirs(_parent, exist_ok=True)

        matches = pd.DataFrame()

        # Read existing matches, combine with new ones, and save
        all_matches = (
            pd.read_csv(matches_csv_path)
            if os.path.exists(matches_csv_path)
            else pd.DataFrame()
        )

        # Step 2: Process each competition
        for comp_info in competitions_list:
            comp_name = comp_info["name"]
            comp_country = comp_info["country"]
            comp_gameweeks = comp_info["number_of_gameweeks"]

            # Only format the ranking path (it has placeholders)
            formatted_paths = _format_paths(
                self.paths,
                last_season=last_season,
                country=comp_country,
                competition=comp_name,
            )

            ranking_csv_path = formatted_paths["ranking"]
            
            # Ensure parent folder exists for ranking
            _parent = os.path.dirname(ranking_csv_path)
            if _parent:
                os.makedirs(_parent, exist_ok=True)

            print(f"            Processing competition: {comp_name} - {comp_country}")

            try:
                comp_matches = self._process_competition(
                    all_matches,
                    comp_name,
                    comp_country,
                    comp_gameweeks,
                    matches_csv_path,   # Fixed path, same for all competitions
                    players_csv_path,   # Fixed path, same for all competitions
                    keepers_csv_path,   # Fixed path, same for all competitions
                    ranking_csv_path,   # Variable path per competition
                    teams_csv_path,     # Fixed path, same for all competitions
                    days,
                    last_season,
                )

                if comp_matches is not None and len(comp_matches) > 0:
                    matches = pd.concat([matches, comp_matches], ignore_index=True)
                    print(f"                Added {len(comp_matches)} matches from {comp_name}")

            except Exception as e:
                print(f"                ERROR processing {comp_name}: {type(e).__name__}: {str(e)}")
                traceback.print_exc()
                continue

        # Check if any matches were found across ALL competitions
        if matches.empty:
            print("            No new matches found")
            return pd.DataFrame()
        
        matches = sort_by_match_datetime(matches)
        if all_matches.empty:
            final_all_matches = matches.copy()
        elif matches.empty:
            final_all_matches = all_matches.copy()
        else:
            final_all_matches = pd.concat([all_matches, matches], ignore_index=True)
        
        final_all_matches.to_csv(matches_csv_path, index=False, encoding="utf-8")
        
        print(f"            Saved {len(matches)} new matches. Total matches in dataset: {len(final_all_matches)}")

        return matches

    def _get_competitions(
        self, competition: Optional[str], last_season: Tuple[str, int, int]
    ) -> List[Dict[str, Any]]:
        """
        Get list of competitions to process with their full configuration.

        Args:
            competition: Specific competition or None for all
            last_season: Tuple with (season_string, start_year, end_year)

        Returns:
            List of dictionaries containing competition data with structure:
            [
                {
                    'name': 'liga',
                    'country': 'spain',
                    'number_of_gameweeks': 38,
                    'paths': {
                        'ranking': 'https://...',
                        'teams_players': 'https://...',
                        'trophies': 'https://...'
                    },
                    'information_urls': {
                        'matches': 'https://fbref.com/...',
                        'fotmob': 'https://www.fotmob.com/...',
                        'teams': 'https://www.transfermarkt.com/...'
                    }
                },
                ...
            ]

        Raises:
            ValueError: If specified competition doesn't exist in config
        """
        # Determine which competitions to process
        if competition:
            if competition not in self.competitions_config:
                available = list(self.competitions_config.keys())
                raise ValueError(
                    f"Competition '{competition}' not found in configuration. "
                    f"Available competitions: {available}"
                )
            competitions_to_process = [competition]
        else:
            competitions_to_process = list(self.competitions_config.keys())

        # Build detailed competition list
        detailed_competitions = []

        for comp_name in competitions_to_process:
            competition_config = self.competitions_config.get(comp_name, {})

            # Extract country
            country = competition_config.get("country", "unknown")
            
            # Extract number of gameweeks
            number_of_gameweeks = competition_config.get("number_of_gameweeks", 38)
            
            # Extract and format information scraping URLs
            info_urls = competition_config.get("information_scraping_urls", {})
            formatted_info_urls = {}

            for url_key, url_template in info_urls.items():
                if url_key == "fotmob":
                    continue
                else:
                    # Format other URLs normally
                    formatted_info_urls[url_key] = url_template.format(
                        last_season=last_season
                    )

            # Build competition dictionary
            comp_dict = {
                "name": comp_name,
                "country": country,
                "number_of_gameweeks": number_of_gameweeks,
                "information_urls": formatted_info_urls,
            }

            detailed_competitions.append(comp_dict)

        return detailed_competitions

    def _process_competition(
        self,
        all_matches: pd.DataFrame,
        comp_name: str,
        comp_country: str,
        comp_gameweeks: Optional[int],
        matches_csv_path: str,
        players_csv_path: str,
        keepers_csv_path: str,
        ranking_csv_path: str,
        teams_csv_path: str,
        days: List[str],
        last_season: Tuple[str, int, int],
    ) -> pd.DataFrame:
        """
        Process a single competition and return match data.

        Args:
            comp_info: Dictionary containing competition information:
                {
                    'name': str,
                    'country': str,
                    'paths': {
                        'ranking': str,
                        'matches': str,
                        'teams': str,
                        'teams_players': str,
                        'trophies': str
                    }
                }
            days: List of dates to process
            execution_date: Date of execution

        Returns:
            List of match dictionaries
        """
        # Get competition configuration
        comp_config = self.competitions_config[comp_name]

        # Determine competition type from config or infer from name
        comp_type = self._infer_competition_type(comp_name)

        # Scrape match data from FBRef
        scraper = SofaScoreScraper(headless=True, verbose=False)

        # Run the scraper to get DataFrame-like objects
        df_matches, players_data, keepers_data = scraper.run_after()

        df = scraper.scrape_matches(
            url="https://www.sofascore.com/football/tournament/spain/laliga/8",
            season="24/25",
            max_rounds=38,
            target_dates=days
        )

        # If no matches found, stop processing
        if df_matches.empty:
            print(f"                No matches to process")
            return pd.DataFrame()
        
        current_gameweek = int(df_matches['gameweek'].max())

        if comp_type == "league":

            # Check if gameweek is comp_gameweeks BEFORE calling the function
            if current_gameweek == comp_gameweeks:
                df_matches = scraper.scrape_league_standings(
                    ranking_csv_path=ranking_csv_path,
                    recent_matches_df=df_matches,
                    all_matches_df=all_matches,
                    gameweek=current_gameweek,
                    verbose=False
                )

                df_matches = enrich_with_team_history(
                    df_matches,
                    self.teams_informations,
                    teams_csv_path,
                    comp_country
                )

                update_league_winners(
                    ranking_csv_path=ranking_csv_path,
                    trophies_csv_path=teams_csv_path,
                    comp_gameweeks=comp_gameweeks,
                    verbose=False
                )
            else:
                manager = LeagueRanking()

                # Ejecuta todo el proceso
                df_matches = manager.get_team_rankings(
                    ranking_csv_path=ranking_csv_path,
                    recent_matches_df=df_matches,
                    historical_matches_csv_path=matches_csv_path
                )

                df_matches = enrich_with_team_history(
                    df_matches,
                    self.teams_informations,
                    teams_csv_path,
                    comp_country
                )
        elif comp_type == "european":
            df_matches = enrich_with_team_history(
                df_matches,
                self.teams_informations,
                teams_csv_path,
                comp_country
            )
            if current_gameweek == comp_gameweeks:
                update_european_winners(
                    trophies_csv_path=teams_csv_path,
                    final_match_df=df_matches,
                    competition_name=comp_name,
                    verbose=False
                )

        # --- Ensure parent folder exists for players CSVs ---
        _parent = os.path.dirname(players_csv_path)
        if _parent:
            os.makedirs(_parent, exist_ok=True)

        # ---------- PLAYERS ----------
        raw = players_data
        if isinstance(raw, pd.DataFrame):
            df_players = raw
        elif isinstance(raw, list):
            if not raw:
                df_players = pd.DataFrame()
            elif all(isinstance(x, dict) for x in raw):
                df_players = pd.DataFrame(raw)
            elif all(isinstance(x, pd.DataFrame) for x in raw):
                df_players = pd.concat(raw, ignore_index=True)
            elif all(hasattr(x, "to_dict") for x in raw):
                df_players = pd.DataFrame([x.to_dict() for x in raw])
            else:
                raise TypeError("players_data list has unsupported element types")
        else:
            raise TypeError(f"Unsupported players_data type: {type(raw)}")

        # Ensure parent folder exists
        dirpath = os.path.dirname(os.path.abspath(players_csv_path))
        os.makedirs(dirpath, exist_ok=True)

        # Check if file already exists
        file_exists = os.path.isfile(players_csv_path)

        if df_players is not None and not df_players.empty:
            if file_exists:
                # Read existing data
                df_existing = pd.read_csv(players_csv_path, encoding="utf-8")
                
                # Accumulate yellow cards PER COMPETITION_TYPE (league vs european)
                if 'Players' in df_existing.columns and 'PlayersYellowCards' in df_existing.columns:
                    if 'Players' in df_players.columns and 'PlayersYellowCards' in df_players.columns:
                        # Create dict with previous yellow cards per player PER COMPETITION_TYPE
                        # Key: (player_name, competition_type, team_name), Value: max yellow cards
                        if 'competition_type' in df_existing.columns and 'team_name' in df_existing.columns:
                            previous_yellows = df_existing.groupby(['Players', 'competition_type', 'team_name'])['PlayersYellowCards'].max().to_dict()
                        else:
                            # Fallback if columns don't exist
                            previous_yellows = df_existing.groupby('Players')['PlayersYellowCards'].max().to_dict()
                        
                        # For each new player record, accumulate yellow cards
                        def accumulate_yellows(row):
                            player_name = row['Players']
                            current_yellows = row.get('PlayersYellowCards', 0)
                            gameweek = row.get('gameweek', None)
                            
                            # CRITICAL: If gameweek is 1, start fresh (new season)
                            if pd.notna(gameweek) and int(float(gameweek)) == 1:
                                # New season starts, don't accumulate
                                return current_yellows
                            
                            # Get competition_type and team_name if available
                            if ('competition_type' in row.index and 'team_name' in row.index and 
                                'competition_type' in df_existing.columns and 'team_name' in df_existing.columns):
                                competition_type = row['competition_type']
                                team_name = row['team_name']
                                key = (player_name, competition_type, team_name)
                            else:
                                key = player_name
                            
                            # If player exists in previous data for this competition_type and team
                            if key in previous_yellows:
                                prev_yellows = previous_yellows[key]
                                # If there's an increment, add it to the previous total
                                if pd.notna(current_yellows) and pd.notna(prev_yellows):
                                    # Convert to numeric types to handle both int and str
                                    try:
                                        # Handle empty strings
                                        prev = float(prev_yellows) if prev_yellows != '' else 0.0
                                        curr = float(current_yellows) if current_yellows != '' else 0.0
                                        # Accumulate: previous + new cards from this batch
                                        return int(prev + curr)
                                    except (ValueError, TypeError):
                                        # If conversion fails, return current value
                                        return current_yellows
                            
                            return current_yellows
                        
                        df_players['PlayersYellowCards'] = df_players.apply(accumulate_yellows, axis=1)
                
                # Append new data to existing
                df_combined = pd.concat([df_existing, df_players], ignore_index=True)
                
                # Write complete updated data (overwrite)
                df_combined.to_csv(
                    players_csv_path,
                    mode="w",
                    header=True,
                    index=False,
                    encoding="utf-8",
                )
            else:
                # First time writing, no accumulation needed
                df_players.to_csv(
                    players_csv_path,
                    mode="w",
                    header=True,
                    index=False,
                    encoding="utf-8",
                )

        # ---------- KEEPERS ----------
        raw = keepers_data
        if isinstance(raw, pd.DataFrame):
            df_keepers = raw
        elif isinstance(raw, list):
            if not raw:
                df_keepers = pd.DataFrame()
            elif all(isinstance(x, dict) for x in raw):
                df_keepers = pd.DataFrame(raw)
            elif all(isinstance(x, pd.DataFrame) for x in raw):
                df_keepers = pd.concat(raw, ignore_index=True)
            elif all(hasattr(x, "to_dict") for x in raw):
                df_keepers = pd.DataFrame([x.to_dict() for x in raw])
            else:
                raise TypeError("keepers_data list has unsupported element types")
        else:
            raise TypeError(f"Unsupported keepers_data type: {type(raw)}")

        # Ensure parent folder exists
        dirpath = os.path.dirname(os.path.abspath(keepers_csv_path))
        os.makedirs(dirpath, exist_ok=True)

        # Check if file already exists
        file_exists = os.path.isfile(keepers_csv_path)

        if df_keepers is not None and not df_keepers.empty:
            if file_exists:
                # Read existing data
                df_existing = pd.read_csv(keepers_csv_path, encoding="utf-8")
                
                # Accumulate yellow cards for keepers PER COMPETITION_TYPE (league vs european)
                if 'Players' in df_existing.columns and 'PlayersYellowCards' in df_existing.columns:
                    if 'Players' in df_keepers.columns and 'PlayersYellowCards' in df_keepers.columns:
                        # Create dict with previous yellow cards per keeper PER COMPETITION_TYPE
                        # Key: (player_name, competition_type, team_name), Value: max yellow cards
                        if 'competition_type' in df_existing.columns and 'team_name' in df_existing.columns:
                            previous_yellows = df_existing.groupby(['Players', 'competition_type', 'team_name'])['PlayersYellowCards'].max().to_dict()
                        else:
                            # Fallback if columns don't exist
                            previous_yellows = df_existing.groupby('Players')['PlayersYellowCards'].max().to_dict()
                        
                        # For each new keeper record, accumulate yellow cards
                        def accumulate_yellows(row):
                            player_name = row['Players']
                            current_yellows = row.get('PlayersYellowCards', 0)
                            gameweek = row.get('gameweek', None)
                            
                            # CRITICAL: If gameweek is 1, start fresh (new season)
                            if pd.notna(gameweek) and int(float(gameweek)) == 1:
                                # New season starts, don't accumulate
                                return current_yellows
                            
                            # Get competition_type and team_name if available
                            if ('competition_type' in row.index and 'team_name' in row.index and 
                                'competition_type' in df_existing.columns and 'team_name' in df_existing.columns):
                                competition_type = row['competition_type']
                                team_name = row['team_name']
                                key = (player_name, competition_type, team_name)
                            else:
                                key = player_name
                            
                            # If keeper exists in previous data for this competition_type and team
                            if key in previous_yellows:
                                prev_yellows = previous_yellows[key]
                                # If there's an increment, add it to the previous total
                                if pd.notna(current_yellows) and pd.notna(prev_yellows):
                                    # Convert to numeric types to handle both int and str
                                    try:
                                        # Handle empty strings
                                        prev = float(prev_yellows) if prev_yellows != '' else 0.0
                                        curr = float(current_yellows) if current_yellows != '' else 0.0
                                        # Accumulate: previous + new cards from this batch
                                        return int(prev + curr)
                                    except (ValueError, TypeError):
                                        # If conversion fails, return current value
                                        return current_yellows
                            
                            return current_yellows
                        
                        df_keepers['PlayersYellowCards'] = df_keepers.apply(accumulate_yellows, axis=1)
                
                # Append new data to existing
                df_combined = pd.concat([df_existing, df_keepers], ignore_index=True)
                
                # Write complete updated data (overwrite)
                df_combined.to_csv(
                    keepers_csv_path,
                    mode="w",
                    header=True,
                    index=False,
                    encoding="utf-8",
                )
            else:
                # First time writing, no accumulation needed
                df_keepers.to_csv(
                    keepers_csv_path,
                    mode="w",
                    header=True,
                    index=False,
                    encoding="utf-8",
                )

        return df_matches

    def _infer_competition_type(self, competition: str) -> str:
        """
        Infer competition type from competition name.

        Args:
            competition: Competition identifier

        Returns:
            Competition type: 'league', 'european'
        """
        comp_lower = competition.lower()

        if "uefa" in comp_lower:
            return "european"

        if (
            "league" in comp_lower
            or "liga" in comp_lower
            or "serie" in comp_lower
            or "bundesliga" in comp_lower
            or "ligue" in comp_lower
        ):
            return "league"

        return "league"

    def _prepare_target_matches(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract home_team, away_team, and date from a DataFrame to prepare
        target matches for FotMob scraper.

        Args:
            df: DataFrame with columns ['home_team_name', 'away_team_name', 'date_of_match']

        Returns:
            DataFrame with columns ['date', 'home_team', 'away_team'] ready for scraper
        """
        # Select relevant columns
        target_matches = df[
            ["date_of_match", "home_team_name", "away_team_name"]
        ].copy()

        # Rename columns to match scraper expected format
        target_matches = target_matches.rename(
            columns={
                "date_of_match": "date_of_match",
                "home_team_name": "home_team",
                "away_team_name": "away_team",
            }
        )

        # Remove duplicates if any
        target_matches = target_matches.drop_duplicates()

        # Reset index
        target_matches = target_matches.reset_index(drop=True)

        return target_matches