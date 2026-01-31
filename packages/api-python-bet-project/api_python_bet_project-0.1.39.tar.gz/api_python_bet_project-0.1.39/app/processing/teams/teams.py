import os
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from typing import Dict

def process_stadium_location(df_match: pd.DataFrame, stadiums_path: str) -> pd.DataFrame:
    """
    Process stadium location information for a single match row.
    
    - Creates stadiums CSV if it doesn't exist
    - Looks up stadium location info based on stadium column
    - Asks user for missing stadium data
    - Updates both stadiums CSV and df_match
    
    Args:
        df_match: DataFrame with ONE match row (must have 'stadium' column)
        stadiums_path: Path to stadiums CSV file
        
    Returns:
        Updated df_match with longitude, latitude, and altitude columns
    """
    
    # Validate input
    if df_match.empty:
        print("[WARNING] Empty DataFrame provided, returning as is")
        return df_match
    
    if len(df_match) > 1:
        print(f"[WARNING] DataFrame has {len(df_match)} rows, only processing first row")
        df_match = df_match.iloc[[0]].copy()
    else:
        df_match = df_match.copy()
    
    # Ensure parent directory exists
    stadiums_dir = os.path.dirname(stadiums_path)
    if stadiums_dir:
        os.makedirs(stadiums_dir, exist_ok=True)
    
    # Check if stadiums CSV exists, if not create it
    if not os.path.exists(stadiums_path):
        print(f"[STADIUMS] Creating new stadiums CSV at {stadiums_path}")
        df_stadiums = pd.DataFrame(columns=['name', 'longitude', 'latitude', 'altitude'])
        df_stadiums.to_csv(stadiums_path, index=False, encoding='utf-8')
    else:
        df_stadiums = pd.read_csv(stadiums_path, encoding='utf-8')
    
    # Ensure df_match has the required column
    if 'stadium' not in df_match.columns:
        raise ValueError("df_match must have a 'stadium' column")
    
    # Add location info columns to df_match if they don't exist
    missing_cols = [col for col in ['longitude', 'latitude', 'altitude'] if col not in df_match.columns]
    if missing_cols:
        for col in missing_cols:
            df_match[col] = None
    
    # Get stadium name
    stadium_name = df_match['stadium'].iloc[0]
    
    if pd.isna(stadium_name) or stadium_name == '':
        print("[WARNING] No stadium name found in match, skipping location processing")
        return df_match
    
    print(f"[STADIUMS] Processing stadium: {stadium_name}")
    
    # Check if stadium exists in stadiums CSV
    stadium_match = df_stadiums[df_stadiums['name'] == stadium_name]
    
    if not stadium_match.empty:
        # Stadium found - get its data
        stadium_info = stadium_match.iloc[0]
        longitude = stadium_info['longitude']
        latitude = stadium_info['latitude']
        altitude = stadium_info['altitude']
        print(f"[STADIUMS] Found in database: {stadium_name}")
        
    else:
        # Stadium not found - ask user for data
        print(f"\n{'='*60}")
        print(f"Stadium NOT found in database: {stadium_name}")
        print(f"Please provide stadium location information:")
        print(f"{'='*60}\n")
        
        # Ask for longitude
        while True:
            try:
                longitude_input = input(f"   Longitude (decimal degrees, e.g., -3.688): ").strip()
                if longitude_input == '':
                    longitude = None
                    break
                longitude = float(longitude_input)
                break
            except ValueError:
                print("   Invalid input. Please enter a valid number or press Enter to skip.")
        
        # Ask for latitude
        while True:
            try:
                latitude_input = input(f"   Latitude (decimal degrees, e.g., 40.453): ").strip()
                if latitude_input == '':
                    latitude = None
                    break
                latitude = float(latitude_input)
                break
            except ValueError:
                print("   Invalid input. Please enter a valid number or press Enter to skip.")
        
        # Ask for altitude
        while True:
            try:
                altitude_input = input(f"   Altitude (meters, e.g., 667): ").strip()
                if altitude_input == '':
                    altitude = None
                    break
                altitude = float(altitude_input)
                break
            except ValueError:
                print("   Invalid input. Please enter a valid number or press Enter to skip.")
        
        # Add new stadium to df_stadiums
        new_stadium = pd.DataFrame([{
            'name': stadium_name,
            'longitude': longitude,
            'latitude': latitude,
            'altitude': altitude
        }])
        
        df_stadiums = pd.concat([df_stadiums, new_stadium], ignore_index=True)
        
        # Save updated stadiums CSV
        df_stadiums.to_csv(stadiums_path, index=False, encoding='utf-8')
        print(f"[STADIUMS] Added new stadium to {stadiums_path}")
    
    # Update df_match with stadium location info
    df_match.loc[df_match.index[0], 'longitude'] = longitude
    df_match.loc[df_match.index[0], 'latitude'] = latitude
    df_match.loc[df_match.index[0], 'altitude'] = altitude
    
    print(f"[STADIUMS] Location data added to match")
    
    return df_match

