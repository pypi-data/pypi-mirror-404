"""
Date utility functions for determining scraping date ranges.
"""

from datetime import datetime, timedelta, date
from typing import List, Tuple, Optional, Union, Set
import pandas as pd


def validate_execution_day(date_str: Optional[str] = None) -> datetime:
    """
    Validate that the execution day is Tuesday or Friday.

    Args:
        date_str: Date string in format YYYY-MM-DD. If None, uses today.

    Returns:
        datetime object of the validated date

    Raises:
        ValueError: If date is not a Tuesday (1) or Friday (4)
    """
    if date_str is None:
        execution_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        print(
            f"📅 No date provided. Using today: {execution_date.strftime('%A, %Y-%m-%d')}"
        )
    else:
        try:
            execution_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid date format: '{date_str}'. Please use YYYY-MM-DD format (e.g., '2025-10-10')"
            )

    weekday = execution_date.weekday()  # Monday = 0, Sunday = 6
    day_name = execution_date.strftime("%A")

    # Check if it's Tuesday (1) or Friday (4)
    if weekday not in [1, 4]:
        raise ValueError(
            f"Dataset update can only run on Tuesday or Friday. "
            f"Provided date is {day_name} ({execution_date.strftime('%Y-%m-%d')}). "
            f"Please provide a Tuesday or Friday date."
        )

    return execution_date


