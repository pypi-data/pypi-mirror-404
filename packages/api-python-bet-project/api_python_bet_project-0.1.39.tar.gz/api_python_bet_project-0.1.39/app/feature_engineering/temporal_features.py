import pandas as pd
import numpy as np

def add_circular_temporal_features(
    df_matches: pd.DataFrame,
    comp_type: str,
    max_gameweeks: int = 38,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Add circular temporal features using sine and cosine transformations.
    
    Transforms temporal columns into circular components:
    - day_of_week (0-6) → cos_day_of_week, sin_day_of_week
    - day_of_year (1-365/366) → cos_day_of_year, sin_day_of_year
    - hour_of_day (0-23) → cos_hour_of_day, sin_hour_of_day
    - gameweek → only for leagues (circular)
    
    For European competitions, use add_knockout_features() for gameweek encoding.
    
    Args:
        df_matches: DataFrame with temporal columns
        comp_type: Competition type ('league', 'european')
        max_gameweeks: Maximum number of gameweeks for league competitions (default: 38)
        verbose: Print debugging information
        
    Returns:
        DataFrame with added circular features
    """
    
    if df_matches.empty:
        print("[TEMPORAL] Empty DataFrame provided, returning as is")
        return df_matches
    
    if verbose:
        print(f"\n[TEMPORAL] ========== Adding circular temporal features ==========")
        print(f"[TEMPORAL] Competition type: {comp_type}")
    
    # Make a copy
    df_result = df_matches.copy()
    
    # =========================================================================
    # 1. DAY OF WEEK (0-6)
    # =========================================================================
    if 'day_of_week' in df_result.columns:
        df_result['cos_day_of_week'] = np.cos(2 * np.pi * df_result['day_of_week'] / 7.0)
        df_result['sin_day_of_week'] = np.sin(2 * np.pi * df_result['day_of_week'] / 7.0)
        
        if verbose:
            print(f"[TEMPORAL] ✓ Added: cos_day_of_week, sin_day_of_week")
    else:
        if verbose:
            print(f"[TEMPORAL] ⚠ Warning: 'day_of_week' column not found")
    
    # =========================================================================
    # 2. DAY OF YEAR (1-365/366)
    # =========================================================================
    if 'day_of_year' in df_result.columns:
        # Use 366 as max to handle leap years
        df_result['cos_day_of_year'] = np.cos(2 * np.pi * df_result['day_of_year'] / 366.0)
        df_result['sin_day_of_year'] = np.sin(2 * np.pi * df_result['day_of_year'] / 366.0)
        
        if verbose:
            print(f"[TEMPORAL] ✓ Added: cos_day_of_year, sin_day_of_year")
    else:
        if verbose:
            print(f"[TEMPORAL] ⚠ Warning: 'day_of_year' column not found")
    
    # =========================================================================
    # 3. HOUR OF DAY (0-23)
    # =========================================================================
    if 'hour_of_day' in df_result.columns:
        df_result['cos_hour_of_day'] = np.cos(2 * np.pi * df_result['hour_of_day'] / 24.0)
        df_result['sin_hour_of_day'] = np.sin(2 * np.pi * df_result['hour_of_day'] / 24.0)
        
        if verbose:
            print(f"[TEMPORAL] ✓ Added: cos_hour_of_day, sin_hour_of_day")
    else:
        if verbose:
            print(f"[TEMPORAL] ⚠ Warning: 'hour_of_day' column not found")
    
    # =========================================================================
    # 4. GAMEWEEK (only for leagues)
    # =========================================================================
    if 'gameweek' in df_result.columns:
        
        if comp_type == 'league':
            # For leagues: circular transformation (gameweek 38 is close to gameweek 1)
            df_result['cos_gameweek'] = np.cos(2 * np.pi * df_result['gameweek'] / max_gameweeks)
            df_result['sin_gameweek'] = np.sin(2 * np.pi * df_result['gameweek'] / max_gameweeks)
            
            if verbose:
                print(f"[TEMPORAL] ✓ Added: cos_gameweek, sin_gameweek (circular, max={max_gameweeks})")
        
        elif comp_type == 'european':
            if verbose:
                print(f"[TEMPORAL] ℹ European competition: Use add_knockout_features() for gameweek encoding")
        
        else:
            if verbose:
                print(f"[TEMPORAL] ℹ Unknown comp_type '{comp_type}': Gameweek encoding skipped")
    
    else:
        if verbose:
            print(f"[TEMPORAL] ⚠ Warning: 'gameweek' column not found")
    
    if verbose:
        new_cols = [col for col in df_result.columns if col not in df_matches.columns]
        print(f"\n[TEMPORAL] Total new columns added: {len(new_cols)}")
        if new_cols:
            print(f"[TEMPORAL] New columns: {new_cols}")
        print(f"[TEMPORAL] ========== Circular temporal features complete ==========\n")
    
    return df_result

def add_knockout_features(
    df_matches: pd.DataFrame,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Add knockout stage features for European competitions.
    
    Analyzes gameweek values to identify knockout rounds (after group stage).
    Play-offs (gameweek=50) are NOT considered knockout rounds.
    
    Features added:
    - is_knockout: Boolean (True if knockout round, False if group stage)
    - knockout_round: Integer (1=first knockout, 2=next, ..., N=final) or None
    - knockout_progress: Float 0-1 (0=first knockout, 1=final) or None
    - rounds_to_final: Integer (how many rounds until final) or None
    
    Knockout round detection (based on gameweek value):
    - 36: Round of 64
    - 68: Round of 32
    - 84: Round of 16
    - 92: Quarter-finals
    - 96: Semi-finals
    - 98: Final
    
    Args:
        df_matches: DataFrame with 'gameweek' column
        verbose: Print debugging information
        
    Returns:
        DataFrame with added knockout features
    """
    
    if df_matches.empty:
        print("[KNOCKOUT] Empty DataFrame provided, returning as is")
        return df_matches
    
    if verbose:
        print(f"\n[KNOCKOUT] ========== Adding knockout features ==========")
    
    # Make a copy
    df_result = df_matches.copy()
    
    # Check if gameweek column exists
    if 'gameweek' not in df_result.columns:
        print(f"[KNOCKOUT] ERROR: 'gameweek' column not found")
        raise ValueError("DataFrame must have 'gameweek' column")
    
    # =========================================================================
    # DEFINE KNOCKOUT ROUNDS
    # =========================================================================
    
    # Knockout rounds mapping: gameweek_value → round_name
    # Play-offs (50) are NOT included as they're before group stage
    knockout_gameweeks = {
        36: 'Round of 64',
        68: 'Round of 32',
        84: 'Round of 16',
        92: 'Quarter-finals',
        96: 'Semi-finals',
        98: 'Final'
    }
    
    # =========================================================================
    # IDENTIFY EXISTING KNOCKOUT ROUNDS
    # =========================================================================
    
    # Get unique gameweek values
    existing_gameweeks = df_result['gameweek'].dropna().unique()
    
    # Filter for knockout rounds only
    existing_knockouts = sorted([gw for gw in existing_gameweeks if gw in knockout_gameweeks])
    
    if not existing_knockouts:
        # No knockout rounds found (only group stage)
        df_result['is_knockout'] = False
        df_result['knockout_round'] = None
        df_result['knockout_progress'] = None
        df_result['rounds_to_final'] = None
        
        if verbose:
            print(f"[KNOCKOUT] No knockout rounds found (group stage only)")
            print(f"[KNOCKOUT] All matches marked as non-knockout")
            print(f"[KNOCKOUT] ========== Knockout features complete ==========\n")
        
        return df_result
    
    # =========================================================================
    # CREATE SEQUENTIAL MAPPING
    # =========================================================================
    
    total_knockout_rounds = len(existing_knockouts)
    
    # Create mapping: gameweek → (sequential_round_number, rounds_to_final)
    sequential_mapping = {}
    for idx, gw in enumerate(existing_knockouts, start=1):
        rounds_to_final = total_knockout_rounds - idx
        sequential_mapping[gw] = (idx, rounds_to_final)
    
    if verbose:
        print(f"[KNOCKOUT] Found {total_knockout_rounds} knockout rounds:")
        for gw in existing_knockouts:
            round_num, rtf = sequential_mapping[gw]
            round_name = knockout_gameweeks[gw]
            print(f"[KNOCKOUT]   Gameweek {gw} ({round_name}): Round {round_num}, {rtf} rounds to final")
    
    # =========================================================================
    # APPLY MAPPING TO DATAFRAME
    # =========================================================================
    
    def get_knockout_info(gameweek):
        """Get knockout information for a given gameweek value."""
        if pd.isna(gameweek):
            return False, None, None, None
        
        if gameweek in sequential_mapping:
            round_num, rounds_to_final = sequential_mapping[gameweek]
            
            # Calculate progress (0.0 to 1.0)
            if total_knockout_rounds > 1:
                progress = (round_num - 1) / (total_knockout_rounds - 1)
            else:
                progress = 1.0  # Only one knockout round (final)
            
            return True, round_num, progress, rounds_to_final
        else:
            # Group stage or other non-knockout round
            return False, None, None, None
    
    # Apply to all rows
    df_result[['is_knockout', 'knockout_round', 'knockout_progress', 'rounds_to_final']] = \
        df_result['gameweek'].apply(lambda gw: pd.Series(get_knockout_info(gw)))
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    if verbose:
        knockout_count = df_result['is_knockout'].sum()
        total_count = len(df_result)
        
        print(f"\n[KNOCKOUT] Summary:")
        print(f"[KNOCKOUT] Total matches: {total_count}")
        print(f"[KNOCKOUT] Knockout matches: {knockout_count}")
        print(f"[KNOCKOUT] Group stage matches: {total_count - knockout_count}")
        
        if knockout_count > 0:
            print(f"\n[KNOCKOUT] Knockout round distribution:")
            round_counts = df_result[df_result['is_knockout']].groupby('knockout_round').size()
            for round_num in sorted(round_counts.index):
                count = round_counts[round_num]
                # Find gameweek for this round
                gw = existing_knockouts[round_num - 1]
                round_name = knockout_gameweeks[gw]
                print(f"[KNOCKOUT]   Round {round_num} ({round_name}): {count} matches")
        
        print(f"[KNOCKOUT] ========== Knockout features complete ==========\n")
    
    return df_result