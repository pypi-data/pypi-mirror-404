from functools import lru_cache
from typing import Dict, Type


class Settings:
    """Central project configuration (pure data, no logic)."""

    # --- Max values for cyclic (circular) features ---
    circular_max_values: Dict[str, int] = {
        "hour_of_day": 24,
        "day_of_week": 7,
        "gameweek": 38,
        "day_of_year": 365,
    }

    # CSV paths
    paths: Dict[str, str] = {
        "matches": "app/data/raw/matches/matches.csv",
        "players": "app/data/raw/players/players.csv",
        "keepers": "app/data/raw/players/keepers.csv",
        "ranking": "app/data/raw/rankings/{country}/{last_season[0]}/rankings_{competition}_{last_season[0]}.csv",
        "dataset": "app/data/features/dataset.csv",
        "teams": "app/data/raw/teams/teams.csv",
        "stadiums": "app/data/raw/teams/stadiums.csv"
    }

    # Random state
    random_state: int = 42

    # Centralized feature configuration
    update_features_config: Dict[str, Dict[str, Type]] = {
        # Base categorical columns (no processing needed)
        "fbref_informations": {
            "gameweek": int,
            "date_of_match": str,
            "hour_of_the_match": str,
            "day_of_week": int,
            "day_of_year": int,
            "hour_of_day": float,
            "home_team_name": str,
            "away_team_name": str,
            "home_trainer": str,
            "away_trainer": str,
            "stadium": str,
            "home_attendance": int,
            "referee": str,
            "var": str,
            "home_team_formation": str,
            "away_team_formation": str,
            "home_possession": float,
            "away_possession": float,
            "home_goals": int,
            "away_goals": int,
            "home_result": float,
        },
        # Creation features
        "fbref_work_features": {
            "away_attendance": int,
            "away_result": str,
            "competition_name": str,
            "competition_type": str,
            "competition_country": str,
            "altitude": float,
            "longitude": float,
            "latitude": float,
            "home_team_country": str,
            "away_team_country": str,
        },
        # Ranking 
        "ranking_informations": {
            "home_team_rank": int,
            "away_team_rank": int,
            "home_team_points": int,
            "away_team_points": int,
            "home_team_goals_for": int,
            "away_team_goals_for": int,
            "home_team_goals_against": int,
            "away_team_goals_against": int,
            "home_team_goals_difference": int,
            "away_team_goals_difference": int,
        },
        # Teams
        "teams_informations": {
            "first_place_league": int,
            "second_place_league": int,
            "years_total_league": int,
            "years_consecutive_league": int,
            "first_place_cup": int,
            "second_place_cup": int,
            "first_place_supercup": int,
            "second_place_supercup": int,
            "first_place_europe_1": int,
            "second_place_europe_1": int,
            "first_place_europe_2": int,
            "second_place_europe_2": int,
            "first_place_europe_3": int,
            "second_place_europe_3": int,
            "first_place_europe_supercup": int,
            "second_place_europe_supercup": int,
            "years_total_europe": int,
            "years_consecutive_europe": int,
        },
    }
    
    # Centralized feature configuration
    predicting_features_config: Dict[str, any] = {
        # Base categorical columns (no processing needed)
        "fbref_informations": {
            "gameweek": int,
            "date_of_match": str,
            "hour_of_the_match": str,
            "day_of_week": int,
            "day_of_year": int,
            "hour_of_day": float,
            "home_team_name": str,
            "away_team_name": str,
            "home_trainer": str,
            "away_trainer": str,
            "stadium": str,
            "referee": str,
            "var": str,
        },
        # Creation features
        "fbref_work_features": {
            "competition_name": str,
            "competition_type": str,
            "competition_country": str,
            "altitude": float,
            "longitude": float,
            "latitude": float,
            "home_team_country": str,
            "away_team_country": str,
            "home_team_rest_time": float,
            "away_team_rest_time": float,
            "home_team_distance": float, 
            "away_team_distance": float, 
            "home_team_accumulated_distance": float,
            "away_team_accumulated_distance": float,
            "home_team_accumulated_matches": float,
            "away_team_accumulated_matches": float
        },
        # Ranking 
        "ranking_informations": {
            "home_team_rank": int,
            "away_team_rank": int,
            "home_team_points": int,
            "away_team_points": int,
            "home_team_goals_for": int,
            "away_team_goals_for": int,
            "home_team_goals_against": int,
            "away_team_goals_against": int,
            "home_team_goals_difference": int,
            "away_team_goals_difference": int,
        },
        "teams_informations": {
            "first_place_league": int,
            "second_place_league": int,
            "years_total_league": int,
            "years_consecutive_league": int,
            "first_place_cup": int,
            "second_place_cup": int,
            "first_place_supercup": int,
            "second_place_supercup": int,
            "first_place_europe_1": int,
            "second_place_europe_1": int,
            "first_place_europe_2": int,
            "second_place_europe_2": int,
            "first_place_europe_3": int,
            "second_place_europe_3": int,
            "first_place_europe_supercup": int,
            "second_place_europe_supercup": int,
            "years_total_europe": int,
            "years_consecutive_europe": int,
        },
        # Features with binning configuration: thresholds + operators
        "fbref_features": {
            "result": {
                "thresholds": [2, 1, 0, 0, 2],
                "operators": ["eq", "eq", "eq", "gt", "lt"],
            },
            "attendance": {
                "thresholds": [20000, 50000, 50000, 70000],
                "operators": ["lt", "lt", "gt", "gt"],
            },
            "goals_0_15": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "goals_15_30": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "goals_30_45": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "goals_45_60": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "goals_60_75": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "goals_75_90": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "yellow_cards_0_15": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "yellow_cards_15_30": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "yellow_cards_30_45": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "yellow_cards_45_60": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "yellow_cards_60_75": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "yellow_cards_75_90": {
                "thresholds": [0, 1, 2, 2],
                "operators": ["eq", "eq", "eq", "gt"],
            },
            "red_cards_0_15": {
                "thresholds": [0, 1, 1],
                "operators": ["eq", "eq", "gt"],
            },
            "red_cards_15_30": {
                "thresholds": [0, 1, 1],
                "operators": ["eq", "eq", "gt"],
            },
            "red_cards_30_45": {
                "thresholds": [0, 1, 1],
                "operators": ["eq", "eq", "gt"],
            },
            "red_cards_45_60": {
                "thresholds": [0, 1, 1],
                "operators": ["eq", "eq", "gt"],
            },
            "red_cards_60_75": {
                "thresholds": [0, 1, 1],
                "operators": ["eq", "eq", "gt"],
            },
            "red_cards_75_90": {
                "thresholds": [0, 1, 1],
                "operators": ["eq", "eq", "gt"],
            },
            "possession": {
                "thresholds": [20, 30, 40, 50, 60, 70, 80],
                "operators": ["le", "le", "le", "ge", "ge", "ge", "ge"],
            },
            "goals": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersAge": {
                "thresholds": [23.0, 27.0, 30.0, 30.0],
                "operators": ["le", "le", "le", "gt"],
            },
            "PlayersAvgMinutes": {
                "thresholds": [70.0, 70.0, 80.0, 80.0],
                "operators": ["le", "gt", "le", "gt"],
            },
            "PlayersShots": {
                "thresholds": [ 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
                "operators": [ "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "ge",],
            },
            "PlayersShotsOnTarget": {
                "thresholds": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "operators": [ "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "eq", "ge",],
            },
            "PlayersCompletedPasses": {
                "thresholds": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
                "operators": ["le", "le", "le", "ge", "ge", "ge"],
            },
            "PlayersAttemptedPasses": {
                "thresholds": [200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0],
                "operators": ["le", "le", "le", "le", "le", "le", "ge"],
            },
            "Players%CompletedPasses": {
                "thresholds": [40.0, 50.0, 60.0, 70.0, 80.0, 90.0],
                "operators": ["le", "le", "ge", "ge", "ge", "ge"],
            },
            "PlayersDistancePasses": {
                "thresholds": [50, 100, 150, 200, 250, 300],
                "operators": ["le", "le", "le", "ge", "ge", "ge"],
            },
            "PlayersDistanceProgression": {
                "thresholds": [20, 40, 60, 80, 100, 120],
                "operators": ["le", "le", "le", "ge", "ge", "ge"],
            },
            "PlayersShortPasses": {
                "thresholds": [50, 100, 150, 200, 250],
                "operators": ["le", "le", "le", "ge", "ge"],
            },
            "PlayersAttemptedShortPasses": {
                "thresholds": [60, 120, 180, 240, 300],
                "operators": ["le", "le", "le", "ge", "ge"],
            },
            "Players%ShortCompletedPasses": {
                "thresholds": [60, 70, 80, 90],
                "operators": ["le", "le", "ge", "ge"],
            },
            "PlayersMediumPasses": {
                "thresholds": [30, 60, 90, 120, 150],
                "operators": ["le", "le", "le", "ge", "ge"],
            },
            "PlayersAttemptedMediumPasses": {
                "thresholds": [40, 80, 120, 160, 200],
                "operators": ["le", "le", "le", "ge", "ge"],
            },
            "Players%MediumCompletedPasses": {
                "thresholds": [60, 70, 80, 90],
                "operators": ["le", "le", "ge", "ge"],
            },
            "PlayersLongPasses": {
                "thresholds": [10, 20, 30, 40, 50],
                "operators": ["le", "le", "le", "ge", "ge"],
            },
            "PlayersAttemptedLongPasses": {
                "thresholds": [15, 30, 45, 60, 75],
                "operators": ["le", "le", "le", "ge", "ge"],
            },
            "Players%LongCompletedPasses": {
                "thresholds": [40, 50, 60, 70],
                "operators": ["le", "le", "ge", "ge"],
            },
            "PlayersAssistance": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge",],
            },
            "PlayersExpectedGoalsAssistance": {
                "thresholds": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                "operators": [ "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge", "ge",],
            },
            "PlayersExpectedAssistance": {
                "thresholds": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                "operators": [ "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge", "ge",],
            },
            "PlayersKeyPasses": {
                "thresholds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersLast1/3Passes": {
                "thresholds": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                "operators": [ "le", "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersGoalAreaPasses": {
                "thresholds": [1, 3, 5, 7, 9, 11, 13, 15, 17, 19],
                "operators": [ "le", "le", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersGoalAreaCrosses": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersGoalPasses": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersLiveBallPasses": {
                "thresholds": [20, 40, 60, 80, 100, 120, 140, 160, 180, 200],
                "operators": [ "le", "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersDeadBallPasses": {
                "thresholds": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                "operators": [ "le", "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersFreeKick": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersThroughPasses": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersSidePasses": {
                "thresholds": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                "operators": [ "le", "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersCrosses": {
                "thresholds": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                "operators": [ "le", "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersStrongcrosses": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersCorner": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersCornerIn": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersCornerOut": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersCornerRect": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersOffsidePasses": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersPassesBlocked": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersTackles": {
                "thresholds": [5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                "operators": [ "le", "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersSuccessfulTackles": {
                "thresholds": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersTacklesInDefense": {
                "thresholds": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersTacklesInMedium": {
                "thresholds": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersTacklesInAttack": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersDribblerTackles": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersAttemptedDribblerTackles": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "Players%DribblerTacklesCompleted": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                "operators": [ "le", "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersDribblerTacklesNonCompleted": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersBallsBlocked": {
                "thresholds": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersShotsBlocked": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersInterceptions": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersTackles+Interceptions": {
                "thresholds": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersClearances": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersMistakesRivalShots": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersTouches": {
                "thresholds": [20, 30, 40, 50, 60, 70, 80, 90, 100],
                "operators": ["le", "le", "le", "le", "le", "ge", "ge", "ge", "ge"],
            },
            "PlayersOwnPenaltyAreaTouches": {
                "thresholds": [0, 2, 4, 6, 8, 10],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersTouchesInDefense": {
                "thresholds": [0, 5, 10, 15, 20, 25],
                "operators": ["le", "le", "le", "le", "le", "ge"],
            },
            "PlayersTouchesInMedium": {
                "thresholds": [0, 5, 10, 15, 20, 25],
                "operators": ["le", "le", "le", "le", "le", "ge"],
            },
            "PlayersTouchesInAttack": {
                "thresholds": [0, 5, 10, 15, 20, 25],
                "operators": ["le", "le", "le", "le", "le", "ge"],
            },
            "PlayersAwayPenaltyAreaTouches": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersLiveBallTouches": {
                "thresholds": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                "operators": [ "le", "le", "le", "le", "le", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersAttemptedDribbles": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersDribblesCompleted": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "Players%DribblesCompleted": {
                "thresholds": [0, 20, 40, 60, 80, 100],
                "operators": ["le", "le", "le", "le", "le", "ge"],
            },
            "PlayersBallCarries": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60, 70],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersDistanceCarried": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersForwardDistanceCarried": {
                "thresholds": [0, 5, 10, 15, 20, 25],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersForwardCarries": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersCarriesInAttack": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersAwayPenaltyAreaCarries": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersLostControlCarries": {
                "thresholds": [0, 1, 2, 3, 4, 5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersLostCarries": {
                "thresholds": [0, 1, 2, 3, 4, 5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersPassesReception": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60, 70],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersAttackPassesReception": {
                "thresholds": [0, 5, 10, 15, 20],
                "operators": ["eq", "ge", "ge", "ge", "ge"],
            },
            "PlayersYellowCards": {
                "thresholds": [0, 1, 2, 3, 4],
                "operators": ["eq", "ge", "ge", "ge", "ge"],
            },
            "PlayersRedCards": {
                "thresholds": [0, 1, 2, 3],
                "operators": ["eq", "ge", "ge", "ge"],
            },
            "PlayersSecondYellowCards": {
                "thresholds": [0, 1, 2],
                "operators": ["eq", "ge", "ge"],
            },
            "PlayersFouls": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersFoulsReceived": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
                "operators": [ "eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersPenalties": {
                "thresholds": [0, 1, 2, 3],
                "operators": ["eq", "ge", "ge", "ge"],
            },
            "PlayersPenaltiesConceded": {
                "thresholds": [0, 1, 2, 3],
                "operators": ["eq", "ge", "ge", "ge"],
            },
            "PlayersLostBallRecoveries": {
                "thresholds": [0, 10, 20, 30, 40, 50],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersAerialsWon": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60, 70],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "PlayersAerialsLost": {
                "thresholds": [0, 10, 20, 30, 40, 50],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "Players%AerialsWon": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersShotsOnTargetAgainst": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersGoalsAgainst": {
                "thresholds": [0, 1, 2, 3, 4, 5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersSaved": {
                "thresholds": [0, 1, 2, 3, 4, 5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "Keepers%Saved": {
                "thresholds": [0, 10, 20, 30, 40, 50, 60],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersxG": {
                "thresholds": [0, 0.1, 0.2, 0.3, 0.4, 0.5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersPassesLaunched": {
                "thresholds": [0, 1, 2, 3, 4, 5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersAttemptedPassesLaunched": {
                "thresholds": [0, 1, 2, 3, 4, 5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "Keepers%CompletedPassesLaunched": {
                "thresholds": [0, 20, 40, 60, 80, 100],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersPasses": {
                "thresholds": [0, 1, 2, 3, 4, 5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersAttemptedPasses": {
                "thresholds": [0, 1, 2, 3, 4, 5],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "Keepers%CompletedPasses": {
                "thresholds": [0, 20, 40, 60, 80, 100],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersPassesDistance": {
                "thresholds": [0, 10, 20, 30, 40, 50],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersAttemptedKicks": {
                "thresholds": [0, 1, 2, 3, 4],
                "operators": ["eq", "ge", "ge", "ge", "ge"],
            },
            "Keepers%Kicks": {
                "thresholds": [0, 20, 40, 60, 80, 100],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersKicksDistance": {
                "thresholds": [0, 10, 20, 30, 40, 50],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersCrosses": {
                "thresholds": [0, 1, 2, 3, 4],
                "operators": ["eq", "ge", "ge", "ge", "ge"],
            },
            "KeepersCrossesStopped": {
                "thresholds": [0, 1, 2, 3, 4],
                "operators": ["eq", "ge", "ge", "ge", "ge"],
            },
            "Keepers%CrossesStopped": {
                "thresholds": [0, 20, 40, 60, 80, 100],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "KeepersActionsOutsideArea": {
                "thresholds": [0, 1, 2, 3, 4],
                "operators": ["eq", "ge", "ge", "ge", "ge"],
            },
            "KeepersDistanceActionsArea": {
                "thresholds": [0, 10, 20, 30, 40, 50],
                "operators": ["eq", "ge", "ge", "ge", "ge", "ge"],
            },
            "unavailable_count": {
                "thresholds": [0, 1, 2, 3, 4, 5, 6, 7],
                "operators": ["eq", "eq", "eq", "eq", "eq", "eq", "eq", "ge"],
            }
        },
    }

    # Centralized feature configuration
    modeling_features_config: Dict[str, any] = {
        # Supervised target column
        "target": "home_result",
    }

    # Competition configuration
    competitions_config: Dict[str, Dict] = {
        # ==================== SPANISH COMPETITIONS ====================
        "liga": {
            "country": "spain",
            "number_of_gameweeks": 38,
            "champions_league": 4,
            "europa_league": 3,
            "conference_league": 0,
            "relegated_teams": 3,
            "suspensions": {
                "yellow_cards_suspensions": {
                    "type": "cycle",
                    "ban_matches": 1,
                    "cards_per_suspension": 5,
                    "cycle_resets_after_serving_ban": True,
                },
                "red_card_ban_matches": 1
            },
            "information_scraping_urls": {
                "matches": "https://fbref.com/es/comps/12/{last_season[0]}/schedule/{last_season[0]}-La-Liga-Scores-and-Fixtures",
                "ranking": "https://fbref.com/en/comps/12/{last_season[0]}/{last_season[0]}-La-Liga-Stats",
                "fotmob": "https://www.fotmob.com/en/leagues/87/fixtures/laliga?season={last_season[0]}&group=by-date&page={page}",
                "summer_transfers": "https://www.transfermarkt.co.uk/laliga/transfers/wettbewerb/ES1/plus/?saison_id={last_season[0]}&s_w=s&leihe=1&intern=0",
                "winter_transfers": "https://www.transfermarkt.co.uk/laliga/transfers/wettbewerb/ES1/plus/?saison_id={last_season[0]}&s_w=w&leihe=1&intern=0"
            },
            "betting_scraping_urls": {
                "betclic": "https://www.betclic.fr/football-sfootball/espagne-laliga-c7",
                "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/32/36",
                "unibet": "https://www.unibet.fr/sport/football/espagne/laliga?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
                "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/espagne/laliga",
                "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B486%5D",
                "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/espagne-28/laliga-102829",
                "netbet": "https://www.netbet.fr/football/espagne/laliga",
                "betsson": "https://betsson.fr/fr/competitions/football/laliga?competition_id=55775.1",
            },
        },
        # ==================== ENGLISH COMPETITIONS ====================
        "premier_league": {
            "country": "england",
            "number_of_gameweeks": 38,
            "champions_league": 4,
            "europa_league": 3,
            "conference_league": 0,
            "relegated_teams": 3,
            "suspensions": {
                "yellow_cards_suspensions": {
                    "type": "milestones",
                    "milestones": [
                        {"cards": 5, "ban_matches": 1, "cutoff_league_fixtures": 19},
                        {"cards": 10, "ban_matches": 2, "cutoff_league_fixtures": 32},
                        {"cards": 15, "ban_matches": 3, "cutoff_league_fixtures": "end_of_season"},
                    ],
                    "cycle_resets_after_serving_ban": False,
                },
                "red_card_ban_matches": 1
            },
            "information_scraping_urls": {
                "matches": "https://fbref.com/en/comps/9/{last_season[0]}/schedule/{last_season[0]}-Premier-League-Scores-and-Fixtures",
                "ranking": "https://fbref.com/es/comps/9/{last_season[0]}/{last_season[0]}-Premier-League-Stats",
                "fotmob": "https://www.fotmob.com/en/leagues/47/fixtures/premier-league?group=by-date&season={last_season[0]}&group=by-date&page={page}",
                "summer_transfers": "https://www.transfermarkt.co.uk/premier-league/transfers/wettbewerb/GB1/plus/?saison_id={last_season[0]}&s_w=s&leihe=1&intern=0",
                "winter_transfers": "https://www.transfermarkt.co.uk/premier-league/transfers/wettbewerb/GB1/plus/?saison_id={last_season[0]}&s_w=w&leihe=1&intern=0"
            },
            "betting_scraping_urls": {
                "betclic": "https://www.betclic.fr/football-sfootball/angl-premier-league-c3",
                "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/1/1",
                "unibet": "https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
                "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/angleterre/premier-league",
                "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B261%5D&boost=%5B%5D",
                "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-102841",
                "netbet": "https://www.netbet.fr/football/angleterre/premier-league",
                "betsson": "https://betsson.fr/fr/competitions/football/premier-league?competition_id=55768.1",
            },
        },
        # ==================== ITALIAN COMPETITIONS ====================
        "serie_a": {
            "country": "italy",
            "number_of_gameweeks": 38,
            "champions_league": 4,
            "europa_league": 3,
            "conference_league": 0,
            "relegated_teams": 3,
            "suspensions": {
                "yellow_cards_suspensions": {
                    "type": "milestones",
                        "ban_matches": 1,
                        "milestones_cards": [5, 10, 14, 17, 19],
                        "after_last_milestone": {"repeat_every_cards": 1, "starting_after_cards": 19},
                        "cycle_resets_after_serving_ban": False,
                },
                "red_card_ban_matches": 1
            },
            "information_scraping_urls": {
                "matches": "https://fbref.com/en/comps/11/{last_season[0]}/schedule/{last_season[0]}-Serie-A-Scores-and-Fixtures",
                "ranking": "https://fbref.com/es/comps/11/{last_season[0]}/{last_season[0]}-Serie-A-Stats",
                "fotmob": "https://www.fotmob.com/leagues/55/fixtures/serie?group=by-date&season={last_season[0]}&group=by-date&page={page}",
                "summer_transfers": "https://www.transfermarkt.co.uk/serie-a/transfers/wettbewerb/IT1/plus/?saison_id={last_season[0]}&s_w=s&leihe=1&intern=0",
                "winter_transfers": "https://www.transfermarkt.co.uk/serie-a/transfers/wettbewerb/IT1/plus/?saison_id={last_season[0]}&s_w=w&leihe=1&intern=0"
            },
            "betting_scraping_urls": {
                "betclic": "https://www.betclic.fr/football-sfootball/angl-premier-league-c3", # Cambiar
                "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/1/1",
                "unibet": "https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
                "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/angleterre/premier-league",
                "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B261%5D&boost=%5B%5D",
                "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-102841",
                "netbet": "https://www.netbet.fr/football/angleterre/premier-league",
                "betsson": "https://betsson.fr/fr/competitions/football/premier-league?competition_id=55768.1",
            },
        },
        # ==================== FRENCH COMPETITIONS ====================
        "ligue_1": {
            "country": "france",
            "number_of_gameweeks": 38,
            "champions_league": 3,
            "europa_league": 3,
            "conference_league": 0,
            "relegated_teams": 3,
            "suspensions": {
                "yellow_cards_suspensions": {
                    "type": "cycle",
                    "ban_matches": 1,
                    "cards_per_suspension": 5,
                    "cycle_resets_after_serving_ban": True,
                },
                "red_card_ban_matches": 1
            },
            "information_scraping_urls": {
                "matches": "https://fbref.com/en/comps/13/{last_season[0]}/schedule/{last_season[0]}-Ligue-1-Scores-and-Fixtures",
                "ranking": "https://fbref.com/es/comps/13/{last_season[0]}/{last_season[0]}-Ligue-1-Stats",
                "fotmob": "https://www.fotmob.com/leagues/53/fixtures/ligue-1?group=by-date&season={last_season[0]}&group=by-date&page={page}",
                "summer_transfers": "https://www.transfermarkt.co.uk/ligue-1/transfers/wettbewerb/FR1/plus/?saison_id={last_season[0]}&s_w=s&leihe=1&intern=0",
                "winter_transfers": "https://www.transfermarkt.co.uk/ligue-1/transfers/wettbewerb/FR1/plus/?saison_id={last_season[0]}&s_w=w&leihe=1&intern=0"
            },
            "betting_scraping_urls": {
                "betclic": "https://www.betclic.fr/football-sfootball/angl-premier-league-c3", # Cambiar
                "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/1/1",
                "unibet": "https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
                "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/angleterre/premier-league",
                "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B261%5D&boost=%5B%5D",
                "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-102841",
                "netbet": "https://www.netbet.fr/football/angleterre/premier-league",
                "betsson": "https://betsson.fr/fr/competitions/football/premier-league?competition_id=55768.1",
            },
        },
        # ==================== GERMAN COMPETITIONS ====================
        "bundesliga": {
            "country": "germany",
            "number_of_gameweeks": 34,
            "champions_league": 4,
            "europa_league": 3,
            "conference_league": 0,
            "relegated_teams": 3,
            "suspensions": {
                "yellow_cards_suspensions": {
                    "type": "cycle",
                    "ban_matches": 1,
                    "cards_per_suspension": 5,
                    "cycle_resets_after_serving_ban": True,
                },
                "red_card_ban_matches": 1
            },
            "information_scraping_urls": {
                "matches": "https://fbref.com/en/comps/20/{last_season[0]}/schedule/{last_season[0]}-Bundesliga-Scores-and-Fixtures",
                "ranking": "https://fbref.com/es/comps/20/{last_season[0]}/{last_season[0]}-Bundesliga-Stats",
                "fotmob": "https://www.fotmob.com/leagues/54/fixtures/bundesliga?group=by-date&season={last_season[0]}&group=by-date&page={page}",
                "summer_transfers": "https://www.transfermarkt.co.uk/bundesliga/transfers/wettbewerb/L1/plus/?saison_id={last_season[0]}&s_w=s&leihe=1&intern=0",
                "winter_transfers": "https://www.transfermarkt.co.uk/bundesliga/transfers/wettbewerb/L1/plus/?saison_id={last_season[0]}&s_w=w&leihe=1&intern=0"
            },
            "betting_scraping_urls": {
                "betclic": "https://www.betclic.fr/football-sfootball/angl-premier-league-c3", # Cambiar
                "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/1/1",
                "unibet": "https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
                "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/angleterre/premier-league",
                "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B261%5D&boost=%5B%5D",
                "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-102841",
                "netbet": "https://www.netbet.fr/football/angleterre/premier-league",
                "betsson": "https://betsson.fr/fr/competitions/football/premier-league?competition_id=55768.1",
            },
        },
        # ==================== PORTUGESH COMPETITIONS ====================
        # "primeira_liga": {
        #     "country": "portugal",
        #     "number_of_gameweeks": 34,
        #     "champions_league": 2,
        #    "europa_league": 3,
        #    "conference_league": 0,
        #    "relegated_teams": 3,
        #    "suspensions": {
            #     "yellow_cards_suspensions": {
            #         "type": "milestones",
            #        "ban_matches": 1,
            #        "milestones_cards": [5, 9, 12, 14],  # then every +2 cards after 14th
            #        "after_last_milestone": {"repeat_every_cards": 2, "starting_after_cards": 14},
            #        "cycle_resets_after_serving_ban": False,
            #    },
        #        "red_card_ban_matches": 1
        #    },
        #     "information_scraping_urls": {
        #         "matches": "https://fbref.com/en/comps/32/{last_season[0]}/schedule/{last_season[0]}-Primeira-Liga-Scores-and-Fixtures",
        #         "ranking": "https://fbref.com/es/comps/33/{last_season[0]}/{last_season[0]}-Primeira-Liga-Stats",
        #         "fotmob": "https://www.fotmob.com/leagues/61/fixtures/liga-portugal?group=by-date&season={last_season[0]}&group=by-date&page={page}",
        #        "summer_transfers": "https://www.transfermarkt.co.uk/liga-nos/transfers/wettbewerb/PO1/plus/?saison_id={last_season[0]}&s_w=s&leihe=1&intern=0",
        #        "winter_transfers": "https://www.transfermarkt.co.uk/liga-nos/transfers/wettbewerb/PO1/plus/?saison_id={last_season[0]}&s_w=w&leihe=1&intern=0"
        #     },
        #     "betting_scraping_urls": {
        #         "betclic": "https://www.betclic.fr/football-sfootball/angl-premier-league-c3", # Cambiar
        #         "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/1/1",
        #         "unibet": "https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
        #         "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/angleterre/premier-league",
        #         "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B261%5D&boost=%5B%5D",
        #         "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-102841",
        #         "netbet": "https://www.netbet.fr/football/angleterre/premier-league",
        #         "betsson": "https://betsson.fr/fr/competitions/football/premier-league?competition_id=55768.1",
        #     },
        # },
        # ==================== EUROPEAN COMPETITIONS ====================
        "uefa_champions_league": {
            "country": "europe",
            "number_of_gameweeks": 98,
            "suspensions": {
                "yellow_cards_suspensions": {
                    "type": "milestones",
                    "milestones_cards": [3, 5, 7, 9],
                    "ban_matches": 1,
                },
                "red_card_ban_matches": 1
            },
            "information_scraping_urls": {
                "matches": "https://fbref.com/en/comps/8/{last_season[0]}/schedule/{last_season[0]}-Champions-League-Scores-and-Fixtures",
                "ranking": "https://fbref.com/en/comps/8/{last_season[0]}/{last_season[0]}-Champions-League-Stats",
                "fotmob": "https://www.fotmob.com/leagues/42/fixtures/champions-league?group=by-date&season={last_season[0]}&group=by-date&page={page}",
            },
            "betting_scraping_urls": {
                "betclic": "https://www.betclic.fr/football-sfootball/angl-premier-league-c3", # Cambiar
                "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/1/1",
                "unibet": "https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
                "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/angleterre/premier-league",
                "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B261%5D&boost=%5B%5D",
                "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-102841",
                "netbet": "https://www.netbet.fr/football/angleterre/premier-league",
                "betsson": "https://betsson.fr/fr/competitions/football/premier-league?competition_id=55768.1",
            },
        },
        "uefa_europa_league": {
            "country": "europe",
            "number_of_gameweeks": 98,
            "suspensions": {
                "yellow_cards_suspensions": {
                    "type": "milestones",
                    "milestones_cards": [3, 5, 7, 9],
                    "ban_matches": 1,
                },
                "red_card_ban_matches": 1
            },
            "information_scraping_urls": {
                "matches": "https://fbref.com/en/comps/19/{last_season[0]}/schedule/{last_season[0]}-Europa-League-Scores-and-Fixtures",
                "ranking": "https://fbref.com/en/comps/19/{last_season[0]}/{last_season[0]}-Europa-League-Stats",
                "fotmob": "https://www.fotmob.com/leagues/73/fixtures/europa-league?group=by-date&season={last_season[0]}&group=by-date&page={page}",
            },
            "betting_scraping_urls": {
                "betclic": "https://www.betclic.fr/football-sfootball/angl-premier-league-c3", # Cambiar
                "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/1/1",
                "unibet": "https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
                "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/angleterre/premier-league",
                "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B261%5D&boost=%5B%5D",
                "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-102841",
                "netbet": "https://www.netbet.fr/football/angleterre/premier-league",
                "betsson": "https://betsson.fr/fr/competitions/football/premier-league?competition_id=55768.1",
            },
        },
        "uefa_conference_league": {
            "country": "europe",
            "number_of_gameweeks": 98,
            "suspensions": {
                "yellow_cards_suspensions": {
                    "type": "milestones",
                    "milestones_cards": [3, 5, 7, 9],
                    "ban_matches": 1,
                },
                "red_card_ban_matches": 1
            },
            "information_scraping_urls": {
                "matches": "https://fbref.com/en/comps/882/{last_season[0]}/schedule/{last_season[0]}-Conference-League-Scores-and-Fixtures",
                "ranking": "https://fbref.com/en/comps/882/{last_season[0]}/{last_season[0]}-Conference-League-Stats",
                "fotmob": "https://www.fotmob.com/leagues/10216/fixtures/conference-league?group=by-date&season={last_season[0]}&group=by-date&page={page}",
            },
            "betting_scraping_urls": {
                "betclic": "https://www.betclic.fr/football-sfootball/angl-premier-league-c3", # Cambiar
                "winamax": "https://www.winamax.fr/paris-sportifs/sports/1/1/1",
                "unibet": "https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match",
                "parionssport": "https://www.enligne.parionssport.fdj.fr/paris-football/angleterre/premier-league",
                "pmu": "https://parisportif.pmu.fr/home/wrapper/events?fId=1&activeSportId=1&leagues=%5B261%5D&boost=%5B%5D",
                "bwin": "https://www.bwin.fr/fr/sports/football-4/paris-sportifs/angleterre-14/premier-league-102841",
                "netbet": "https://www.netbet.fr/football/angleterre/premier-league",
                "betsson": "https://betsson.fr/fr/competitions/football/premier-league?competition_id=55768.1",
            },
        },
    }

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached instance of Settings."""
    return Settings()