def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    
    Returns distance in kilometers.
    """
    if pd.isna(lon1) or pd.isna(lat1) or pd.isna(lon2) or pd.isna(lat2):
        return None
    
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return r * c

def get_season_from_date(date: pd.Timestamp) -> str:
    """
    Determine the season (YYYY-YYYY) from a date.
    Season runs from August 1st to June 30th.
    
    Args:
        date: Date to determine season for
        
    Returns:
        Season string in format "YYYY-YYYY"
    """
    year = date.year
    month = date.month
    
    # If month is August (8) or later, season is current_year - next_year
    # If month is before August, season is previous_year - current_year
    if month >= 8:
        return f"{year}-{year+1}"
    else:
        return f"{year-1}-{year}"

def calculate_accumulated_distance(
    team_name: str,
    current_date: pd.Timestamp,
    df: pd.DataFrame,
    df_teams: pd.DataFrame
) -> float:
    """
    Calculate accumulated distance traveled by a team in the current season.
    Season runs from August 1st to June 30th.
    
    Args:
        team_name: Name of the team
        current_date: Current match date
        df: Complete DataFrame with all matches
        df_teams: DataFrame with team locations
        
    Returns:
        Accumulated distance in kilometers for current season
    """
    # Get current season
    current_season = get_season_from_date(current_date)
    season_start_year = int(current_season.split('-')[0])
    
    # Define season boundaries
    season_start = pd.Timestamp(f"{season_start_year}-08-01")
    season_end = pd.Timestamp(f"{season_start_year + 1}-06-30")
    
    # Get team's home coordinates
    team_info = df_teams[df_teams['name'] == team_name]
    if team_info.empty:
        return None
    
    team_home_lon = team_info['longitude'].iloc[0]
    team_home_lat = team_info['latitude'].iloc[0]
    
    if pd.isna(team_home_lon) or pd.isna(team_home_lat):
        return None
    
    # Get all matches for this team in the current season BEFORE current_date
    team_matches = df[
        ((df['home_team_name'] == team_name) | (df['away_team_name'] == team_name)) &
        (df['date_of_match'] >= season_start) &
        (df['date_of_match'] < current_date) &
        (df['date_of_match'] <= season_end)
    ].copy()
    
    if team_matches.empty:
        return 0.0  # No previous matches in this season
    
    # Sort by date
    team_matches = team_matches.sort_values('date_of_match')
    
    total_accumulated = 0.0
    last_location_lon = team_home_lon
    last_location_lat = team_home_lat
    
    for idx, match in team_matches.iterrows():
        # Determine where the team played this match
        was_home = match['home_team_name'] == team_name
        
        if was_home:
            # Playing at home
            match_lon = team_home_lon
            match_lat = team_home_lat
        else:
            # Playing away - get opponent's location
            opponent = match['home_team_name']
            opponent_info = df_teams[df_teams['name'] == opponent]
            
            if opponent_info.empty:
                continue  # Skip if opponent location not found
            
            match_lon = opponent_info['longitude'].iloc[0]
            match_lat = opponent_info['latitude'].iloc[0]
            
            if pd.isna(match_lon) or pd.isna(match_lat):
                continue
        
        # Calculate distance from last location to this match
        distance = haversine_distance(
            last_location_lon, last_location_lat,
            match_lon, match_lat
        )
        
        if distance is not None:
            total_accumulated += distance
        
        # Update last location
        # After the match, team returns home
        last_location_lon = team_home_lon
        last_location_lat = team_home_lat
    
    return total_accumulated

def calculate_team_travel_distance(
    match_row: pd.DataFrame, 
    df: pd.DataFrame,
    stadiums_path: str = "app/data/raw/teams/stadiums.csv"
) -> pd.DataFrame:
    """
    Calculate travel distances for both teams in a match.
    
    For each team:
    1. Get their home coordinates (using process_team_location)
    2. Find their last match (as home or away)
    3. Calculate distance from last match location to their home
    4. Calculate distance from their home to current match location
    5. Calculate accumulated distance for the current season (INCLUDING current match)
    
    Args:
        match_row: DataFrame with ONE match row
        df: Complete DataFrame with all historical matches
        teams_path: Path to teams CSV file
        
    Returns:
        Updated match_row with columns:
        - home_team_distance: km traveled by home team for this match
        - away_team_distance: km traveled by away team for this match
        - home_team_accumulated_distance: total km traveled by home team this season (including current match)
        - away_team_accumulated_distance: total km traveled by away team this season (including current match)
        - altitude: altitude of the match venue
    """
    
    # Validate input
    if match_row.empty:
        print("[WARNING] Empty DataFrame provided")
        return match_row
    
    if len(match_row) > 1:
        print(f"[WARNING] DataFrame has {len(match_row)} rows, only processing first row")
        match_row = match_row.iloc[[0]].copy()
    else:
        match_row = match_row.copy()
    
    # Required columns
    required_cols = ['home_team_name', 'away_team_name', 'date_of_match']
    missing = [col for col in required_cols if col not in match_row.columns]
    if missing:
        raise ValueError(f"match_row must have columns: {missing}")
    
    # Get current match info
    home_team = match_row['home_team_name'].iloc[0]
    away_team = match_row['away_team_name'].iloc[0]
    current_date = pd.to_datetime(match_row['date_of_match'].iloc[0])
    
    # Process current match location (home team's stadium)
    match_row = process_stadium_location(match_row, stadiums_path=stadiums_path)
    
    current_lon = match_row['longitude'].iloc[0]
    current_lat = match_row['latitude'].iloc[0]
    current_alt = match_row['altitude'].iloc[0]
    
    # Ensure df has date column as datetime
    df = df.copy()
    if 'date_of_match' in df.columns:
        df['date_of_match'] = pd.to_datetime(df['date_of_match'], errors='coerce')
    
    # Load teams database
    if not os.path.exists(stadiums_path):
        df_teams = pd.DataFrame(columns=['name', 'longitude', 'latitude', 'altitude'])
        os.makedirs(os.path.dirname(stadiums_path), exist_ok=True)
        df_teams.to_csv(stadiums_path, index=False, encoding='utf-8')
    else:
        df_teams = pd.read_csv(stadiums_path, encoding='utf-8')
    
    # Initialize distance columns
    match_row['home_team_distance'] = None
    match_row['away_team_distance'] = None
    match_row['home_team_accumulated_distance'] = None
    match_row['away_team_accumulated_distance'] = None
    match_row['altitude'] = current_alt
    
    # Process each team
    for team_type in ['home', 'away']:
        team_name = home_team if team_type == 'home' else away_team
        
        
        # Get team's home coordinates (o preguntar si no existe)
        team_info = df_teams[df_teams['name'] == team_name]
        
        if team_info.empty:
            print(f"{team_name} not found in teams database.")
            print(f"Please provide {team_name}'s home stadium location:")
            
            # Ask for longitude
            while True:
                try:
                    longitude_input = input(f"   Longitude (decimal degrees, e.g., -3.688): ").strip()
                    if longitude_input == '':
                        team_home_lon = None
                        break
                    team_home_lon = float(longitude_input)
                    break
                except ValueError:
                    print("   Invalid input. Please enter a valid number or press Enter to skip.")
            
            # Ask for latitude
            while True:
                try:
                    latitude_input = input(f"   Latitude (decimal degrees, e.g., 40.453): ").strip()
                    if latitude_input == '':
                        team_home_lat = None
                        break
                    team_home_lat = float(latitude_input)
                    break
                except ValueError:
                    print("   Invalid input. Please enter a valid number or press Enter to skip.")
            
            # Ask for altitude
            while True:
                try:
                    altitude_input = input(f"   Altitude (meters, e.g., 667): ").strip()
                    if altitude_input == '':
                        team_altitude = None
                        break
                    team_altitude = float(altitude_input)
                    break
                except ValueError:
                    print("   Invalid input. Please enter a valid number or press Enter to skip.")
            
            # Add to dataframe
            new_team = pd.DataFrame([{
                'name': team_name,
                'longitude': team_home_lon,
                'latitude': team_home_lat,
                'altitude': team_altitude
            }])
            
            df_teams = pd.concat([df_teams, new_team], ignore_index=True)
            df_teams.to_csv(stadiums_path, index=False, encoding='utf-8')
            
        else:
            team_home_lon = team_info['longitude'].iloc[0]
            team_home_lat = team_info['latitude'].iloc[0]
        
        if pd.isna(team_home_lon) or pd.isna(team_home_lat):
            print(f"{team_name} has incomplete location data, skipping distance calculation")
            continue
        
        
        # =================================================================
        # CALCULATE MATCH DISTANCE (last match → home → current match)
        # =================================================================
        
        # Find team's last match before current date
        team_matches = df[
            ((df['home_team_name'] == team_name) | (df['away_team_name'] == team_name)) &
            (df['date_of_match'] < current_date)
        ].copy()
        
        # Variable para guardar la distancia del partido actual
        current_match_distance = None
        
        if team_matches.empty:
            # If no previous match, distance is 0 (they're at home) or distance from home to current venue
            if team_type == 'home':
                current_match_distance = 0.0  # Playing at home
            else:
                # Calcular distancia desde casa del away team al estadio del partido
                current_match_distance = haversine_distance(team_home_lon, team_home_lat, current_lon, current_lat)
            
            match_row.loc[match_row.index[0], f'{team_type}_team_distance'] = current_match_distance
        else:
            # Sort by date to get the most recent match
            team_matches = team_matches.sort_values('date_of_match', ascending=False)
            last_match = team_matches.iloc[0]
            
            last_match_date = last_match['date_of_match']
            
            # Determine where the team played their last match
            was_home = last_match['home_team_name'] == team_name
            
            if was_home:
                last_match_lon = team_home_lon
                last_match_lat = team_home_lat
            else:
                opponent = last_match['home_team_name']
                opponent_info = df_teams[df_teams['name'] == opponent]
                
                if opponent_info.empty or pd.isna(opponent_info['longitude'].iloc[0]):
                    print(f"   Cannot find location for opponent {opponent}")
                    continue
                
                last_match_lon = opponent_info['longitude'].iloc[0]
                last_match_lat = opponent_info['latitude'].iloc[0]
            
            
            # Calculate distance from last match to their home
            dist_last_to_home = haversine_distance(
                last_match_lon, last_match_lat,
                team_home_lon, team_home_lat
            )
            
            # Calculate distance from their home to current match
            dist_home_to_current = haversine_distance(
                team_home_lon, team_home_lat,
                current_lon, current_lat
            )
            
            # Total distance traveled for this match
            if dist_last_to_home is not None and dist_home_to_current is not None:
                current_match_distance = dist_last_to_home + dist_home_to_current
            else:
                current_match_distance = None
                print(f"   Could not calculate total distance")
            
            # Store match distance
            match_row.loc[match_row.index[0], f'{team_type}_team_distance'] = current_match_distance
        
        # =================================================================
        # CALCULATE ACCUMULATED DISTANCE FOR THE SEASON
        # =================================================================
        
        
        # Calcular acumulada de partidos PREVIOS (sin incluir el actual)
        accumulated_distance_previous = calculate_accumulated_distance(
            team_name=team_name,
            current_date=current_date,
            df=df,
            df_teams=df_teams
        )
        
        if accumulated_distance_previous is not None and current_match_distance is not None:
            total_accumulated = accumulated_distance_previous + current_match_distance
            match_row.loc[match_row.index[0], f'{team_type}_team_accumulated_distance'] = total_accumulated
        elif current_match_distance is not None:
            # Si no hay acumulada previa, usar solo la distancia actual
            match_row.loc[match_row.index[0], f'{team_type}_team_accumulated_distance'] = current_match_distance
        else:
            print(f"   Could not calculate accumulated distance")
    
    return match_row

def compute_rest_times(df_row: pd.Series, historical_matches_path: str) -> pd.Series:
    """
    Compute rest time in hours for home and away teams based on the immediately
    previous match each team played (home or away) across ANY competition.
    
    Args:
        df_row: Single row (Series) containing the match information
        historical_matches_path: Path to CSV file with all historical matches
    
    Returns:
        Series with only the computed columns:
        - home_team_rest_time
        - away_team_rest_time
    """
    
    def _to_datetime(date_str, hour_str):
        """
        Build a datetime from date + hour-of-match strings.
        If hour is missing, default to 00:00.
        """
        dt = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(dt):
            return pd.NaT
        
        # Parse hour as HH:MM
        if pd.notna(hour_str):
            try:
                time_obj = pd.to_datetime(hour_str, format="%H:%M", errors="coerce")
                if pd.notna(time_obj):
                    dt = dt.replace(hour=time_obj.hour, minute=time_obj.minute)
            except:
                pass  # Keep dt with 00:00 if parsing fails
        
        return dt
    
    # Initialize result with only the columns we're computing
    result = pd.Series({
        'home_team_rest_time': pd.NA,
        'away_team_rest_time': pd.NA
    })
    
    # Read historical matches
    try:
        df_historical = pd.read_csv(historical_matches_path)
    except FileNotFoundError:
        print(f"Warning: Historical matches file not found at {historical_matches_path}")
        return result
    
    # Get current match info
    home_team = df_row.get("home_team_name")
    away_team = df_row.get("away_team_name")
    current_date = df_row.get("date_of_match")
    current_hour = df_row.get("hour_of_the_match", None)
    
    # Build current match datetime
    current_dt = _to_datetime(current_date, current_hour)
    
    if pd.isna(current_dt):
        return result
    
    # Ensure required columns exist in historical data
    if "hour_of_the_match" not in df_historical.columns:
        df_historical["hour_of_the_match"] = pd.NA
    
    # Build datetime for all historical matches
    df_historical["match_dt"] = df_historical.apply(
        lambda row: _to_datetime(row["date_of_match"], row.get("hour_of_the_match")),
        axis=1
    )
    
    # Filter only matches with valid datetime and before current match
    df_historical = df_historical[
        (~df_historical["match_dt"].isna()) & 
        (df_historical["match_dt"] < current_dt)
    ]
    
    # --- Compute rest time for HOME team ---
    home_team_matches = df_historical[
        (df_historical["home_team_name"] == home_team) | 
        (df_historical["away_team_name"] == home_team)
    ]
    
    if not home_team_matches.empty:
        last_home_match = home_team_matches.nlargest(1, "match_dt").iloc[0]
        prev_home_dt = last_home_match["match_dt"]
        time_diff = current_dt - prev_home_dt
        result["home_team_rest_time"] = time_diff.total_seconds() / 3600.0
    
    # --- Compute rest time for AWAY team ---
    away_team_matches = df_historical[
        (df_historical["home_team_name"] == away_team) | 
        (df_historical["away_team_name"] == away_team)
    ]
    
    if not away_team_matches.empty:
        last_away_match = away_team_matches.nlargest(1, "match_dt").iloc[0]
        prev_away_dt = last_away_match["match_dt"]
        time_diff = current_dt - prev_away_dt
        result["away_team_rest_time"] = time_diff.total_seconds() / 3600.0
    
    return result

def calculate_accumulated_matches_for_row(
    df_row: pd.Series,
    df: pd.DataFrame
) -> pd.Series:
    """
    Calculate accumulated matches for both teams in a row.
    Season runs from August 1st to June 30th.
    
    Args:
        df_row: Single row (Series) containing the match information
        df: Complete DataFrame with all matches
        
    Returns:
        Series with only the computed columns:
        - home_team_accumulated_matches
        - away_team_accumulated_matches
    """
    # Get current match info
    home_team = df_row.get("home_team_name")
    away_team = df_row.get("away_team_name")
    current_date = pd.to_datetime(df_row.get("date_of_match"))
    
    # Get current season
    current_season = get_season_from_date(current_date)
    season_start_year = int(current_season.split('-')[0])
    
    # Define season boundaries
    season_start = pd.Timestamp(f"{season_start_year}-08-01")
    season_end = pd.Timestamp(f"{season_start_year + 1}-06-30")
    
    # Ensure df has date column as datetime
    df_copy = df.copy()
    if 'date_of_match' in df_copy.columns:
        df_copy['date_of_match'] = pd.to_datetime(df_copy['date_of_match'], errors='coerce')
    
    # Calculate for home team
    home_team_matches = df_copy[
        ((df_copy['home_team_name'] == home_team) | (df_copy['away_team_name'] == home_team)) &
        (df_copy['date_of_match'] >= season_start) &
        (df_copy['date_of_match'] < current_date) &
        (df_copy['date_of_match'] <= season_end)
    ]
    
    # Calculate for away team
    away_team_matches = df_copy[
        ((df_copy['home_team_name'] == away_team) | (df_copy['away_team_name'] == away_team)) &
        (df_copy['date_of_match'] >= season_start) &
        (df_copy['date_of_match'] < current_date) &
        (df_copy['date_of_match'] <= season_end)
    ]
    
    # Return only the calculated columns
    return pd.Series({
        'home_team_accumulated_matches': len(home_team_matches),
        'away_team_accumulated_matches': len(away_team_matches)
    })

def calculate_team_travel_distance_for_row(
    df_row: pd.Series,
    df: pd.DataFrame,
    teams_path: str = "app/data/raw/teams/teams.csv"
) -> pd.Series:
    """
    Calculate travel distances and geographic info for both teams in a match row.
    
    Returns:
        Series with only the computed columns:
        - home_team_distance
        - away_team_distance
        - home_team_accumulated_distance
        - away_team_accumulated_distance
        - altitude
        - longitude
        - latitude
    """
    # Convert Series to DataFrame for existing function
    row_df = df_row.to_frame().T
    
    # Call existing function
    result_df = calculate_team_travel_distance(
        match_row=row_df,
        df=df,
        teams_path=teams_path
    )
    
    # Extract only the columns we want to return
    result_row = result_df.iloc[0]
    
    return pd.Series({
        'home_team_distance': result_row.get('home_team_distance'),
        'away_team_distance': result_row.get('away_team_distance'),
        'home_team_accumulated_distance': result_row.get('home_team_accumulated_distance'),
        'away_team_accumulated_distance': result_row.get('away_team_accumulated_distance'),
        'altitude': result_row.get('altitude'),
        'longitude': result_row.get('longitude'),
        'latitude': result_row.get('latitude')
    })

def enrich_with_geographic_and_temporal_features(
    df_matches: pd.DataFrame,
    df_all_matches: pd.DataFrame,
    stadiums_path: str,
    historical_matches_path: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Enrich matches DataFrame with geographic and temporal features.
    
    Features added:
    - Travel distances (home/away team distance, accumulated distance)
    - Geographic info (longitude, latitude, altitude)
    - Rest times (home/away team rest time)
    - Accumulated matches count (home/away team accumulated matches)
    
    Args:
        df_matches: DataFrame with matches to enrich
        df_all_matches: DataFrame with ALL historical matches (for calculating accumulated features)
        stadiums_path: Path to stadiums CSV file
        historical_matches_path: Path to complete historical matches CSV
        verbose: Print progress information
        
    Returns:
        Enriched DataFrame with all geographic and temporal features
    """
    
    if df_matches.empty:
        print("[FEATURES] Empty DataFrame provided, returning as is")
        return df_matches
    
    if verbose:
        print(f"\n[FEATURES] ========== Starting feature enrichment ==========")
        print(f"[FEATURES] Matches to process: {len(df_matches)}")
        print(f"[FEATURES] Historical matches available: {len(df_all_matches)}")
    
    # Make a copy to avoid modifying original
    df_result = df_matches.copy()
    
    # 1. Calculate travel distances + geographic info
    if verbose:
        print(f"\n[FEATURES] Step 1/3: Calculating travel distances and geographic info...")
    
    travel_features = df_result.apply(
        lambda row: calculate_team_travel_distance_for_row(
            df_row=row,
            df=df_all_matches,
            teams_path=stadiums_path
        ),
        axis=1
    )
    
    if verbose:
        print(f"[FEATURES]   Added columns: {travel_features.columns.tolist()}")
    
    # 2. Calculate rest times
    if verbose:
        print(f"\n[FEATURES] Step 2/3: Calculating rest times...")
    
    rest_features = df_result.apply(
        lambda row: compute_rest_times(
            df_row=row,
            historical_matches_path=historical_matches_path
        ),
        axis=1
    )
    
    if verbose:
        print(f"[FEATURES]   Added columns: {rest_features.columns.tolist()}")
    
    # 3. Calculate accumulated matches
    if verbose:
        print(f"\n[FEATURES] Step 3/3: Calculating accumulated matches...")
    
    matches_features = df_result.apply(
        lambda row: calculate_accumulated_matches_for_row(
            df_row=row,
            df=df_all_matches
        ),
        axis=1
    )
    
    if verbose:
        print(f"[FEATURES]   Added columns: {matches_features.columns.tolist()}")
    
    # Concatenate all features
    df_result = pd.concat([df_result, travel_features, rest_features, matches_features], axis=1)
    
    if verbose:
        print(f"\n[FEATURES] Feature enrichment complete!")
        print(f"[FEATURES] Final shape: {df_result.shape}")
        print(f"[FEATURES] New columns added:")
        new_cols = set(df_result.columns) - set(df_matches.columns)
        for col in sorted(new_cols):
            print(f"[FEATURES]   - {col}")
        print(f"[FEATURES] ========== Feature enrichment finished ==========\n")
    
    return df_result