def get_previous_days(execution_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get PREVIOUS date range based on execution day (for update_dataset).

    Rules:
    - Tuesday: Get Fri, Sat, Sun, Mon (4 days BEFORE Tuesday)
    - Friday: Get Tue, Wed, Thu (3 days BEFORE Friday)

    This function is used by update_dataset to scrape matches that already happened.

    Args:
        execution_date: The validated execution date (must be Tuesday or Friday)

    Returns:
        Tuple of (start_date, end_date) for PREVIOUS matches only
    """
    weekday = execution_date.weekday()

    if weekday == 1:  # Tuesday
        # Previous: Fri, Sat, Sun, Mon (4 days before Tuesday)
        start_date = execution_date - timedelta(days=4)  # Friday
        end_date = execution_date - timedelta(days=1)  # Monday

        days = get_days_in_range(start_date, end_date)

    elif weekday == 4:  # Friday
        # Previous: Tue, Wed, Thu (3 days before Friday)
        start_date = execution_date - timedelta(days=3)  # Tuesday
        end_date = execution_date - timedelta(days=1)  # Thursday

        days = get_days_in_range(start_date, end_date)

    return days


def get_next_days(execution_date: datetime) -> Tuple[datetime, datetime]:
    """
    Get NEXT date range based on execution day (for future matches).

    Rules:
    - Tuesday: Get Tue, Wed, Thu (includes execution day + 2 days after)
    - Friday: Get Fri, Sat, Sun, Mon (includes execution day + 3 days after)

    This function is used to scrape matches that will happen in the future.

    Args:
        execution_date: The validated execution date (must be Tuesday or Friday)

    Returns:
        Tuple of (start_date, end_date) for NEXT matches only
    """
    weekday = execution_date.weekday()

    if weekday == 1:  # Tuesday
        # Next: Tue, Wed, Thu (execution day + 2 days after)
        start_date = execution_date  # Tuesday
        end_date = execution_date + timedelta(days=2)  # Thursday

        days = get_days_in_range(start_date, end_date)

    elif weekday == 4:  # Friday
        # Next: Fri, Sat, Sun, Mon (execution day + 3 days after)
        start_date = execution_date  # Friday
        end_date = execution_date + timedelta(days=3)  # Monday

        days = get_days_in_range(start_date, end_date)

    return days


def get_days_in_range(start_date: datetime, end_date: datetime) -> list:
    """
    Get list of all days in the date range.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of datetime objects for each day in range
    """
    days = []
    current = start_date
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)
    return days


def season_from_date(when: Union[str, datetime, date]) -> Tuple[str, int, int]:
    """
    Return (season_str, start_year, end_year) for a given date.

    Rules (European football typical):
      - If date is on/after Aug 1 (inclusive) -> season = year-(year+1)
      - Else (before Aug 1) -> season = (year-1)-year

    Accepts common date formats (DD/MM/YYYY, YYYY-MM-DD, etc.).
    """
    # Parse input into a date object
    if isinstance(when, str):
        formats = (
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%d/%m/%y",
            "%Y/%m/%d",
            "%d.%m.%Y",
            "%d.%m.%y",
        )
        for fmt in formats:
            try:
                d = datetime.strptime(when, fmt).date()
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unrecognized date format: {when!r}")
    elif isinstance(when, datetime):
        d = when.date()
    elif isinstance(when, date):
        d = when
    else:
        raise TypeError("Parameter 'when' must be str, datetime, or date")

    cutoff = date(d.year, 8, 1)  # Aug 1 of that year

    # Inclusive on Aug 1
    if d >= cutoff:
        start_year = d.year
    else:
        start_year = d.year - 1

    end_year = start_year + 1
    season_str = f"{start_year}-{end_year}"
    return (season_str, start_year, end_year)


def sort_by_match_datetime(
    df: pd.DataFrame,
    date_col: str = "date_of_match",
    time_col: str = "hour_of_the_match",
    inplace: bool = False,
    na_position: str = "last",
) -> pd.DataFrame:
    """
    Sort a DataFrame by date_of_match + hour_of_the_match.
    - date_of_match: flexible parse (tries standard first, then dayfirst).
    - hour_of_the_match: 'HH:MM' (24h). Invalid/missing -> 00:00.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"sort_by_match_datetime expects a pandas DataFrame, got {type(df)}. "
            f"If you have a list of dicts, wrap it with pd.DataFrame(...)."
        )

    if not inplace:
        df = df.copy()

    # Ensure required columns exist
    missing = [c for c in (date_col, time_col) if c not in df.columns]
    if missing:
        raise KeyError(
            f"Missing required columns: {missing}. Available: {list(df.columns)}"
        )

    # Parse date: try default, then dayfirst for failures
    dates = pd.to_datetime(df[date_col], errors="coerce")
    mask = dates.isna() & df[date_col].notna()
    if mask.any():
        dates.loc[mask] = pd.to_datetime(
            df.loc[mask, date_col], errors="coerce", dayfirst=True
        )

    # Parse time: 'HH:MM' preferred; fallback to generic; invalid -> 00:00
    times_raw = pd.to_datetime(df[time_col], format="%H:%M", errors="coerce")
    fallback_mask = times_raw.isna() & df[time_col].notna()
    if fallback_mask.any():
        times_raw.loc[fallback_mask] = pd.to_datetime(
            df.loc[fallback_mask, time_col], errors="coerce"
        )

    hours = times_raw.dt.hour.fillna(0).astype(int)
    minutes = times_raw.dt.minute.fillna(0).astype(int)
    tdelta = pd.to_timedelta(hours, unit="h") + pd.to_timedelta(minutes, unit="m")

    # Compose datetime and sort
    df["_match_dt"] = dates + tdelta
    df.sort_values(
        by="_match_dt", ascending=True, na_position=na_position, inplace=True
    )
    df.drop(columns="_match_dt", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def normalize_dates(
        dates_in: List[Union[str, date, pd.Timestamp, datetime]]
    ) -> Set[date]:
        """
        Normalize various date formats to a set of date objects (WITHOUT time).

        Args:
            dates_in: List of dates in various formats

        Returns:
            Set of date objects (no time component)
        """
        normalized_dates = set()

        for d in dates_in:
            try:
                # Handle datetime.date directly
                if isinstance(d, date) and not isinstance(d, (pd.Timestamp, datetime)):
                    normalized_dates.add(d)

                # Handle datetime.datetime - convert to date
                elif isinstance(d, datetime) and not isinstance(d, pd.Timestamp):
                    normalized_dates.add(d.date())

                # Handle pandas Timestamp - convert to date
                elif isinstance(d, pd.Timestamp):
                    normalized_dates.add(d.date())

                # Handle string
                elif isinstance(d, str):
                    parsed = pd.to_datetime(d, errors="raise")
                    normalized_dates.add(parsed.date())  # ← IMPORTANTE: .date()

                else:
                    print(f"Unknown date type: {type(d)} - {d}")

            except Exception as e:
                print(f"Could not parse date '{d}' (type: {type(d)}): {e}")

        return normalized_dates