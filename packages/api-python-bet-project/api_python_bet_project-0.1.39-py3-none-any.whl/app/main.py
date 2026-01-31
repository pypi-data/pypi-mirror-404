"""
Main entry point for updating the football dataset from command line.
This script orchestrates the dataset update process by calling update_dataset.py
"""

import argparse
import sys
import logging
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd

from utils.config import get_settings
from updating.update_dataset import DatasetUpdater
from predicting.predicting import Predicting

def get_tuesdays_and_fridays(start_date: str, end_date: str) -> list:
    """
    Generate all Tuesday and Friday dates between start_date and end_date.
    
    Args:
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD
    
    Returns:
        List of date strings in format YYYY-MM-DD for all Tuesdays and Fridays
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    dates = []
    current = start
    
    while current <= end:
        # 1 = Tuesday, 4 = Friday
        if current.weekday() in [1, 4]:
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return dates

def parse_season(season: str) -> tuple:
    """
    Parse season string and return start and end dates.
    
    Args:
        season: Season in format YYYY-YYYY (e.g., "2017-2018")
    
    Returns:
        Tuple of (start_date, end_date) as strings in YYYY-MM-DD format
    
    Raises:
        ValueError: If season format is invalid
    """
    try:
        years = season.split("-")
        if len(years) != 2:
            raise ValueError("Season must be in format YYYY-YYYY")
        
        start_year = int(years[0])
        end_year = int(years[1])
        
        if end_year != start_year + 1:
            raise ValueError("End year must be one year after start year")
        
        # Football season typically runs from August 1st to June 30th
        start_date = f"{start_year}-08-01"
        end_date = f"{end_year}-06-30"
        
        return start_date, end_date
    
    except Exception as e:
        raise ValueError(f"Invalid season format '{season}': {e}")

def data_update_dataset(
    competition: Optional[str] = None, date: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch latest matches (including future matches), refresh rankings/odds,
    append to dataset and build features only for those rows.

    Args:
        competition: Specific competition to update (None for all competitions)
        date: Date to process (format: YYYY-MM-DD). If None, uses today.
              Must be Tuesday or Friday.

    Returns:
        DataFrame with updated match data and features

    Raises:
        ValueError: If the date is not a Tuesday or Friday
    """
    # Get settings from configuration
    s = get_settings()

    # Initialize DatasetUpdater with settings
    calc_data = DatasetUpdater(
        features_config=s.update_features_config,
        competitions_config=s.competitions_config,
        paths=s.paths,
    )

    # Run the update
    calc_data.update_dataset(date=date, competition=competition)

    # Initialize Predicting with settings
    #calc_predicting = Predicting(
    #    features_config=s.predicting_features_config,
    #    competitions_config=s.competitions_config,
    #    paths=s.paths,
    #)

    # Run the update
    #calc_predicting.update_dataset(date=date, competition=competition)

