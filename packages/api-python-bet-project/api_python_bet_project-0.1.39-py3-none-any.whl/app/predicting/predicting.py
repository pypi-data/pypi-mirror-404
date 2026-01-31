"""
Dataset updater module.
Contains the DatasetUpdater class that orchestrates all data collection,
processing, and feature engineering steps.
"""

import os
from typing import Optional, List, Dict, Tuple, Any
import pandas as pd

# Import custom modules
from scrapers.fbref_scraper import FBRefScraper
from scrapers.fotmob_scraper import FotMobScraper
from scrapers.meteo_scraper import add_weather_features_auto_past_future
from processing.teams.teams import update_league_season_participation, update_european_season_participation, add_team_countries, filter_matches_by_country_and_history, enrich_with_team_history, get_initial_ranking_from_trophies
from feature_engineering.feature_engineering import MatchStatsCalculator
from scrapers.transfers_scraper import scrape_transfers_if_window_open, dedupe_and_merge_repeated_players_transfers
from processing.ranking.league_ranking import LeagueRanking
from processing.ranking.situation_ranking import TeamSituationAnalyzer
from feature_engineering.team_notes_fixtures import compute_team_notes_for_fixtures
from feature_engineering.temporal_features import add_circular_temporal_features, add_knockout_features 
from utils.date import get_next_days, validate_execution_day, season_from_date
from utils.format import _format_paths