def enrich_with_team_history(
    df: pd.DataFrame,
    teams_columns: Dict[str, type],
    csv_path: str,
    country: str,
) -> pd.DataFrame:
    """
    Enrich dataframe with team historical information.
    Simply iterates through teams_columns and asks for each value.
    
    Args:
        df: DataFrame with matches (must have home_team_name, away_team_name)
        teams_columns: Dictionary with column names and types (base names, will add home_/away_ prefix)
        csv_path: Path to CSV file with team historical information
        country: Country of the competition (if 'europe', will ask for team country)

    Returns:
        DataFrame with enriched team history columns
    """
    
    # Read or create teams CSV
    if not os.path.exists(csv_path):
        print(f"Creating new teams history CSV at {csv_path}")
        df_teams = pd.DataFrame(columns=['name', 'country'])
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df_teams.to_csv(csv_path, index=False, encoding='utf-8')
    else:
        df_teams = pd.read_csv(csv_path, encoding='utf-8')
    
    # Make a copy
    df_result = df.copy()
    
    # Initialize columns with home_ and away_ prefixes
    type_mapping = {int: "Int64", float: "float64", str: "string"}
    
    for base_col, col_type in teams_columns.items():
        dtype = type_mapping.get(col_type, "object")
        home_col = f"home_{base_col}"
        away_col = f"away_{base_col}"
        
        if home_col not in df_result.columns:
            df_result[home_col] = pd.Series([None] * len(df_result), dtype=dtype)
        if away_col not in df_result.columns:
            df_result[away_col] = pd.Series([None] * len(df_result), dtype=dtype)
    
    # Ensure all columns exist in df_teams
    if 'country' not in df_teams.columns:
        df_teams['country'] = ''
    for base_col in teams_columns.keys():
        if base_col not in df_teams.columns:
            df_teams[base_col] = 0  # Default value
    
    def ask_team_data(team_name: str, prefix: str, idx: int) -> dict:
        """Ask user for all team data."""
        print(f"\n{'='*60}")
        print(f"Team: {team_name} (position: {prefix})")
        print(f"{'='*60}\n")
        
        new_team_data = {'name': team_name}
        
        # Handle country column specially
        if country == 'europe':
            while True:
                team_country = input(f"Country: ").strip()
                if team_country:
                    new_team_data['country'] = team_country
                    break
                else:
                    print("Country is required for European competitions.")
        else:
            new_team_data['country'] = country
            print(f"Country: {country} (auto-assigned)")
        
        # Simply iterate through all columns and ask
        for base_col, col_type in teams_columns.items():
            # Make display name user-friendly
            display_name = base_col.replace('_', ' ').title()
            
            while True:
                try:
                    user_input = input(f"{display_name}: ").strip()
                    
                    if user_input == '':
                        value = 0  # Default
                        break
                    
                    if col_type == int:
                        value = int(user_input)
                    elif col_type == float:
                        value = float(user_input)
                    else:
                        value = user_input
                    break
                    
                except ValueError:
                    print(f"Invalid input. Please enter a valid {col_type.__name__}.")
            
            # Save to CSV (without prefix)
            new_team_data[base_col] = value
            
            # Save to df_result (WITH prefix)
            target_col = f"{prefix}_{base_col}"
            if target_col in df_result.columns:
                df_result.at[idx, target_col] = value
        
        return new_team_data
    
    # Collect all unique teams from the matches DataFrame
    all_teams = set()
    if 'home_team_name' in df.columns:
        all_teams.update(df['home_team_name'].dropna().unique())
    if 'away_team_name' in df.columns:
        all_teams.update(df['away_team_name'].dropna().unique())
        
    # Check which teams are missing from CSV
    existing_teams = set(df_teams['name'].values) if 'name' in df_teams.columns else set()
    missing_teams = all_teams - existing_teams
    
    if missing_teams:
        print(f"[TEAM HISTORY] Missing teams: {len(missing_teams)}")
        print(f"[TEAM HISTORY] Teams to add: {sorted(missing_teams)}")
        
        # Ask for data for each missing team
        new_teams_data = []
        for team_name in sorted(missing_teams):
            # Use dummy values for prefix and idx since we're just collecting data
            new_data = ask_team_data(team_name, "team", 0)
            new_teams_data.append(new_data)
        
        # Add new teams to df_teams
        if new_teams_data:
            df_new_teams = pd.DataFrame(new_teams_data)
            df_teams = pd.concat([df_teams, df_new_teams], ignore_index=True)
            df_teams.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"\n[TEAM HISTORY] Added {len(new_teams_data)} new teams to {csv_path}")
    
    # Now enrich the matches DataFrame with team data    
    for idx, row in df_result.iterrows():
        # Home team
        home_team = row['home_team_name']
        if pd.notna(home_team) and home_team in df_teams['name'].values:
            team_data = df_teams[df_teams['name'] == home_team].iloc[0]
            for base_col in teams_columns.keys():
                if base_col in team_data:
                    df_result.at[idx, f'home_{base_col}'] = team_data[base_col]
        
        # Away team
        away_team = row['away_team_name']
        if pd.notna(away_team) and away_team in df_teams['name'].values:
            team_data = df_teams[df_teams['name'] == away_team].iloc[0]
            for base_col in teams_columns.keys():
                if base_col in team_data:
                    df_result.at[idx, f'away_{base_col}'] = team_data[base_col]
        
    return df_result