def data_update_season(
    season: str,
    competition: Optional[str] = None,
    start_from: Optional[str] = None,
    until: Optional[str] = None
) -> None:
    """
    Update dataset for an entire football season by iterating through all
    Tuesdays and Fridays in the season.
    
    Args:
        season: Season in format YYYY-YYYY (e.g., "2017-2018")
        competition: Specific competition to update (None for all competitions)
        start_from: Optional date to start from (YYYY-MM-DD). Useful to resume
                   an interrupted update. If None, starts from beginning of season.
        until: Optional date to end at (YYYY-MM-DD). If None, goes until end of season.
    
    Raises:
        ValueError: If season format is invalid
    """
    print(f"Starting season update for {season}")
    
    # Parse season to get date range
    start_date, end_date = parse_season(season)
    
    # Override start date if start_from is provided
    if start_from:
        start_date = start_from
    
    # Override end date if until is provided
    if until:
        end_date = until
    
    # Get all Tuesdays and Fridays in the season
    dates = get_tuesdays_and_fridays(start_date, end_date)
    
    total_dates = len(dates)
    
    # Process each date
    successful = 0
    failed = 0
    failed_dates = []
    
    for idx, date in enumerate(dates, 1):
        print(f"    Starting update for date {date}")
        try:            
            # Call the update function for this specific date
            data_update_dataset(competition=competition, date=date)
            
            successful += 1
            
        except Exception as e:
            failed += 1
            failed_dates.append(date)
            print(f"Failed to process {date}: {e}")
            
            # Ask user if they want to continue
            print(f"Continue with remaining dates? (y/n): ", end='')
            response = input().lower().strip()
            if response != 'y':
                print("User chose to stop processing")
                break
    
    # Summary
    print(f"Season: {season}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Total dates: {total_dates}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed_dates:
        print(f"Failed dates: {', '.join(failed_dates)}")
        print(f"To resume from first failed date, use:")
        print(f"python main.py --season {season} --start-from {failed_dates[0]}")

def main():
    """
    Main entry point for command-line execution.
    Parses arguments and calls appropriate update function.
    """
    parser = argparse.ArgumentParser(
        description="Update football dataset with latest matches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update all competitions for today (must be Tuesday or Friday)
  python main.py
  
  # Update specific competition
  python main.py --competition spanish_league
  python main.py -c spanish_league
  
  # Update with specific date (must be Tuesday or Friday)
  python main.py --date 2025-10-10
  python main.py -d 2025-10-10
  
  # Update specific competition on specific date
  python main.py --competition spanish_league --date 2025-10-10
  python main.py -c spanish_league -d 2025-10-10
  
  # Update entire season (all Tuesdays and Fridays)
  python main.py --season 2017-2018
  python main.py -s 2017-2018
  
  # Update entire season for specific competition
  python main.py --season 2017-2018 --competition spanish_league
  python main.py -s 2017-2018 -c spanish_league
  
  # Resume season update from specific date
  python main.py --season 2017-2018 --start-from 2018-01-15
  python main.py -s 2017-2018 --start-from 2018-01-15
  
  # Update season up to specific date
  python main.py --season 2017-2018 --until 2018-01-31
  python main.py -s 2017-2018 --until 2018-01-31
  
  # Update specific date range within season
  python main.py --season 2017-2018 --start-from 2017-09-01 --until 2017-12-31
  python main.py -s 2017-2018 --start-from 2017-09-01 --until 2017-12-31
        """,
    )

    parser.add_argument(
        "--competition",
        "-c",
        type=str,
        default=None,
        help="Specific competition to update (e.g., spanish_league). If not provided, updates all competitions.",
    )

    parser.add_argument(
        "--date",
        "-d",
        type=str,
        default=None,
        help="Date to process in YYYY-MM-DD format (e.g., 2025-10-10). Must be Tuesday or Friday. If not provided, uses today.",
    )

    parser.add_argument(
        "--season",
        "-s",
        type=str,
        default=None,
        help="Season to process in YYYY-YYYY format (e.g., 2017-2018). Processes all Tuesdays and Fridays in the season.",
    )

    parser.add_argument(
        "--start-from",
        type=str,
        default=None,
        help="When using --season, start from this date (YYYY-MM-DD). Useful to resume interrupted updates.",
    )

    parser.add_argument(
        "--until",
        type=str,
        default=None,
        help="When using --season, end at this date (YYYY-MM-DD). Useful to update only part of a season.",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--list-competitions",
        action="store_true",
        help="List all available competitions and exit",
    )

    args = parser.parse_args()

    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # List competitions if requested
    if args.list_competitions:
        s = get_settings()
        for comp_name, comp_config in s.competitions_config.items():
            country = comp_config.get("country", "N/A")
            print(f"{comp_name:<30} (Country: {country})")
        return 0

    # Validate arguments
    if args.date and args.season:
        print("Error: Cannot use both --date and --season options together")
        return 1
    
    if args.start_from and not args.season:
        print("Error: --start-from can only be used with --season option")
        return 1
    
    if args.until and not args.season:
        print("Error: --until can only be used with --season option")
        return 1

    try:
        # SEASON MODE
        if args.season:
            # Run season update
            data_update_season(
                season=args.season,
                competition=args.competition,
                start_from=args.start_from,
                until=args.until
            )

            return 0

        # SINGLE DATE MODE
        else:
            # Run the update
            data_update_dataset(competition=args.competition, date=args.date)

            return 0

    except ValueError as e:
        print(f"Validation error: {e}")
        return 1

    except KeyboardInterrupt:
        print("Process interrupted by user")
        return 1

    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())