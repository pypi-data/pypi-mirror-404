"""
Team Situation Analyzer - Determine Must-Win Situations
========================================================

Analyzes each team's position in the table and determines:
- Current position status (champions zone, europa, relegated, etc.)
- What they're still fighting for (title, europa, survival)
- If the match is a must-win
"""

import pandas as pd
from typing import Dict, Tuple, Optional


class TeamSituationAnalyzer:
    """
    Analyzes team situations based on standings and remaining matches.
    """
    
    def __init__(
        self,
        champions_league_spots: int = 4,
        europa_league_spots: int = 3,
        conference_league_spots: int = 0,
        relegated_spots: int = 3,
        number_of_gameweeks: int = 38
    ):
        """
        Initialize the analyzer with league structure.
        
        Args:
            champions_league_spots: Number of teams that qualify for Champions League
            europa_league_spots: Number of teams that qualify for Europa League
            conference_league_spots: Number of teams that qualify for Conference League
            relegated_spots: Number of teams that get relegated
            number_of_gameweeks: Total number of gameweeks in the season
        """
        self.cl_spots = champions_league_spots
        self.el_spots = europa_league_spots
        self.conf_spots = conference_league_spots
        self.rel_spots = relegated_spots
        self.total_gameweeks = number_of_gameweeks
    
    def analyze_matches(
        self,
        df_matches: pd.DataFrame,
        rankings_csv_path: str
    ) -> pd.DataFrame:
        """
        Analyze each match and add team situation columns.
        
        Args:
            df_matches: DataFrame with matches (must have: home_team, away_team, gameweek)
            rankings_csv_path: Path to rankings CSV
        
        Returns:
            DataFrame with added columns for team situations
        """
        # Load rankings
        rankings_df = pd.read_csv(rankings_csv_path)
        
        # Prepare result DataFrame
        result_df = df_matches.copy()
        
        # Initialize new columns for home team
        home_cols = [
            'home_is_first', 'home_in_champions_zone', 'home_in_europa_zone',
            'home_in_conference_zone', 'home_in_europa', 'home_in_relegated_zone',
            'home_can_win_title', 'home_can_reach_champions', 'home_can_reach_europa',
            'home_can_reach_europe', 'home_can_survive', 'home_must_win'
        ]
        
        # Initialize new columns for away team
        away_cols = [
            'away_is_first', 'away_in_champions_zone', 'away_in_europa_zone',
            'away_in_conference_zone', 'away_in_europa', 'away_in_relegated_zone',
            'away_can_win_title', 'away_can_reach_champions', 'away_can_reach_europa',
            'away_can_reach_europe', 'away_can_survive', 'away_must_win'
        ]
        
        for col in home_cols + away_cols:
            result_df[col] = 0
        
        # Process each match
        for idx, match in result_df.iterrows():
            home_team = match['home_team']
            away_team = match['away_team']
            current_gameweek = match['gameweek']
            
            # Get previous gameweek standings
            previous_gameweek = current_gameweek - 1
            
            if previous_gameweek < 1:
                # First gameweek - no previous standings
                continue
            
            # Filter rankings for previous gameweek
            prev_rankings = rankings_df[
                rankings_df['gameweek'] == previous_gameweek
            ].copy()
            
            if prev_rankings.empty:
                continue
            
            # Sort by rank to ensure correct order
            prev_rankings = prev_rankings.sort_values('rank').reset_index(drop=True)
            
            # Analyze home team
            home_situation = self._analyze_team_situation(
                team_name=home_team,
                rankings=prev_rankings,
                current_gameweek=current_gameweek
            )
            
            # Analyze away team
            away_situation = self._analyze_team_situation(
                team_name=away_team,
                rankings=prev_rankings,
                current_gameweek=current_gameweek
            )
            
            # Set home team columns
            if home_situation:
                result_df.at[idx, 'home_is_first'] = home_situation['is_first']
                result_df.at[idx, 'home_in_champions_zone'] = home_situation['in_champions_zone']
                result_df.at[idx, 'home_in_europa_zone'] = home_situation['in_europa_zone']
                result_df.at[idx, 'home_in_conference_zone'] = home_situation['in_conference_zone']
                result_df.at[idx, 'home_in_europa'] = home_situation['in_europa']
                result_df.at[idx, 'home_in_relegated_zone'] = home_situation['in_relegated_zone']
                result_df.at[idx, 'home_can_win_title'] = home_situation['can_win_title']
                result_df.at[idx, 'home_can_reach_champions'] = home_situation['can_reach_champions']
                result_df.at[idx, 'home_can_reach_europa'] = home_situation['can_reach_europa']
                result_df.at[idx, 'home_can_reach_europe'] = home_situation['can_reach_europe']
                result_df.at[idx, 'home_can_survive'] = home_situation['can_survive']
                result_df.at[idx, 'home_must_win'] = home_situation['must_win']
            
            # Set away team columns
            if away_situation:
                result_df.at[idx, 'away_is_first'] = away_situation['is_first']
                result_df.at[idx, 'away_in_champions_zone'] = away_situation['in_champions_zone']
                result_df.at[idx, 'away_in_europa_zone'] = away_situation['in_europa_zone']
                result_df.at[idx, 'away_in_conference_zone'] = away_situation['in_conference_zone']
                result_df.at[idx, 'away_in_europa'] = away_situation['in_europa']
                result_df.at[idx, 'away_in_relegated_zone'] = away_situation['in_relegated_zone']
                result_df.at[idx, 'away_can_win_title'] = away_situation['can_win_title']
                result_df.at[idx, 'away_can_reach_champions'] = away_situation['can_reach_champions']
                result_df.at[idx, 'away_can_reach_europa'] = away_situation['can_reach_europa']
                result_df.at[idx, 'away_can_reach_europe'] = away_situation['can_reach_europe']
                result_df.at[idx, 'away_can_survive'] = away_situation['can_survive']
                result_df.at[idx, 'away_must_win'] = away_situation['must_win']
        
        return result_df
    
    def _analyze_team_situation(
        self,
        team_name: str,
        rankings: pd.DataFrame,
        current_gameweek: int
    ) -> Optional[Dict]:
        """
        Analyze a single team's situation in the standings.
        
        Args:
            team_name: Name of the team
            rankings: Rankings DataFrame for the previous gameweek
            current_gameweek: Current gameweek number
        
        Returns:
            Dictionary with team situation analysis or None if team not found
        """
        # Find team in rankings
        team_row = rankings[rankings['team_name'] == team_name]
        
        if team_row.empty:
            return None
        
        team_data = team_row.iloc[0]
        team_rank = int(team_data['rank'])
        team_points = int(team_data['points'])
        
        # Calculate remaining gameweeks and maximum points
        gameweeks_played = current_gameweek - 1  # Previous gameweek
        remaining_gameweeks = self.total_gameweeks - gameweeks_played
        max_points_remaining = remaining_gameweeks * 3
        max_possible_points = team_points + max_points_remaining
        
        # Determine current position status
        is_first = (team_rank == 1)
        in_champions_zone = (team_rank <= self.cl_spots)
        in_europa_zone = (
            team_rank > self.cl_spots and 
            team_rank <= self.cl_spots + self.el_spots
        )
        in_conference_zone = (
            team_rank > self.cl_spots + self.el_spots and
            team_rank <= self.cl_spots + self.el_spots + self.conf_spots
        )
        in_europa = in_champions_zone or in_europa_zone or in_conference_zone
        
        total_teams = len(rankings)
        in_relegated_zone = (team_rank > total_teams - self.rel_spots)
        
        # Get key positions from rankings
        first_place_points = int(rankings.iloc[0]['points'])
        
        # Last Champions League spot
        last_cl_points = int(rankings.iloc[min(self.cl_spots - 1, len(rankings) - 1)]['points'])
        
        # Last Europa League spot
        last_el_idx = min(self.cl_spots + self.el_spots - 1, len(rankings) - 1)
        last_el_points = int(rankings.iloc[last_el_idx]['points'])
        
        # Last European spot (including Conference)
        last_europe_idx = min(
            self.cl_spots + self.el_spots + self.conf_spots - 1,
            len(rankings) - 1
        )
        last_europe_points = int(rankings.iloc[last_europe_idx]['points']) if last_europe_idx >= 0 else 0
        
        # First relegated spot
        first_rel_idx = max(total_teams - self.rel_spots, 0)
        first_relegated_points = int(rankings.iloc[first_rel_idx]['points'])
        
        # Determine what team can still achieve
        can_win_title = max_possible_points >= first_place_points
        can_reach_champions = max_possible_points >= last_cl_points if self.cl_spots > 0 else False
        can_reach_europa = max_possible_points >= last_el_points if self.el_spots > 0 else False
        can_reach_europe = max_possible_points >= last_europe_points if (self.cl_spots + self.el_spots + self.conf_spots) > 0 else False
        can_survive = max_possible_points > first_relegated_points
        
        # Determine if this is a must-win situation
        must_win = self._determine_must_win(
            team_rank=team_rank,
            team_points=team_points,
            max_possible_points=max_possible_points,
            in_champions_zone=in_champions_zone,
            in_europa_zone=in_europa_zone,
            in_europa=in_europa,
            in_relegated_zone=in_relegated_zone,
            can_win_title=can_win_title,
            can_reach_champions=can_reach_champions,
            can_reach_europa=can_reach_europa,
            can_reach_europe=can_reach_europe,
            can_survive=can_survive,
            first_place_points=first_place_points,
            last_cl_points=last_cl_points,
            last_el_points=last_el_points,
            last_europe_points=last_europe_points,
            first_relegated_points=first_relegated_points,
            remaining_gameweeks=remaining_gameweeks
        )
        
        return {
            'is_first': int(is_first),
            'in_champions_zone': int(in_champions_zone),
            'in_europa_zone': int(in_europa_zone),
            'in_conference_zone': int(in_conference_zone),
            'in_europa': int(in_europa),
            'in_relegated_zone': int(in_relegated_zone),
            'can_win_title': int(can_win_title),
            'can_reach_champions': int(can_reach_champions),
            'can_reach_europa': int(can_reach_europa),
            'can_reach_europe': int(can_reach_europe),
            'can_survive': int(can_survive),
            'must_win': int(must_win)
        }
    
    def _determine_must_win(
        self,
        team_rank: int,
        team_points: int,
        max_possible_points: int,
        in_champions_zone: bool,
        in_europa_zone: bool,
        in_europa: bool,
        in_relegated_zone: bool,
        can_win_title: bool,
        can_reach_champions: bool,
        can_reach_europa: bool,
        can_reach_europe: bool,
        can_survive: bool,
        first_place_points: int,
        last_cl_points: int,
        last_el_points: int,
        last_europe_points: int,
        first_relegated_points: int,
        remaining_gameweeks: int
    ) -> bool:
        """
        Determine if this is a must-win match based on team's situation.
        
        A match is considered "must-win" if:
        - Team is in relegation zone but can still survive
        - Team is close to European spots and can still reach them
        - Team is in title race and every point matters
        - Team is just outside Champions/Europa but within reach
        """
        # If late in the season (last 10 games), pressure increases
        late_season = remaining_gameweeks <= 10
        very_late_season = remaining_gameweeks <= 5
        
        # Calculate point gaps
        gap_to_first = first_place_points - team_points
        gap_to_safety = team_points - first_relegated_points
        
        # 1. RELEGATION BATTLE - Must win if in danger
        if in_relegated_zone and can_survive:
            # In relegation zone but can still escape
            if very_late_season:
                return True
            if gap_to_safety <= 3:  # Within 3 points of safety
                return True
        
        if not in_relegated_zone and gap_to_safety <= 6 and late_season:
            # Just above relegation zone in late season
            return True
        
        # 2. EUROPEAN RACE - Must win if close to qualification
        if not in_europa and can_reach_europe:
            gap_to_europe = last_europe_points - team_points
            if gap_to_europe <= 3 and late_season:
                # Within 3 points of Europe in late season
                return True
            if gap_to_europe <= 6 and very_late_season:
                # Within 6 points in very late season
                return True
        
        # 3. CHAMPIONS LEAGUE RACE
        if not in_champions_zone and can_reach_champions:
            gap_to_cl = last_cl_points - team_points
            if in_europa_zone and gap_to_cl <= 3:
                # In Europa zone, close to Champions
                return True
            if gap_to_cl <= 3 and late_season:
                return True
        
        # 4. TITLE RACE - Must win if close to first
        if can_win_title and gap_to_first <= 6:
            if very_late_season and gap_to_first <= 9:
                # Very late season, within 9 points
                return True
            if late_season and gap_to_first <= 6:
                # Late season, within 6 points
                return True
            if gap_to_first <= 3:
                # Always must-win if within 3 points of first
                return True
        
        # 5. PROTECTING POSITION
        if in_champions_zone and late_season:
            # In Champions zone in late season - must protect position
            if team_rank == self.cl_spots:
                # On the edge of CL qualification
                return True
        
        if in_europa_zone and very_late_season:
            # In Europa zone in very late season
            return True
        
        return False