def update_league_winners(
    ranking_csv_path: str,
    trophies_csv_path: str,
    comp_gameweeks: int = 38,
    verbose: bool = False
) -> None:
    """
    Update first and second place trophies after gameweek 38.
    
    Reads the ranking CSV, finds gameweek 38 standings, and updates:
    - 1st place team: +1 to first_place_league
    - 2nd place team: +1 to second_place_league
    
    Args:
        ranking_csv_path: Path to the ranking CSV file
        trophies_csv_path: Path to the team trophies CSV file
        comp_gameweeks: Number of gameweeks to check for final standings
        verbose: Print debugging information
    """
    
    if verbose:
        print("[TROPHIES] Updating league winners...")
    
    # Read ranking CSV
    if not os.path.exists(ranking_csv_path):
        print(f"[TROPHIES] ERROR: Ranking CSV not found!")
        raise FileNotFoundError(f"Ranking CSV not found: {ranking_csv_path}")
    
    df_ranking = pd.read_csv(ranking_csv_path, encoding='utf-8')
    
    if verbose:
        print(f"[TROPHIES] Loaded ranking CSV with {len(df_ranking)} rows")
    
    # Filter for gameweek 38
    df_gw38 = df_ranking[df_ranking['gameweek'] == comp_gameweeks]
        
    if df_gw38.empty:
        if verbose:
            print(f"[TROPHIES] No gameweek {comp_gameweeks} data found in ranking CSV")
        return
    
    # Sort by team_rank to ensure correct order
    df_gw38 = df_gw38.sort_values('team_rank')
    
    # Get 1st and 2nd place teams
    first_place_team = df_gw38.iloc[0]['team_name']
    second_place_team = df_gw38.iloc[1]['team_name'] if len(df_gw38) > 1 else None
    
    if verbose:
        print(f"[TROPHIES] 1st place: {first_place_team}")
        if second_place_team:
            print(f"[TROPHIES] 2nd place: {second_place_team}")
    
    # Read or create trophies CSV
    if not os.path.exists(trophies_csv_path):
        if verbose:
            print(f"[TROPHIES] Creating new trophies CSV at {trophies_csv_path}")
        df_trophies = pd.DataFrame(columns=['name', 'country', 'first_place_league', 
                                            'second_place_league', 'years_total_league',
                                            'years_consecutive_league'])
        os.makedirs(os.path.dirname(trophies_csv_path), exist_ok=True)
    else:
        df_trophies = pd.read_csv(trophies_csv_path, encoding='utf-8')
    
    # Ensure required columns exist
    for col in ['first_place_league', 'second_place_league']:
        if col not in df_trophies.columns:
            df_trophies[col] = 0
        
    # Update first place
    if first_place_team in df_trophies['name'].values:
        old_count = df_trophies.loc[df_trophies['name'] == first_place_team, 'first_place_league'].iloc[0]
        df_trophies.loc[df_trophies['name'] == first_place_team, 'first_place_league'] += 1
        new_count = df_trophies.loc[df_trophies['name'] == first_place_team, 'first_place_league'].iloc[0]
        if verbose:
            print(f"[TROPHIES] {first_place_team}: first_place_league = {new_count}")
    else:
        if verbose:
            print(f"[TROPHIES] Warning: {first_place_team} not found in trophies CSV")
    
    # Update second place
    if second_place_team and second_place_team in df_trophies['name'].values:
        old_count = df_trophies.loc[df_trophies['name'] == second_place_team, 'second_place_league'].iloc[0]
        df_trophies.loc[df_trophies['name'] == second_place_team, 'second_place_league'] += 1
        new_count = df_trophies.loc[df_trophies['name'] == second_place_team, 'second_place_league'].iloc[0]
        if verbose:
            print(f"[TROPHIES] {second_place_team}: second_place_league = {new_count}")
    elif second_place_team:
        if verbose:
            print(f"[TROPHIES] Warning: {second_place_team} not found in trophies CSV")
    
    # Save updated CSV
    df_trophies.to_csv(trophies_csv_path, index=False, encoding='utf-8')
    
    if verbose:
        print(f"[TROPHIES] Updated trophies saved to {trophies_csv_path}")

def update_european_winners(
    trophies_csv_path: str,
    final_match_df: pd.DataFrame,
    competition_name: str,
    verbose: bool = False
) -> None:
    """
    Update European competition trophies after a final match.
    
    Reads the final match result and updates trophies CSV:
    - Winner: +1 to first_place_europe_X
    - Runner-up: +1 to second_place_europe_X
    
    Args:
        trophies_csv_path: Path to the team trophies CSV file
        final_match_df: DataFrame with the final match (single row)
        competition_name: Name of the competition ('uefa_champions_league', 'uefa_europa_league', 
                        'uefa_conference_league', 'europe_supercup')
        verbose: Print debugging information
    """
    
    # Map competition names to trophy column suffixes
    competition_mapping = {
        'uefa_champions_league': 'europe_1',
        'uefa_europa_league': 'europe_2',
        'uefa_conference_league': 'europe_3',
        'europe_supercup': 'europe_supercup'
    }
    
    trophy_suffix = competition_mapping[competition_name]
    first_place_col = f'first_place_{trophy_suffix}'
    second_place_col = f'second_place_{trophy_suffix}'
        
    if verbose:
        print(f"[TROPHIES] Updating {competition_name} winners...")
    
    # Validate final match DataFrame
    if final_match_df.empty:
        raise ValueError("Final match DataFrame is empty")
    
    if len(final_match_df) > 1:
        print(f"[TROPHIES] WARNING: Multiple matches provided, using first row only")
        final_match_df = final_match_df.iloc[[0]]
    
    # Extract match data
    home_team = final_match_df.iloc[0]['home_team_name']
    away_team = final_match_df.iloc[0]['away_team_name']
    result = final_match_df.iloc[0]['result']
    
    # Determine winner and runner-up based on result
    if result == 0:
        # Home team won
        winner = home_team
        runner_up = away_team
    elif result == 2:
        # Away team won
        winner = away_team
        runner_up = home_team
    else:
        raise ValueError(f"Invalid result value: {result}. Expected 0 (home win) or 2 (away win)")
    
    if verbose:
        print(f"[TROPHIES] Winner: {winner}")
        print(f"[TROPHIES] Runner-up: {runner_up}")
    
    # Read or create trophies CSV
    if not os.path.exists(trophies_csv_path):
        if verbose:
            print(f"[TROPHIES] Creating new trophies CSV at {trophies_csv_path}")
        
        # Create with all European trophy columns
        df_trophies = pd.DataFrame(columns=[
            'name', 'country', 
            'first_place_league', 'second_place_league', 'years_total_league', 'years_consecutive_league',
            'first_place_cup', 'second_place_cup',
            'first_place_supercup', 'second_place_supercup',
            'first_place_europe_1', 'second_place_europe_1',
            'first_place_europe_2', 'second_place_europe_2',
            'first_place_europe_3', 'second_place_europe_3',
            'first_place_europe_supercup', 'second_place_europe_supercup',
            'years_total_europe', 'years_consecutive_europe'
        ])
        os.makedirs(os.path.dirname(trophies_csv_path), exist_ok=True)
    else:
        df_trophies = pd.read_csv(trophies_csv_path, encoding='utf-8')
    
    # Ensure required columns exist
    for col in [first_place_col, second_place_col]:
        if col not in df_trophies.columns:
            df_trophies[col] = 0
        
    # Update winner
    if winner in df_trophies['name'].values:
        old_count = df_trophies.loc[df_trophies['name'] == winner, first_place_col].iloc[0]
        df_trophies.loc[df_trophies['name'] == winner, first_place_col] += 1
        new_count = df_trophies.loc[df_trophies['name'] == winner, first_place_col].iloc[0]
        if verbose:
            print(f"[TROPHIES] {winner}: {first_place_col} = {new_count}")
    else:
        if verbose:
            print(f"[TROPHIES] Warning: {winner} not found in trophies CSV")
    
    # Update runner-up
    if runner_up in df_trophies['name'].values:
        old_count = df_trophies.loc[df_trophies['name'] == runner_up, second_place_col].iloc[0]
        df_trophies.loc[df_trophies['name'] == runner_up, second_place_col] += 1
        new_count = df_trophies.loc[df_trophies['name'] == runner_up, second_place_col].iloc[0]
        if verbose:
            print(f"[TROPHIES] {runner_up}: {second_place_col} = {new_count}")
    else:
        if verbose:
            print(f"[TROPHIES] Warning: {runner_up} not found in trophies CSV")
    
    # Save updated CSV
    df_trophies.to_csv(trophies_csv_path, index=False, encoding='utf-8')
    
    if verbose:
        print(f"[TROPHIES] Updated trophies saved to {trophies_csv_path}")