class Predicting:
    """Main class to orchestrate the dataset update process."""

    def __init__(
        self,
        features_config: Dict[str, any],
        competitions_config: Dict[str, Dict],
        paths: Dict[str, str],
    ):
        """
        Initialize Predicting with configuration from Settings.

        Args:
            features_config: Configuration for feature engineering
            competitions_config: Configuration for competitions
            dataset_csv: Path to the dataset CSV file
        """
        self.fbref_informations = features_config['fbref_informations']
        self.fbref_work_features = features_config['fbref_work_features']
        self.fbref_features = features_config['fbref_features']
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
           - Scrape injury and suspension data from Fotmob
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
        print(f"        Starting feature engineering process")

        # Step 0: Validate execution day
        try:
            execution_date = validate_execution_day(date)
        except ValueError as e:
            error_msg = str(e)
            print(f"\nERROR: {error_msg}")
            raise

        # Determine date range based on validated day
        days = get_next_days(execution_date)

        last_season = season_from_date(execution_date)

        # Step 1: Determine which competitions to process
        competitions_list = self._get_competitions(competition, last_season)

        transfers_df = pd.DataFrame(columns=['player_name', 'old_team', 'new_team', 'transfer_nature'])

        # Step 2: Process each competition
        for comp_info in competitions_list:
            comp_name = comp_info["name"]
            comp_country = comp_info["country"]
            comp_suspensions = comp_info["suspensions"]
            comp_champions = comp_info["champions"]
            comp_europa_league = comp_info["europa_league"]
            comp_conference_league = comp_info["conference_league"]
            comp_relegated = comp_info["relegated"]
            comp_gameweeks = comp_info["number_of_gameweeks"]

            fotmob_url = comp_info["information_urls"]["fotmob"]
            summer_url = comp_info["information_urls"]["summer_transfers"]
            winter_url = comp_info["information_urls"]["winter_transfers"]

            formatted_paths = _format_paths(
                self.paths,
                last_season=last_season,
                country=comp_country,
                competition=comp_name,
            )

            matches_csv_path = formatted_paths["matches"]
            players_csv_path = formatted_paths["players"]
            keepers_csv_path = formatted_paths["keepers"]
            ranking_csv_path = formatted_paths["ranking"]
            dataset_global_csv_path = formatted_paths["dataset_global"]
            dataset_country_csv_path = formatted_paths["dataset_country"]
            dataset_competition_csv_path = formatted_paths["dataset_competition"]
            teams_csv_path = formatted_paths["teams"]
            stadiums_csv_path = formatted_paths["stadiums"]

            # --- Ensure parent folders exist for the three CSVs ---
            for _p in [matches_csv_path]:
                _parent = os.path.dirname(_p)
                if _parent:
                    os.makedirs(_parent, exist_ok=True)

            print(f"            Processing competition: {comp_name} - {comp_country}")

            try:
                self._process_competition(
                    execution_date,
                    comp_name,
                    comp_country,
                    comp_gameweeks,
                    comp_suspensions,
                    comp_champions,
                    comp_europa_league,
                    comp_conference_league,
                    comp_relegated,
                    matches_csv_path,
                    players_csv_path,
                    keepers_csv_path,
                    ranking_csv_path,
                    dataset_global_csv_path,
                    dataset_country_csv_path,
                    dataset_competition_csv_path,
                    teams_csv_path,
                    stadiums_csv_path,
                    days,
                    last_season,
                    fotmob_url,
                    summer_url,
                    winter_url,
                    transfers_df
                )

            except Exception as e:
                continue

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
            champions = competition_config.get("champions", {})
            europa_league = competition_config.get("europa_league", 0)
            conference_league = competition_config.get("conference_league", 0)
            relegated = competition_config.get("relegated", 0)
            number_of_gameweeks = competition_config.get("number_of_gameweeks", 38)

            suspensions = competition_config.get("suspensions", {})

            # Extract and format information scraping URLs
            info_urls = competition_config.get("information_scraping_urls", {})
            formatted_info_urls = {}

            for url_key, url_template in info_urls.items():
                if url_key == "fotmob":
                    # FotMob URL needs page parameter, store template without formatting page
                    formatted_info_urls[url_key] = url_template.format(
                        last_season=last_season,
                        page="{page}",  # Keep placeholder for later formatting
                    )
                else:
                    # Format other URLs normally
                    formatted_info_urls[url_key] = url_template.format(
                        last_season=last_season
                    )

            # Build competition dictionary
            comp_dict = {
                "name": comp_name,
                "country": country,
                "information_urls": formatted_info_urls,
                "suspensions": suspensions,
                "champions": champions,
                "europa_league": europa_league,
                "conference_league": conference_league,
                "relegated": relegated,
                "number_of_gameweeks": number_of_gameweeks,
            }

            detailed_competitions.append(comp_dict)

        return detailed_competitions

    def _process_competition(
        self,
        date: str,
        comp_name: str,
        comp_country: str,
        comp_gameweeks: int,
        comp_suspensions: Dict[str, Any],
        comp_champions: int,
        comp_europa_league: int,
        comp_conference_league: int,
        comp_relegated: int,
        matches_csv_path: str,
        players_csv_path: str,
        keepers_csv_path: str,
        ranking_csv_path: str,
        dataset_global_csv_path: str,
        teams_csv_path: str,
        stadiums_csv_path: str,
        days: List[str],
        last_season: Tuple[str, int, int],
        fotmob_url: str,
        summer_url: str,
        winter_url: str,
        transfers_df: pd.DataFrame,
    ) -> None:
        """
        Process a single competition and update datasets.

        Args:
            comp_name: Name of the competition
            comp_country: Country of the competition
            matches_csv_path: Path to matches CSV file
            players_csv_path: Path to players CSV file
            keepers_csv_path: Path to keepers CSV file
            ranking_csv_path: Path to ranking CSV file
            dataset_global_csv_path: Path to global dataset CSV file
            dataset_country_csv_path: Path to country dataset CSV file
            dataset_competition_csv_path: Path to competition dataset CSV file
            teams_csv_path: Path to teams CSV file
            stadiums_csv_path: Path to stadiums CSV file
            days: List of dates to process
            last_season: Tuple containing season information (name, start_year, end_year)
            fotmob_url: URL for FotMob scraping
        """

        # Get competition configuration
        comp_config = self.competitions_config[comp_name]
        comp_country = comp_config.get("country", comp_country)

        # Determine competition type from config or infer from name
        comp_type = self._infer_competition_type(comp_name)

        # Scrape match data from FBRef
        scraper = FBRefScraper(
            matches_csv_path,
            stadiums_csv_path,
            last_season, 
            comp_config, 
            comp_name, 
            comp_config, 
            comp_type, 
            days
        )

        # Run the scraper to get DataFrame
        df_matches = scraper.run_before()

        # If no matches found, stop processing
        if df_matches.empty:
            print(f"                No matches to process")
            return
        
        # Read past matches CSV
        try:
            past_matches = pd.read_csv(matches_csv_path)
        except Exception as e:
            print(f"                Not enough historical data to process matches")
            return pd.DataFrame()
        
        df_matches = add_team_countries(
            df_matches=df_matches,
            teams_path=teams_csv_path,
            comp_type=comp_type,
            comp_country=comp_country,
            comp_name=comp_name,
            verbose=True
        )

        df_matches = filter_matches_by_country_and_history(
            df_matches=df_matches,
            past_matches=past_matches,
            comp_name=comp_name,
            minimum_matches=18,
            verbose=True
        )

        # If no matches found, stop processing
        if df_matches.empty:
            print(f"                Not enough historical data to process matches")
            return
        
        print(f"                Imputing rankings...")

        current_gameweek = int(df_matches['gameweek'].max())

        # Calculate rankings and trophy information
        if comp_type == "league":
            
            # =====================================================================
            # LEAGUE COMPETITIONS
            # =====================================================================
            
            if current_gameweek == 1:
                # Gameweek 1: Update participation, get trophy-based ranking
                df_matches = update_league_season_participation(
                    df_matches=df_matches,
                    country=comp_country,
                    trophies_csv_path=teams_csv_path,
                    teams_columns=self.teams_informations,
                    verbose=True
                )
                
                # Get initial ranking from trophy history
                df_matches = get_initial_ranking_from_trophies(
                    df_matches=df_matches,
                    teams_path=teams_csv_path,
                    verbose=True
                )
            
            else:
                league_ranker = LeagueRanking(
                    ranking_csv_path,
                    self.ranking_informations,
                    teams_csv_path,
                    self.teams_informations,
                    comp_name,
                    comp_country,
                )
                # Gameweek 2+: Get ranking from last match
                df_matches = league_ranker.get_last_match_stats(
                    df_matches=df_matches,
                    past_matches=past_matches,
                    verbose=True
                )

            df_matches = add_circular_temporal_features(
                df_matches=df_matches,
                comp_type='league',
                max_gameweeks=38,
                verbose=True
            )

            new_transfers = scrape_transfers_if_window_open(
                summer_url=summer_url,
                winter_url=winter_url,
                date=date,
                delay=2.0,
                verbose=True
            )

            transfers_df = pd.concat([transfers_df, new_transfers], ignore_index=True)

            if comp_name == "primeira_liga":
                transfers_df = dedupe_and_merge_repeated_players_transfers(transfers_df)

            analyzer = TeamSituationAnalyzer(
                champions_league_spots=comp_champions,
                europa_league_spots=comp_europa_league,
                conference_league_spots=comp_conference_league,
                relegated_spots=comp_relegated,
                number_of_gameweeks=comp_gameweeks
            )

            # 2. Analizar partidos
            df_matches = analyzer.analyze_matches(
                df_matches=df_matches,
                rankings_csv_path=teams_csv_path
            )

        elif comp_type == "european":
            
            # =====================================================================
            # EUROPEAN COMPETITIONS
            # =====================================================================
            
            if current_gameweek == 1:
                # Gameweek 1: Update European participation
                df_matches = update_european_season_participation(
                    df_matches=df_matches,
                    competition=comp_name,
                    trophies_csv_path=teams_csv_path,
                    verbose=True
                )
                
                # Get initial ranking from trophy history
                df_matches = get_initial_ranking_from_trophies(
                    df_matches=df_matches,
                    teams_path=teams_csv_path,
                    verbose=True
                )
            
            else:
                league_ranker = LeagueRanking(
                    ranking_csv_path,
                    self.ranking_informations,
                    teams_csv_path,
                    self.teams_informations,
                    comp_name,
                    comp_country,
                )
                # Gameweek 2+: Get ranking from last match
                df_matches = league_ranker.get_last_match_stats(
                    df_matches=df_matches,
                    past_matches=past_matches,
                    verbose=True
                )

            df_matches = add_circular_temporal_features(
                df_matches=df_matches,
                comp_type='european',
                verbose=True
            )

            df_matches = add_knockout_features(
                df_matches=df_matches,
                verbose=True
            )

            transfers_df = dedupe_and_merge_repeated_players_transfers(transfers_df)
            
        # Enrich with team history (for all gameweeks)
        df_matches = enrich_with_team_history(
            df=df_matches,
            teams_columns=self.teams_informations,
            csv_path=teams_csv_path,
            country=comp_type
        )

        df_matches = add_weather_features_auto_past_future(df_matches)

        print(f"                Building teams' notes...")

        fotmob_df = self._prepare_target_matches(df_matches)
        scraper_fotmob = FotMobScraper()
        unavailable_list = scraper_fotmob.scrape_all_injuries(fotmob_df, fotmob_url)

        df_matches = compute_team_notes_for_fixtures(
            df_matches,
            past_matches,
            players_csv_path, 
            keepers_csv_path,
            unavailable_list=unavailable_list,
            transfers_df=transfers_df
        )

        df_matches = compute_team_notes_for_fixtures(
            fixtures_df=df_matches,
            past_matches=past_matches,
            players_csv_path=players_csv_path,
            keepers_csv_path=keepers_csv_path,
            teams_csv_path=teams_csv_path,
            unavailable_list=unavailable_list,
            transfers_df=transfers_df,
            apply_suspensions=True,
            suspension_config=comp_suspensions
        )

        # Hacer notas de los equipos aqui

        print(f"                Making feature engineering...")

        # Making feature engineering
        feature_engineer = MatchStatsCalculator(
            dataset_global_csv_path,
            comp_type,
            comp_country,
            self.fbref_features,
        )

        feature_engineer.data_update_dataset(df_matches)
        
    def _infer_competition_type(self, competition: str) -> str:
        """
        Infer competition type from competition name.

        Args:
            competition: Competition identifier

        Returns:
            Competition type: 'league', 'cup', 'supercup', 'european', or 'international'
        """
        comp_lower = competition.lower()

        if (
            "league" in comp_lower
            or "liga" in comp_lower
            or "serie" in comp_lower
            or "bundesliga" in comp_lower
            or "ligue" in comp_lower
        ):
            return "league"
        elif (
            "fa" in comp_lower
            or "carabao" in comp_lower
            or "rey" in comp_lower
            or "pokal" in comp_lower
            or "coppa" in comp_lower
        ):
            return "cup"
        elif (
            "supercup" in comp_lower
            or "supercopa" in comp_lower
            or "shield" in comp_lower
        ):
            return "supercup"
        elif "uefa" in comp_lower:
            return "european"
        elif "fifa" in comp_lower:
            return "international"
        else:
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
                "date_of_match": "date",
                "home_team_name": "home_team",
                "away_team_name": "away_team",
            }
        )

        # Remove duplicates if any
        target_matches = target_matches.drop_duplicates()

        # Reset index
        target_matches = target_matches.reset_index(drop=True)

        return target_matches
