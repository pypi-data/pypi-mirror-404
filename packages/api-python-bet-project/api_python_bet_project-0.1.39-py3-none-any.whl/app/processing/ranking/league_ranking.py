import pandas as pd
import numpy as np


class LeagueRanking:
    """
    Class to fetch team rankings from a rankings CSV file based on either:
    - The gameweek of recent matches (if more than 5 matches available)
    - The last match of each team in the competition (if less than 5 matches)
    """
    
    def __init__(self):
        """Initialize the TeamRankingFetcher"""
        pass
    
    def get_team_rankings(
        self,
        ranking_csv_path: str,
        recent_matches_df: pd.DataFrame,
        historical_matches_csv_path: str
    ) -> pd.DataFrame:
        """
        Add team ranking columns to the recent matches DataFrame.
        
        Args:
            ranking_csv_path: Path to the CSV file containing team rankings by gameweek
            recent_matches_df: DataFrame containing recent matches
            historical_matches_csv_path: Path to CSV file with all historical matches
            
        Returns:
            DataFrame with added columns:
            - home_team_rank
            - away_team_rank
            - home_team_points
            - away_team_points
            - home_team_goals_for
            - away_team_goals_for
            - home_team_goals_against
            - away_team_goals_against
            - home_team_goals_difference
            - away_team_goals_difference
        """
        
        # Make a copy to avoid modifying the original DataFrame
        df_updated = recent_matches_df.copy()
        
        # Load the rankings CSV
        rankings_df = pd.read_csv(ranking_csv_path)
        
        # Check if there are more than 5 matches in the recent matches DataFrame
        if len(recent_matches_df) > 5:
            df_updated = self._add_rankings_by_gameweek(
                df_updated, 
                rankings_df
            )
        else:
            df_updated = self._add_rankings_from_last_match(
                df_updated,
                historical_matches_csv_path,
                rankings_df
            )
        
        return df_updated
    
    def _add_rankings_by_gameweek(
        self,
        df: pd.DataFrame,
        rankings_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add ranking columns by identifying the gameweek from each match.
        
        Assumes df has columns: 'gameweek', 'home_team', 'away_team'
        (adjust column names as needed for your actual data structure)
        """
        
        # Identify column names
        if 'gameweek' in df.columns:
            gameweek_col = 'gameweek'
        else:
            raise ValueError("DataFrame must contain 'gameweek' or 'round' column")
        
        home_team_col = 'home_team' if 'home_team' in df.columns else ('home_team_name' if 'home_team_name' in df.columns else 'Home')
        away_team_col = 'away_team' if 'away_team' in df.columns else ('away_team_name' if 'away_team_name' in df.columns else 'Away')
        
        
        # Initialize new columns with None
        df['home_team_rank'] = None
        df['away_team_rank'] = None
        df['home_team_points'] = None
        df['away_team_points'] = None
        df['home_team_goals_for'] = None
        df['away_team_goals_for'] = None
        df['home_team_goals_against'] = None
        df['away_team_goals_against'] = None
        df['home_team_goals_difference'] = None
        df['away_team_goals_difference'] = None
                
        # Iterate over each match and add ranking information
        for idx, match in df.iterrows():
            
            gameweek = match[gameweek_col]
            
            home_team = match[home_team_col]
            
            away_team = match[away_team_col]
            
            # Filter rankings for the gameweek
            gameweek_rankings = rankings_df[rankings_df['gameweek'] == gameweek]
            
            # Get home team ranking
            home_ranking = gameweek_rankings[gameweek_rankings['team_name'] == home_team]
            # Get away team ranking
            away_ranking = gameweek_rankings[gameweek_rankings['team_name'] == away_team]
                        
            # If team found, add the data
            if not home_ranking.empty:
                home_ranking = home_ranking.iloc[0]
                df.at[idx, 'home_team_rank'] = int(home_ranking['team_rank'])
                df.at[idx, 'home_team_points'] = int(home_ranking['team_points'])
                df.at[idx, 'home_team_goals_for'] = int(home_ranking['team_goals_for'])
                df.at[idx, 'home_team_goals_against'] = int(home_ranking['team_goals_against'])
                df.at[idx, 'home_team_goals_difference'] = int(home_ranking['team_goals_difference'])
            
            if not away_ranking.empty:
                away_ranking = away_ranking.iloc[0]
                df.at[idx, 'away_team_rank'] = int(away_ranking['team_rank'])
                df.at[idx, 'away_team_points'] = int(away_ranking['team_points'])
                df.at[idx, 'away_team_goals_for'] = int(away_ranking['team_goals_for'])
                df.at[idx, 'away_team_goals_against'] = int(away_ranking['team_goals_against'])
                df.at[idx, 'away_team_goals_difference'] = int(away_ranking['team_goals_difference'])
        
        return df
    
    def _add_rankings_from_last_match(
        self,
        df: pd.DataFrame,
        historical_matches_csv_path: str,
        rankings_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add ranking columns from the last historical match of each team in the competition.
        
        Assumes historical matches CSV has columns like: 'date_of_match', 'gameweek', 'competition',
        'home_team', 'away_team', etc.
        """
        
        # Load historical matches
        historical_df = pd.read_csv(historical_matches_csv_path)
        
        # Get team column names
        home_team_col = 'home_team' if 'home_team' in df.columns else ('home_team_name' if 'home_team_name' in df.columns else 'Home')
        away_team_col = 'away_team' if 'away_team' in df.columns else ('away_team_name' if 'away_team_name' in df.columns else 'Away')
        
        # Get team column names for historical_df (may be different)
        hist_home_col = 'home_team' if 'home_team' in historical_df.columns else ('home_team_name' if 'home_team_name' in historical_df.columns else 'Home')
        hist_away_col = 'away_team' if 'away_team' in historical_df.columns else ('away_team_name' if 'away_team_name' in historical_df.columns else 'Away')
        
        # Identify the competition column
        competition_col = 'competition' if 'competition' in df.columns else 'Competition'
                
        # Ensure historical_df has date column sorted
        if 'date_of_match' in historical_df.columns:
            historical_df['date_of_match'] = pd.to_datetime(historical_df['date_of_match'])
            historical_df = historical_df.sort_values('date_of_match', ascending=False)
        
        # Initialize new columns with None
        df['home_team_rank'] = None
        df['away_team_rank'] = None
        df['home_team_points'] = None
        df['away_team_points'] = None
        df['home_team_goals_for'] = None
        df['away_team_goals_for'] = None
        df['home_team_goals_against'] = None
        df['away_team_goals_against'] = None
        df['home_team_goals_difference'] = None
        df['away_team_goals_difference'] = None
                
        # Iterate over each match
        for idx, match in df.iterrows():
            home_team = match[home_team_col]
            away_team = match[away_team_col]
            
            
            # Filter historical matches by competition if available
            hist_df_filtered = historical_df.copy()
            if competition_col in match.index and competition_col in historical_df.columns:
                competition = match[competition_col]
                hist_df_filtered = hist_df_filtered[hist_df_filtered[competition_col] == competition]
            
            # Find last match for home team
            home_team_matches = hist_df_filtered[
                (hist_df_filtered[hist_home_col] == home_team) | 
                (hist_df_filtered[hist_away_col] == home_team)
            ]
            
            # Find last match for away team
            away_team_matches = hist_df_filtered[
                (hist_df_filtered[hist_home_col] == away_team) | 
                (hist_df_filtered[hist_away_col] == away_team)
            ]
            
            # Extract gameweek column name
            gameweek_col = 'gameweek' if 'gameweek' in historical_df.columns else 'round'
            
            # Get rankings for home team from their last match
            if not home_team_matches.empty:
                last_home_match = home_team_matches.iloc[0]
                home_last_gameweek = last_home_match[gameweek_col]
                
                home_ranking = rankings_df[
                    (rankings_df['gameweek'] == home_last_gameweek) &
                    (rankings_df['team_name'] == home_team)
                ]
                
                if not home_ranking.empty:
                    home_ranking = home_ranking.iloc[0]
                    df.at[idx, 'home_team_rank'] = int(home_ranking['team_rank'])
                    df.at[idx, 'home_team_points'] = int(home_ranking['team_points'])
                    df.at[idx, 'home_team_goals_for'] = int(home_ranking['team_goals_for'])
                    df.at[idx, 'home_team_goals_against'] = int(home_ranking['team_goals_against'])
                    df.at[idx, 'home_team_goals_difference'] = int(home_ranking['team_goals_difference'])
            
            # Get rankings for away team from their last match
            if not away_team_matches.empty:
                last_away_match = away_team_matches.iloc[0]
                away_last_gameweek = last_away_match[gameweek_col]
                
                away_ranking = rankings_df[
                    (rankings_df['gameweek'] == away_last_gameweek) &
                    (rankings_df['team_name'] == away_team)
                ]
                
                if not away_ranking.empty:
                    away_ranking = away_ranking.iloc[0]
                    df.at[idx, 'away_team_rank'] = int(away_ranking['team_rank'])
                    df.at[idx, 'away_team_points'] = int(away_ranking['team_points'])
                    df.at[idx, 'away_team_goals_for'] = int(away_ranking['team_goals_for'])
                    df.at[idx, 'away_team_goals_against'] = int(away_ranking['team_goals_against'])
                    df.at[idx, 'away_team_goals_difference'] = int(away_ranking['team_goals_difference'])
        
        return df
    
    def get_last_match_stats(
        self,
        df_matches: pd.DataFrame,
        past_matches: pd.DataFrame,
        verbose: bool = False
    ) -> pd.DataFrame:
        """
        For each match in df_matches, finds the last match played by each team
        in any non-European competition (league/cup/supercup only).
        
        Uses competition_type column to filter: excludes 'european', includes all others.
        
        Args:
            df_matches: DataFrame with matches to enrich
            past_matches: DataFrame with historical matches (must have competition_type column)
            verbose: Print debugging information
            
        Returns:
            DataFrame with added ranking columns from last match
        """
        
        if df_matches.empty:
            print("[LAST STATS] Empty DataFrame provided, returning as is")
            return df_matches
        
        if verbose:
            print(f"\n[LAST STATS] Getting stats from last matches...")
            print(f"[LAST STATS] Matches to process: {len(df_matches)}")
        
        # Check required columns
        required_cols = ['home_team_name', 'away_team_name', 'date_of_match']
        missing = [col for col in required_cols if col not in df_matches.columns]
        
        if missing:
            print(f"[LAST STATS] ERROR: df_matches missing columns: {missing}")
            raise ValueError(f"df_matches must have columns: {required_cols}")
        
        if 'competition_type' not in past_matches.columns:
            print(f"[LAST STATS] ERROR: past_matches missing 'competition_type' column")
            raise ValueError("past_matches must have 'competition_type' column")
        
        # Columns to extract
        stats_columns = [
            'team_rank',
            'matchs_played',
            'matchs_won',
            'matchs_drawn',
            'matchs_lost',
            'team_goals_for',
            'team_goals_against',
            'team_goals_difference',
            'team_points'
        ]
        
        # Make a copy
        df_result = df_matches.copy()
        
        # Initialize columns
        for prefix in ['home', 'away']:
            for col in stats_columns:
                df_result[f'{prefix}_{col}'] = np.nan
        
        if verbose:
            print(f"[LAST STATS] Filtering past matches (competition_type != 'european')...")
        
        # Filter past matches: exclude European competitions
        past_matches_filtered = past_matches[
            past_matches['competition_type'] != 'european'
        ].copy()
        
        if verbose:
            print(f"[LAST STATS] Historical matches (non-European): {len(past_matches_filtered)}")
            print(f"[LAST STATS] Original historical matches: {len(past_matches)}")
            print(f"[LAST STATS] Excluded European matches: {len(past_matches) - len(past_matches_filtered)}")
        
        if past_matches_filtered.empty:
            print(f"[LAST STATS] WARNING: No non-European matches in history")
            return df_result
        
        # Process each match
        matches_processed = 0
        home_found = 0
        away_found = 0
        
        for idx, row in df_result.iterrows():
            home_team = row['home_team_name']
            away_team = row['away_team_name']
            match_date = row['date_of_match']
            
            # Find last match for home team in any non-European competition
            home_last_match = past_matches_filtered[
                (
                    ((past_matches_filtered['home_team_name'] == home_team) | 
                    (past_matches_filtered['away_team_name'] == home_team))
                ) &
                (past_matches_filtered['date_of_match'] < match_date)
            ].sort_values('date_of_match', ascending=False)
            
            if not home_last_match.empty:
                last_match = home_last_match.iloc[0]
                # Determine if they played as home or away
                if last_match['home_team_name'] == home_team:
                    prefix_source = 'home'
                else:
                    prefix_source = 'away'
                
                # Copy statistics
                for col in stats_columns:
                    source_col = f'{prefix_source}_{col}'
                    if source_col in last_match.index:
                        df_result.at[idx, f'home_{col}'] = last_match[source_col]
                
                home_found += 1
            
            # Find last match for away team in any non-European competition
            away_last_match = past_matches_filtered[
                (
                    ((past_matches_filtered['home_team_name'] == away_team) | 
                    (past_matches_filtered['away_team_name'] == away_team))
                ) &
                (past_matches_filtered['date_of_match'] < match_date)
            ].sort_values('date_of_match', ascending=False)
            
            if not away_last_match.empty:
                last_match = away_last_match.iloc[0]
                # Determine if they played as home or away
                if last_match['home_team_name'] == away_team:
                    prefix_source = 'home'
                else:
                    prefix_source = 'away'
                
                # Copy statistics
                for col in stats_columns:
                    source_col = f'{prefix_source}_{col}'
                    if source_col in last_match.index:
                        df_result.at[idx, f'away_{col}'] = last_match[source_col]
                
                away_found += 1
            
            matches_processed += 1
        
        if verbose:
            print(f"\n[LAST STATS] Processing complete")
            print(f"[LAST STATS] Matches processed: {matches_processed}")
            print(f"[LAST STATS] Home teams with history: {home_found}/{matches_processed}")
            print(f"[LAST STATS] Away teams with history: {away_found}/{matches_processed}")
            
            missing_home = df_result['home_team_rank'].isna().sum()
            missing_away = df_result['away_team_rank'].isna().sum()
            print(f"[LAST STATS] Missing home rankings: {missing_home}/{len(df_result)}")
            print(f"[LAST STATS] Missing away rankings: {missing_away}/{len(df_result)}")
        
        return df_result