def update_league_season_participation(
    df_matches: pd.DataFrame,
    country: str,
    trophies_csv_path: str,
    teams_columns: Dict[str, type] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Update team participation stats before gameweek 1 of a new season.
    Returns df_matches enriched with initial ranking and team history data.
    
    For teams participating in this season's league (present in df_matches):
    - Increments years_total_league by 1
    - Increments years_consecutive_league by 1
    - Creates gameweek 0 ranking based on trophy history
    - Enriches df_matches with ranking columns (all stats at 0 except team_rank)
    - Enriches df_matches with team historical information
    
    For teams from the same country NOT participating:
    - Resets years_consecutive_league to 0
    
    Also asks user for Cup and Supercup winners/runners-up and updates trophies.
    
    Args:
        df_matches: DataFrame with matches (must have home_team and/or away_team columns)
        country: Country code to filter teams (e.g., 'ESP', 'ENG')
        trophies_csv_path: Path to the team trophies CSV file
        teams_columns: Dictionary with column names and types for team history (optional)
        verbose: Print debugging information
        
    Returns:
        DataFrame (df_matches) enriched with ranking and team history columns
    """
    
    if verbose:
        print("[PARTICIPATION] Updating season participation...")
        print(f"[PARTICIPATION] Country: {country}")
    
    # Read or create trophies CSV
    if not os.path.exists(trophies_csv_path):
        if verbose:
            print(f"[PARTICIPATION] Creating new trophies CSV at {trophies_csv_path}")
        df_trophies = pd.DataFrame(columns=['name', 'country', 'first_place_league', 
                                            'second_place_league', 'years_total_league',
                                            'years_consecutive_league', 'first_place_cup',
                                            'second_place_cup', 'first_place_supercup',
                                            'second_place_supercup'])
        os.makedirs(os.path.dirname(trophies_csv_path), exist_ok=True)
    else:
        df_trophies = pd.read_csv(trophies_csv_path, encoding='utf-8')
    
    # Ensure required columns exist
    for col in ['country', 'years_total_league', 'years_consecutive_league', 
                'first_place_league', 'second_place_league', 'first_place_cup',
                'second_place_cup', 'first_place_supercup', 'second_place_supercup']:
        if col == 'country':
            if col not in df_trophies.columns:
                df_trophies[col] = ''
        else:
            if col not in df_trophies.columns:
                df_trophies[col] = 0
    
    # Get unique teams from matches (check both home_team and away_team columns)
    participating_teams = set()
    
    if 'home_team' in df_matches.columns:
        participating_teams.update(df_matches['home_team'].dropna().unique())
    if 'away_team' in df_matches.columns:
        participating_teams.update(df_matches['away_team'].dropna().unique())
    if 'home_team_name' in df_matches.columns:
        participating_teams.update(df_matches['home_team_name'].dropna().unique())
    if 'away_team_name' in df_matches.columns:
        participating_teams.update(df_matches['away_team_name'].dropna().unique())
    
    if verbose:
        print(f"[PARTICIPATION] Found {len(participating_teams)} participating teams")
    
    # Filter teams from this country
    df_country = df_trophies[df_trophies['country'] == country].copy()
    
    if verbose:
        print(f"[PARTICIPATION] Found {len(df_country)} teams from {country} in trophies CSV")
    
    # Update participating teams
    for team in participating_teams:
        if team in df_trophies['name'].values:
            # Increment years_total_league
            df_trophies.loc[df_trophies['name'] == team, 'years_total_league'] += 1
            
            # Increment years_consecutive_league
            df_trophies.loc[df_trophies['name'] == team, 'years_consecutive_league'] += 1
            
            if verbose:
                total = df_trophies.loc[df_trophies['name'] == team, 'years_total_league'].iloc[0]
                consecutive = df_trophies.loc[df_trophies['name'] == team, 'years_consecutive_league'].iloc[0]
                print(f"[PARTICIPATION] {team}: total={total}, consecutive={consecutive}")
        else:
            if verbose:
                print(f"[PARTICIPATION] Warning: {team} not found in trophies CSV")
    
    # Reset consecutive years for non-participating teams from this country
    non_participating = df_country[~df_country['name'].isin(participating_teams)]['name']
    
    for team in non_participating:
        df_trophies.loc[df_trophies['name'] == team, 'years_consecutive_league'] = 0
        if verbose:
            print(f"[PARTICIPATION] {team}: Reset consecutive years to 0 (not participating)")
    
    # =========================================================================
    # ASK FOR CUP AND SUPERCUP WINNERS
    # =========================================================================
    
    # Get all teams from this country
    country_teams = df_trophies[df_trophies['country'] == country]['name'].tolist()
    
    if country_teams:
        print(f"\n{'='*60}")
        print(f"TEAMS FROM {country.upper()}")
        print(f"{'='*60}\n")
        
        # Create team list with numbers
        team_dict = {}
        for i, team_name in enumerate(sorted(country_teams), start=1):
            team_dict[i] = team_name
            print(f"  {i}. {team_name}")
        
        print(f"\n{'='*60}")
        
        # =====================================================================
        # CUP WINNER AND RUNNER-UP
        # =====================================================================
        print(f"\n--- NATIONAL CUP ---\n")
        
        # Ask for cup winner
        while True:
            try:
                winner_input = input("Enter number of CUP WINNER (or press Enter to skip): ").strip()
                if winner_input == '':
                    cup_winner = None
                    break
                winner_num = int(winner_input)
                if winner_num in team_dict:
                    cup_winner = team_dict[winner_num]
                    print(f"✓ Cup winner: {cup_winner}")
                    break
                else:
                    print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        
        # Ask for cup runner-up
        cup_runner_up = None
        if cup_winner:
            while True:
                try:
                    runner_input = input("Enter number of CUP RUNNER-UP (or press Enter to skip): ").strip()
                    if runner_input == '':
                        break
                    runner_num = int(runner_input)
                    if runner_num in team_dict:
                        if team_dict[runner_num] == cup_winner:
                            print("Runner-up cannot be the same as winner. Please choose another team.")
                            continue
                        cup_runner_up = team_dict[runner_num]
                        print(f"✓ Cup runner-up: {cup_runner_up}")
                        break
                    else:
                        print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
        
        # Update cup trophies
        if cup_winner:
            df_trophies.loc[df_trophies['name'] == cup_winner, 'first_place_cup'] += 1
            print(f"\n[TROPHIES] {cup_winner}: first_place_cup +1")
        
        if cup_runner_up:
            df_trophies.loc[df_trophies['name'] == cup_runner_up, 'second_place_cup'] += 1
            print(f"[TROPHIES] {cup_runner_up}: second_place_cup +1")
        
        # =====================================================================
        # SUPERCUP WINNER AND RUNNER-UP
        # =====================================================================
        print(f"\n--- SUPERCUP ---\n")
        
        # Ask for supercup winner
        while True:
            try:
                winner_input = input("Enter number of SUPERCUP WINNER (or press Enter to skip): ").strip()
                if winner_input == '':
                    supercup_winner = None
                    break
                winner_num = int(winner_input)
                if winner_num in team_dict:
                    supercup_winner = team_dict[winner_num]
                    print(f"✓ Supercup winner: {supercup_winner}")
                    break
                else:
                    print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        
        # Ask for supercup runner-up
        supercup_runner_up = None
        if supercup_winner:
            while True:
                try:
                    runner_input = input("Enter number of SUPERCUP RUNNER-UP (or press Enter to skip): ").strip()
                    if runner_input == '':
                        break
                    runner_num = int(runner_input)
                    if runner_num in team_dict:
                        if team_dict[runner_num] == supercup_winner:
                            print("Runner-up cannot be the same as winner. Please choose another team.")
                            continue
                        supercup_runner_up = team_dict[runner_num]
                        print(f"✓ Supercup runner-up: {supercup_runner_up}")
                        break
                    else:
                        print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
        
        # Update supercup trophies
        if supercup_winner:
            df_trophies.loc[df_trophies['name'] == supercup_winner, 'first_place_supercup'] += 1
            print(f"\n[TROPHIES] {supercup_winner}: first_place_supercup +1")
        
        if supercup_runner_up:
            df_trophies.loc[df_trophies['name'] == supercup_runner_up, 'second_place_supercup'] += 1
            print(f"[TROPHIES] {supercup_runner_up}: second_place_supercup +1")
        
        print(f"\n{'='*60}\n")
    
    # Save updated trophies CSV
    df_trophies.to_csv(trophies_csv_path, index=False, encoding='utf-8')
    
    if verbose:
        print(f"[PARTICIPATION] Updated participation saved to {trophies_csv_path}")
    
    # Create gameweek 0 ranking based on trophy history
    df_participating = df_trophies[df_trophies['name'].isin(participating_teams)].copy()
    
    # Sort by trophy criteria to determine ranking
    # Priority: 1st place > 2nd place > total years > consecutive years
    df_participating = df_participating.sort_values(
        by=['first_place_league', 'second_place_league', 'years_total_league', 'years_consecutive_league'],
        ascending=[False, False, False, False]
    ).reset_index(drop=True)
    
    # Create ranking DataFrame
    df_ranking = pd.DataFrame({
        'team_name': df_participating['name'].values,
        'team_rank': range(1, len(df_participating) + 1),
        'matchs_played': 0,
        'matchs_won': 0,
        'matchs_drawn': 0,
        'matchs_lost': 0,
        'team_goals_for': 0,
        'team_goals_against': 0,
        'team_goals_difference': 0,
        'team_points': 0
    })
    
    if verbose:
        print(f"\n[PARTICIPATION] Gameweek 0 ranking created:")
        print(df_ranking[['team_rank', 'team_name']].to_string(index=False))
    
    # Enrich df_matches with ranking data
    df_matches_enriched = df_matches.copy()
    
    # Determine which column names to use for merging
    home_col = 'home_team' if 'home_team' in df_matches.columns else 'home_team_name'
    away_col = 'away_team' if 'away_team' in df_matches.columns else 'away_team_name'
    
    # Merge home team ranking
    df_matches_enriched = df_matches_enriched.merge(
        df_ranking[['team_name', 'team_rank', 'matchs_played', 'matchs_won', 'matchs_drawn',
                   'matchs_lost', 'team_goals_for', 'team_goals_against', 
                   'team_goals_difference', 'team_points']],
        left_on=home_col,
        right_on='team_name',
        how='left',
        suffixes=('', '_home')
    )
    
    # Rename home team columns
    df_matches_enriched.rename(columns={
        'team_rank': 'home_team_rank',
        'matchs_played': 'home_matchs_played',
        'matchs_won': 'home_matchs_won',
        'matchs_drawn': 'home_matchs_drawn',
        'matchs_lost': 'home_matchs_lost',
        'team_goals_for': 'home_team_goals_for',
        'team_goals_against': 'home_team_goals_against',
        'team_goals_difference': 'home_team_goals_difference',
        'team_points': 'home_team_points'
    }, inplace=True)
    
    # Drop temporary column
    df_matches_enriched.drop(columns=['team_name'], inplace=True, errors='ignore')
    
    # Merge away team ranking
    df_matches_enriched = df_matches_enriched.merge(
        df_ranking[['team_name', 'team_rank', 'matchs_played', 'matchs_won', 'matchs_drawn',
                   'matchs_lost', 'team_goals_for', 'team_goals_against', 
                   'team_goals_difference', 'team_points']],
        left_on=away_col,
        right_on='team_name',
        how='left',
        suffixes=('', '_away')
    )
    
    # Rename away team columns
    df_matches_enriched.rename(columns={
        'team_rank': 'away_team_rank',
        'matchs_played': 'away_matchs_played',
        'matchs_won': 'away_matchs_won',
        'matchs_drawn': 'away_matchs_drawn',
        'matchs_lost': 'away_matchs_lost',
        'team_goals_for': 'away_team_goals_for',
        'team_goals_against': 'away_team_goals_against',
        'team_goals_difference': 'away_team_goals_difference',
        'team_points': 'away_team_points'
    }, inplace=True)
    
    # Drop temporary column
    df_matches_enriched.drop(columns=['team_name'], inplace=True, errors='ignore')
    
    if verbose:
        print(f"\n[PARTICIPATION] Enriched df_matches with ranking columns")
        print(f"[PARTICIPATION] Added home/away columns: team_rank, matchs_played, matchs_won, etc.")
    
    # Enrich with team history if teams_columns provided
    if teams_columns:
        if verbose:
            print(f"\n[PARTICIPATION] Enriching with team history...")
        
        df_matches_enriched = enrich_with_team_history(
            df=df_matches_enriched,
            teams_columns=teams_columns,
            csv_path=trophies_csv_path,
            country=country
        )
        
        if verbose:
            print(f"[PARTICIPATION] Team history enrichment complete")
    
    if verbose:
        print(f"[PARTICIPATION] Final shape: {df_matches_enriched.shape}")
    
    return df_matches_enriched

def update_european_season_participation(
    df_matches: pd.DataFrame,
    competition: str,
    trophies_csv_path: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Update team participation stats for European competitions.
    
    For teams participating in this European competition (present in df_matches):
    - Increments years_total_europe by 1
    - Increments years_consecutive_europe by 1
    
    For teams NOT participating:
    - Resets years_consecutive_europe to 0
    
    If competition is 'uefa_champions_league', asks for European Supercup winner/runner-up.
    
    Then, for each "minor" country (not in major leagues), asks about:
    - Local league winner/runner-up
    - Local cup winner/runner-up
    - Local supercup winner/runner-up
    - Which teams will participate in first division next season
    
    Args:
        df_matches: DataFrame with matches (must have home_team_name and/or away_team_name columns)
        competition: Competition name (e.g., 'uefa_champions_league', 'uefa_europa_league')
        trophies_csv_path: Path to the team trophies CSV file
        verbose: Print debugging information
        
    Returns:
        DataFrame (df_matches unchanged, as no ranking is created for European competitions)
    """
    
    if verbose:
        print(f"[EURO PARTICIPATION] Updating European season participation...")
        print(f"[EURO PARTICIPATION] Competition: {competition}")
    
    # Read or create trophies CSV
    if not os.path.exists(trophies_csv_path):
        if verbose:
            print(f"[EURO PARTICIPATION] Creating new trophies CSV at {trophies_csv_path}")
        df_trophies = pd.DataFrame(columns=[
            'name', 'country', 
            'first_place_league', 'second_place_league', 'years_total_league', 'years_consecutive_league',
            'first_place_cup', 'second_place_cup',
            'first_place_supercup', 'second_place_supercup',
            'first_place_europe_1', 'second_place_europe_1',
            'first_place_europe_2', 'second_place_europe_2',
            'first_place_europe_3', 'second_place_europe_3',
            'first_place_europe_supercup', 'second_place_europe_supercup',
            'years_total_europe', 'years_consecutive_europe'
        ])
        os.makedirs(os.path.dirname(trophies_csv_path), exist_ok=True)
    else:
        df_trophies = pd.read_csv(trophies_csv_path, encoding='utf-8')
    
    # Ensure required columns exist
    required_cols = [
        'country', 'years_total_europe', 'years_consecutive_europe',
        'first_place_europe_supercup', 'second_place_europe_supercup',
        'first_place_league', 'second_place_league', 'years_total_league', 'years_consecutive_league',
        'first_place_cup', 'second_place_cup',
        'first_place_supercup', 'second_place_supercup'
    ]
    
    for col in required_cols:
        if col not in df_trophies.columns:
            if col == 'country':
                df_trophies[col] = ''
            else:
                df_trophies[col] = 0
    
    # Get unique teams from matches
    participating_teams = set()
    
    if 'home_team' in df_matches.columns:
        participating_teams.update(df_matches['home_team'].dropna().unique())
    if 'away_team' in df_matches.columns:
        participating_teams.update(df_matches['away_team'].dropna().unique())
    if 'home_team_name' in df_matches.columns:
        participating_teams.update(df_matches['home_team_name'].dropna().unique())
    if 'away_team_name' in df_matches.columns:
        participating_teams.update(df_matches['away_team_name'].dropna().unique())
    
    if verbose:
        print(f"[EURO PARTICIPATION] Found {len(participating_teams)} participating teams")
    
    # Update participating teams - increment European participation
    for team in participating_teams:
        if team in df_trophies['name'].values:
            # Increment years_total_europe
            df_trophies.loc[df_trophies['name'] == team, 'years_total_europe'] += 1
            
            # Increment years_consecutive_europe
            df_trophies.loc[df_trophies['name'] == team, 'years_consecutive_europe'] += 1
            
            if verbose:
                total = df_trophies.loc[df_trophies['name'] == team, 'years_total_europe'].iloc[0]
                consecutive = df_trophies.loc[df_trophies['name'] == team, 'years_consecutive_europe'].iloc[0]
                print(f"[EURO PARTICIPATION] {team}: total_europe={total}, consecutive_europe={consecutive}")
        else:
            if verbose:
                print(f"[EURO PARTICIPATION] Warning: {team} not found in trophies CSV")
    
    # Reset consecutive years for non-participating teams
    # (All teams that exist in trophies CSV but are not in this competition)
    non_participating = df_trophies[~df_trophies['name'].isin(participating_teams)]['name']
    
    for team in non_participating:
        df_trophies.loc[df_trophies['name'] == team, 'years_consecutive_europe'] = 0
        if verbose:
            print(f"[EURO PARTICIPATION] {team}: Reset consecutive_europe to 0 (not participating)")
    
    # =========================================================================
    # ASK FOR EUROPEAN SUPERCUP (only if Champions League)
    # =========================================================================
    
    if competition == 'uefa_champions_league':
        print(f"\n{'='*60}")
        print(f"UEFA CHAMPIONS LEAGUE - EUROPEAN SUPERCUP")
        print(f"{'='*60}\n")
        
        # Get all teams (from any country)
        all_teams = df_trophies['name'].tolist()
        
        if all_teams:
            # Create team list with numbers
            team_dict = {}
            for i, team_name in enumerate(sorted(all_teams), start=1):
                team_dict[i] = team_name
                print(f"  {i}. {team_name}")
            
            print(f"\n{'='*60}")
            print(f"\n--- EUROPEAN SUPERCUP ---\n")
            
            # Ask for supercup winner
            while True:
                try:
                    winner_input = input("Enter number of EUROPEAN SUPERCUP WINNER (or press Enter to skip): ").strip()
                    if winner_input == '':
                        supercup_winner = None
                        break
                    winner_num = int(winner_input)
                    if winner_num in team_dict:
                        supercup_winner = team_dict[winner_num]
                        print(f"✓ European Supercup winner: {supercup_winner}")
                        break
                    else:
                        print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            
            # Ask for supercup runner-up
            supercup_runner_up = None
            if supercup_winner:
                while True:
                    try:
                        runner_input = input("Enter number of EUROPEAN SUPERCUP RUNNER-UP (or press Enter to skip): ").strip()
                        if runner_input == '':
                            break
                        runner_num = int(runner_input)
                        if runner_num in team_dict:
                            if team_dict[runner_num] == supercup_winner:
                                print("Runner-up cannot be the same as winner. Please choose another team.")
                                continue
                            supercup_runner_up = team_dict[runner_num]
                            print(f"✓ European Supercup runner-up: {supercup_runner_up}")
                            break
                        else:
                            print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
            
            # Update supercup trophies
            if supercup_winner:
                df_trophies.loc[df_trophies['name'] == supercup_winner, 'first_place_europe_supercup'] += 1
                print(f"\n[TROPHIES] {supercup_winner}: first_place_europe_supercup +1")
            
            if supercup_runner_up:
                df_trophies.loc[df_trophies['name'] == supercup_runner_up, 'second_place_europe_supercup'] += 1
                print(f"[TROPHIES] {supercup_runner_up}: second_place_europe_supercup +1")
            
            print(f"\n{'='*60}\n")
    
    # =========================================================================
    # PROCESS MINOR COUNTRIES (not in top leagues)
    # =========================================================================
    
    major_countries = {'portugal', 'spain', 'france', 'italy', 'england', 'germany'}
    
    # Get all unique countries from trophies CSV
    all_countries = df_trophies['country'].dropna().unique()
    minor_countries = [c for c in all_countries if c.lower() not in major_countries and c != '']
    
    if minor_countries:
        print(f"\n{'='*60}")
        print(f"MINOR COUNTRIES - LOCAL LEAGUE UPDATES")
        print(f"{'='*60}\n")
        print(f"Found {len(minor_countries)} minor countries: {sorted(minor_countries)}\n")
        
        for country in sorted(minor_countries):
            print(f"\n{'='*60}")
            print(f"COUNTRY: {country.upper()}")
            print(f"{'='*60}\n")
            
            # Get teams from this country
            country_teams = df_trophies[df_trophies['country'] == country]['name'].tolist()
            
            if not country_teams:
                print(f"No teams found for {country}, skipping...")
                continue
            
            # Create team list with numbers
            team_dict = {}
            for i, team_name in enumerate(sorted(country_teams), start=1):
                team_dict[i] = team_name
                print(f"  {i}. {team_name}")
            
            print(f"\n{'='*60}")
            
            # =================================================================
            # LOCAL LEAGUE WINNER AND RUNNER-UP
            # =================================================================
            print(f"\n--- LOCAL LEAGUE ({country}) ---\n")
            
            league_winner = None
            league_runner_up = None
            
            while True:
                try:
                    winner_input = input("Enter number of LOCAL LEAGUE WINNER (or press Enter to skip): ").strip()
                    if winner_input == '':
                        break
                    winner_num = int(winner_input)
                    if winner_num in team_dict:
                        league_winner = team_dict[winner_num]
                        print(f"✓ League winner: {league_winner}")
                        break
                    else:
                        print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            
            if league_winner:
                while True:
                    try:
                        runner_input = input("Enter number of LOCAL LEAGUE RUNNER-UP (or press Enter to skip): ").strip()
                        if runner_input == '':
                            break
                        runner_num = int(runner_input)
                        if runner_num in team_dict:
                            if team_dict[runner_num] == league_winner:
                                print("Runner-up cannot be the same as winner. Please choose another team.")
                                continue
                            league_runner_up = team_dict[runner_num]
                            print(f"✓ League runner-up: {league_runner_up}")
                            break
                        else:
                            print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
            
            # Update league trophies
            if league_winner:
                df_trophies.loc[df_trophies['name'] == league_winner, 'first_place_league'] += 1
                print(f"\n[TROPHIES] {league_winner}: first_place_league +1")
            
            if league_runner_up:
                df_trophies.loc[df_trophies['name'] == league_runner_up, 'second_place_league'] += 1
                print(f"[TROPHIES] {league_runner_up}: second_place_league +1")
            
            # =================================================================
            # LOCAL CUP WINNER AND RUNNER-UP
            # =================================================================
            print(f"\n--- LOCAL CUP ({country}) ---\n")
            
            cup_winner = None
            cup_runner_up = None
            
            while True:
                try:
                    winner_input = input("Enter number of LOCAL CUP WINNER (or press Enter to skip): ").strip()
                    if winner_input == '':
                        break
                    winner_num = int(winner_input)
                    if winner_num in team_dict:
                        cup_winner = team_dict[winner_num]
                        print(f"✓ Cup winner: {cup_winner}")
                        break
                    else:
                        print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            
            if cup_winner:
                while True:
                    try:
                        runner_input = input("Enter number of LOCAL CUP RUNNER-UP (or press Enter to skip): ").strip()
                        if runner_input == '':
                            break
                        runner_num = int(runner_input)
                        if runner_num in team_dict:
                            if team_dict[runner_num] == cup_winner:
                                print("Runner-up cannot be the same as winner. Please choose another team.")
                                continue
                            cup_runner_up = team_dict[runner_num]
                            print(f"✓ Cup runner-up: {cup_runner_up}")
                            break
                        else:
                            print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
            
            # Update cup trophies
            if cup_winner:
                df_trophies.loc[df_trophies['name'] == cup_winner, 'first_place_cup'] += 1
                print(f"\n[TROPHIES] {cup_winner}: first_place_cup +1")
            
            if cup_runner_up:
                df_trophies.loc[df_trophies['name'] == cup_runner_up, 'second_place_cup'] += 1
                print(f"[TROPHIES] {cup_runner_up}: second_place_cup +1")
            
            # =================================================================
            # LOCAL SUPERCUP WINNER AND RUNNER-UP
            # =================================================================
            print(f"\n--- LOCAL SUPERCUP ({country}) ---\n")
            
            supercup_winner = None
            supercup_runner_up = None
            
            while True:
                try:
                    winner_input = input("Enter number of LOCAL SUPERCUP WINNER (or press Enter to skip): ").strip()
                    if winner_input == '':
                        break
                    winner_num = int(winner_input)
                    if winner_num in team_dict:
                        supercup_winner = team_dict[winner_num]
                        print(f"✓ Supercup winner: {supercup_winner}")
                        break
                    else:
                        print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            
            if supercup_winner:
                while True:
                    try:
                        runner_input = input("Enter number of LOCAL SUPERCUP RUNNER-UP (or press Enter to skip): ").strip()
                        if runner_input == '':
                            break
                        runner_num = int(runner_input)
                        if runner_num in team_dict:
                            if team_dict[runner_num] == supercup_winner:
                                print("Runner-up cannot be the same as winner. Please choose another team.")
                                continue
                            supercup_runner_up = team_dict[runner_num]
                            print(f"✓ Supercup runner-up: {supercup_runner_up}")
                            break
                        else:
                            print(f"Invalid number. Please enter a number between 1 and {len(team_dict)}")
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
            
            # Update supercup trophies
            if supercup_winner:
                df_trophies.loc[df_trophies['name'] == supercup_winner, 'first_place_supercup'] += 1
                print(f"\n[TROPHIES] {supercup_winner}: first_place_supercup +1")
            
            if supercup_runner_up:
                df_trophies.loc[df_trophies['name'] == supercup_runner_up, 'second_place_supercup'] += 1
                print(f"[TROPHIES] {supercup_runner_up}: second_place_supercup +1")
            
            # =================================================================
            # FIRST DIVISION PARTICIPATION FOR NEXT SEASON
            # =================================================================
            print(f"\n--- FIRST DIVISION PARTICIPATION ({country}) ---\n")
            print("Enter the numbers of teams that will participate in first division next season.")
            print("Enter numbers separated by commas (e.g., 1,3,5,8) or press Enter when done:\n")
            
            first_division_teams = []
            
            while True:
                try:
                    teams_input = input("Teams in first division (comma-separated numbers): ").strip()
                    if teams_input == '':
                        break
                    
                    team_nums = [int(x.strip()) for x in teams_input.split(',')]
                    
                    # Validate all numbers
                    valid = True
                    for num in team_nums:
                        if num not in team_dict:
                            print(f"Invalid number: {num}. Please use numbers between 1 and {len(team_dict)}")
                            valid = False
                            break
                    
                    if valid:
                        first_division_teams = [team_dict[num] for num in team_nums]
                        print(f"\n✓ First division teams ({len(first_division_teams)}):")
                        for team in first_division_teams:
                            print(f"  - {team}")
                        break
                        
                except ValueError:
                    print("Invalid input. Please enter comma-separated numbers.")
            
            # Update years_total_league and years_consecutive_league for participating teams
            for team in country_teams:
                if team in first_division_teams:
                    # Increment participation
                    df_trophies.loc[df_trophies['name'] == team, 'years_total_league'] += 1
                    df_trophies.loc[df_trophies['name'] == team, 'years_consecutive_league'] += 1
                    print(f"[TROPHIES] {team}: years_total_league +1, years_consecutive_league +1")
                else:
                    # Reset consecutive years
                    df_trophies.loc[df_trophies['name'] == team, 'years_consecutive_league'] = 0
                    print(f"[TROPHIES] {team}: years_consecutive_league reset to 0")
        
        print(f"\n{'='*60}\n")
    
    # Save updated trophies CSV
    df_trophies.to_csv(trophies_csv_path, index=False, encoding='utf-8')
    
    if verbose:
        print(f"[EURO PARTICIPATION] Updated participation saved to {trophies_csv_path}")
    
    # Return df_matches unchanged (no ranking created for European competitions)
    return df_matches

def add_team_countries(
    df_matches: pd.DataFrame,
    teams_path: str,
    comp_type: str,
    comp_country: str,
    comp_name: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Add team country columns and competition info to matches DataFrame.
    
    Looks up each team in the teams CSV and adds their country to the DataFrame.
    Also adds competition type, country, and name.
    
    Args:
        df_matches: DataFrame with matches (must have home_team_name and away_team_name columns)
        teams_path: Path to teams CSV file (must have 'name' and 'country' columns)
        comp_type: Competition type (e.g., 'league', 'cup', 'european')
        comp_country: Competition country (e.g., 'spain', 'europe')
        comp_name: Competition name (e.g., 'liga', 'uefa_champions_league')
        verbose: Print debugging information
        
    Returns:
        DataFrame with added columns: 
        - home_team_country, away_team_country
        - competition_type, competition_country, competition_name
    """
    
    if df_matches.empty:
        print("[COUNTRIES] Empty DataFrame provided, returning as is")
        return df_matches
    
    if verbose:
        print(f"\n[COUNTRIES] Adding team countries and competition info...")
        print(f"[COUNTRIES] Teams CSV: {teams_path}")
        print(f"[COUNTRIES] Competition: {comp_name} ({comp_type}, {comp_country})")
    
    # Read teams CSV
    if not os.path.exists(teams_path):
        print(f"[COUNTRIES] ERROR: Teams CSV not found at {teams_path}")
        raise FileNotFoundError(f"Teams CSV not found: {teams_path}")
    
    df_teams = pd.read_csv(teams_path, encoding='utf-8')
    
    if 'name' not in df_teams.columns or 'country' not in df_teams.columns:
        print(f"[COUNTRIES] ERROR: Teams CSV must have 'name' and 'country' columns")
        raise ValueError("Teams CSV must have 'name' and 'country' columns")
    
    if verbose:
        print(f"[COUNTRIES] Loaded {len(df_teams)} teams from CSV")
    
    # Make a copy to avoid modifying original
    df_result = df_matches.copy()
    
    # Check required columns
    if 'home_team_name' not in df_result.columns or 'away_team_name' not in df_result.columns:
        print(f"[COUNTRIES] ERROR: DataFrame must have 'home_team_name' and 'away_team_name' columns")
        raise ValueError("DataFrame must have 'home_team_name' and 'away_team_name' columns")
    
    # Extract only name and country from teams
    df_teams_lookup = df_teams[['name', 'country']].copy()
    
    # Merge home team country
    df_result = df_result.merge(
        df_teams_lookup,
        left_on='home_team_name',
        right_on='name',
        how='left',
        suffixes=('', '_home')
    )
    
    # Rename to home_team_country
    df_result.rename(columns={'country': 'home_team_country'}, inplace=True)
    
    # Drop temporary name column
    df_result.drop(columns=['name'], inplace=True, errors='ignore')
    
    # Merge away team country
    df_result = df_result.merge(
        df_teams_lookup,
        left_on='away_team_name',
        right_on='name',
        how='left',
        suffixes=('', '_away')
    )
    
    # Rename to away_team_country
    df_result.rename(columns={'country': 'away_team_country'}, inplace=True)
    
    # Drop temporary name column
    df_result.drop(columns=['name'], inplace=True, errors='ignore')
    
    # Add competition information
    df_result['competition_type'] = comp_type
    df_result['competition_country'] = comp_country
    df_result['competition_name'] = comp_name
    
    if verbose:
        # Check for missing countries
        missing_home = df_result['home_team_country'].isna().sum()
        missing_away = df_result['away_team_country'].isna().sum()
        
        print(f"[COUNTRIES] Countries added successfully")
        print(f"[COUNTRIES] Missing home countries: {missing_home}/{len(df_result)}")
        print(f"[COUNTRIES] Missing away countries: {missing_away}/{len(df_result)}")
        
        if missing_home > 0:
            missing_teams = df_result[df_result['home_team_country'].isna()]['home_team_name'].unique()
            print(f"[COUNTRIES] Home teams not found: {list(missing_teams)}")
        
        if missing_away > 0:
            missing_teams = df_result[df_result['away_team_country'].isna()]['away_team_name'].unique()
            print(f"[COUNTRIES] Away teams not found: {list(missing_teams)}")
        
        print(f"[COUNTRIES] Competition info added to all {len(df_result)} matches")
    
    return df_result

def filter_matches_by_country_and_history(
    df_matches: pd.DataFrame,
    past_matches: pd.DataFrame,
    comp_name: str,
    minimum_matches: int = 5,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Filter matches based on team countries and historical match count.
    
    First filters out matches where either team is NOT from a major country.
    Then filters matches where teams don't have minimum historical matches in the competition.
    
    Args:
        df_matches: DataFrame with matches to filter
        past_matches: DataFrame with historical matches
        comp_name: Competition name to filter by
        minimum_matches: Minimum number of historical matches required (default: 5)
        verbose: Print debugging information
        
    Returns:
        Filtered DataFrame
    """
    
    if df_matches.empty:
        print("[FILTER] Empty DataFrame provided, returning as is")
        return df_matches
    
    if verbose:
        print(f"\n[FILTER] ========== Starting match filtering ==========")
        print(f"[FILTER] Initial matches: {len(df_matches)}")
        print(f"[FILTER] Competition: {comp_name}")
        print(f"[FILTER] Minimum matches required: {minimum_matches}")
    
    # Make a copy to avoid modifying original
    df_result = df_matches.copy()
    
    # =========================================================================
    # STEP 1: Filter by major countries
    # =========================================================================
    major_countries = {'portugal', 'spain', 'france', 'italy', 'england', 'germany'}
    
    if 'home_team_country' not in df_result.columns or 'away_team_country' not in df_result.columns:
        print("[FILTER] ERROR: DataFrame must have 'home_team_country' and 'away_team_country' columns")
        raise ValueError("DataFrame must have 'home_team_country' and 'away_team_country' columns")
    
    # Count before filtering
    initial_count = len(df_result)
    
    # Filter: keep only matches where BOTH teams are from major countries
    mask_major_countries = (
        df_result['home_team_country'].str.lower().isin(major_countries) &
        df_result['away_team_country'].str.lower().isin(major_countries)
    )
    
    df_result = df_result[mask_major_countries].reset_index(drop=True)
    
    filtered_by_country = initial_count - len(df_result)
    
    if verbose:
        print(f"\n[FILTER] Step 1: Filter by major countries")
        print(f"[FILTER] Major countries: {sorted(major_countries)}")
        print(f"[FILTER] Matches removed (non-major country): {filtered_by_country}")
        print(f"[FILTER] Matches remaining: {len(df_result)}")
    
    if df_result.empty:
        print("[FILTER] No matches remaining after country filter")
        return df_result
    
    # =========================================================================
    # STEP 2: Filter by historical match count
    # =========================================================================
    
    if verbose:
        print(f"\n[FILTER] Step 2: Filter by historical match count")
    
    # Required columns in past_matches
    required_cols = ['competition', 'home_team_name', 'away_team_name']
    missing_cols = [col for col in required_cols if col not in past_matches.columns]
    
    if missing_cols:
        print(f"[FILTER] ERROR: past_matches missing columns: {missing_cols}")
        raise ValueError(f"past_matches must have columns: {required_cols}")
    
    # Filter historical matches for the same competition
    past_matches_comp = past_matches[past_matches["competition"] == comp_name].copy()
    
    if verbose:
        print(f"[FILTER] Historical matches in {comp_name}: {len(past_matches_comp)}")
    
    if past_matches_comp.empty:
        print(f"[FILTER] WARNING: No historical matches found for competition '{comp_name}'")
        print(f"[FILTER] All matches will be filtered out (no historical data)")
        return pd.DataFrame()
    
    # Number of matches played as HOME by each team in this competition
    home_counts = past_matches_comp.groupby("home_team_name").size()
    
    # Number of matches played as AWAY by each team in this competition
    away_counts = past_matches_comp.groupby("away_team_name").size()
    
    if verbose:
        print(f"[FILTER] Unique home teams with history: {len(home_counts)}")
        print(f"[FILTER] Unique away teams with history: {len(away_counts)}")
    
    # For each future match, how many historical matches has the home team played as home?
    df_result["home_past_home_matches"] = (
        df_result["home_team_name"]
        .map(home_counts)
        .fillna(0)
        .astype(int)
    )
    
    # For each future match, how many historical matches has the away team played as away?
    df_result["away_past_away_matches"] = (
        df_result["away_team_name"]
        .map(away_counts)
        .fillna(0)
        .astype(int)
    )
    
    # Count before filtering
    before_history_filter = len(df_result)
    
    # Filter by minimum historical matches
    mask_history = (
        (df_result["home_past_home_matches"] >= minimum_matches) &
        (df_result["away_past_away_matches"] >= minimum_matches)
    )
    
    # Apply filter
    df_result = df_result[mask_history].reset_index(drop=True)
    
    filtered_by_history = before_history_filter - len(df_result)
    
    if verbose:
        print(f"[FILTER] Matches removed (insufficient history): {filtered_by_history}")
        print(f"[FILTER] Matches remaining: {len(df_result)}")
    
    # Drop temporary columns
    df_result = df_result.drop(columns=["home_past_home_matches", "away_past_away_matches"])
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    if verbose:
        total_filtered = initial_count - len(df_result)
        print(f"\n[FILTER] ========== Filtering complete ==========")
        print(f"[FILTER] Initial matches: {initial_count}")
        print(f"[FILTER] Final matches: {len(df_result)}")
        print(f"[FILTER] Total filtered: {total_filtered} ({total_filtered/initial_count*100:.1f}%)")
        print(f"[FILTER]   - By country: {filtered_by_country}")
        print(f"[FILTER]   - By history: {filtered_by_history}")
        print(f"[FILTER] ==========================================\n")
    
    return df_result

def get_initial_ranking_from_trophies(
    df_matches: pd.DataFrame,
    teams_path: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Get initial ranking stats for gameweek 1 based on trophy history.
    
    Creates a ranking based on:
    1. first_place_league (descending)
    2. second_place_league (descending)
    3. years_total_league (descending)
    4. years_consecutive_league (descending)
    
    Assigns rank and initializes all stats to 0 except team_rank.
    
    Args:
        df_matches: DataFrame with matches (must have home_team_name and away_team_name)
        teams_path: Path to teams CSV with trophy history
        verbose: Print debugging information
        
    Returns:
        DataFrame with added ranking columns (all at 0 except team_rank)
    """
    
    if df_matches.empty:
        print("[INITIAL RANK] Empty DataFrame provided, returning as is")
        return df_matches
    
    if verbose:
        print(f"\n[INITIAL RANK] Getting initial ranking from trophy history...")
        print(f"[INITIAL RANK] Teams CSV: {teams_path}")
    
    # Read teams CSV
    if not os.path.exists(teams_path):
        print(f"[INITIAL RANK] ERROR: Teams CSV not found")
        raise FileNotFoundError(f"Teams CSV not found: {teams_path}")
    
    df_teams = pd.read_csv(teams_path, encoding='utf-8')
    
    # Check required columns
    required_cols = ['name', 'first_place_league', 'second_place_league', 
                     'years_total_league', 'years_consecutive_league']
    missing = [col for col in required_cols if col not in df_teams.columns]
    
    if missing:
        print(f"[INITIAL RANK] ERROR: Teams CSV missing columns: {missing}")
        raise ValueError(f"Teams CSV must have columns: {required_cols}")
    
    # Get unique teams from matches
    all_teams = set()
    if 'home_team_name' in df_matches.columns:
        all_teams.update(df_matches['home_team_name'].dropna().unique())
    if 'away_team_name' in df_matches.columns:
        all_teams.update(df_matches['away_team_name'].dropna().unique())
    
    if verbose:
        print(f"[INITIAL RANK] Found {len(all_teams)} unique teams in matches")
    
    # Filter teams that are in matches
    df_teams_filtered = df_teams[df_teams['name'].isin(all_teams)].copy()
    
    if verbose:
        print(f"[INITIAL RANK] Found {len(df_teams_filtered)} teams in trophy history")
    
    # Sort by trophy criteria
    df_teams_filtered = df_teams_filtered.sort_values(
        by=['first_place_league', 'second_place_league', 'years_total_league', 'years_consecutive_league'],
        ascending=[False, False, False, False]
    ).reset_index(drop=True)
    
    # Create ranking
    df_teams_filtered['team_rank'] = range(1, len(df_teams_filtered) + 1)
    
    if verbose:
        print(f"\n[INITIAL RANK] Initial ranking (top 10):")
        for idx, row in df_teams_filtered.head(10).iterrows():
            print(f"  {row['team_rank']}. {row['name']}")
    
    # Create ranking dictionary with all stats at 0 except rank
    ranking_dict = {}
    for _, row in df_teams_filtered.iterrows():
        ranking_dict[row['name']] = {
            'team_rank': row['team_rank'],
            'matchs_played': 0,
            'matchs_won': 0,
            'matchs_drawn': 0,
            'matchs_lost': 0,
            'team_goals_for': 0,
            'team_goals_against': 0,
            'team_goals_difference': 0,
            'team_points': 0
        }
    
    # Make a copy of df_matches
    df_result = df_matches.copy()
    
    # Stats columns to add
    stats_columns = [
        'team_rank', 'matchs_played', 'matchs_won', 'matchs_drawn', 'matchs_lost',
        'team_goals_for', 'team_goals_against', 'team_goals_difference', 'team_points'
    ]
    
    # Add home team stats
    for col in stats_columns:
        df_result[f'home_{col}'] = df_result['home_team_name'].map(
            lambda x: ranking_dict.get(x, {}).get(col, None)
        )
    
    # Add away team stats
    for col in stats_columns:
        df_result[f'away_{col}'] = df_result['away_team_name'].map(
            lambda x: ranking_dict.get(x, {}).get(col, None)
        )
    
    if verbose:
        missing_home = df_result['home_team_rank'].isna().sum()
        missing_away = df_result['away_team_rank'].isna().sum()
        print(f"\n[INITIAL RANK] Stats added to matches")
        print(f"[INITIAL RANK] Missing home rankings: {missing_home}/{len(df_result)}")
        print(f"[INITIAL RANK] Missing away rankings: {missing_away}/{len(df_result)}")
    
    return df_result