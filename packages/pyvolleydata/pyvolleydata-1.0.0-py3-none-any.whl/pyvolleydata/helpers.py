import pandas as pd
from datetime import datetime


def get_data(league, seasons, data_type):
    league_config = {
        'mlv': {'start_year': 2024, 'internal_name': 'pvf'},
        'lovb': {'start_year': 2025, 'internal_name': 'lovb'},
        'au': {'start_year': 2022, 'internal_name': 'aupvb'}
    }
    if league in league_config:
        league_start_year = league_config.get(league).get('start_year')
        league_internal_name = league_config.get(league).get('internal_name')
    
        if isinstance(seasons, int):
            seasons = [seasons]
        if isinstance(seasons, list):
            validate_seasons(seasons, league_start_year)
        elif seasons is None:
            seasons = list(range(league_start_year, datetime.now().year + 1))
        else:
            raise TypeError(f'Expected seasons to be an int, list of ints, or None, got {type(seasons).__name__}')
        base_url = "https://github.com/awosoga/volleydata/releases/download"
        df = pd.DataFrame()
        if data_type in {'pbp', 'events_log'}:
            for season in seasons:
                file_path = f"{league_internal_name}-{data_type.replace("_", "-")}/{league_internal_name}_{data_type}_{season}.csv"
                print(f"{base_url}/{file_path}")
                df = pd.concat([df, pd.read_csv(f"{base_url}/{file_path}")])
        else:
            file_path = f"{league_internal_name}-{data_type.replace("_", "-")}/{league_internal_name}_{data_type}.csv"
            df = pd.read_csv(f"{base_url}/{file_path}")
            df = df[df['season'].isin(seasons)]
    else:
        raise TypeError("league must be one of 'mlv', 'lovb', or 'au'")
    df['league'] = league
    return df


def validate_seasons(seasons, league_start_year):
    """
    Checks whether all the provided seasons are valid years and raises an error if not.

    Parameters
    ----------
    seasons: list of int
        A list of years representing seasons to validate.

    Returns
    -------
    None

    Examples
    --------
    >>> validate_seasons([2024, 2025], 2024)
    >>> validate_seasons(['2020'], 2024)  # Raises TypeError
    >>> validate_seasons([2022, 2023, 2030], 2024)  # Raises ValueError
    """
    if not isinstance(seasons, list):
        raise TypeError('Expected a list of years')
    for year in seasons:
        if not isinstance(year, int):
            raise TypeError(f'Expected an integer for year, got {type(year).__name__}')
        if year < league_start_year or year > datetime.now().year:
            raise ValueError(f'Year {year} out of valid range for this league ({league_start_year}-{datetime.now().year})')