import pandas as pd
from . import helpers as h
from datetime import datetime


def load_schedule(league = None, seasons = None):
    """
    Load cleaned schedule data from the volleydata repository.
    
    Parameters
    ----------
    league : str
        A string specifying which of 'mlv', 'pvf', or 'au' to load data for.

    seasons : int, list of int, or None, optional
        Season(s) to load. By default, None loads all available seasons.
        - int : Single season year (e.g., 2025)
        - list of int : Multiple seasons (e.g., [2024, 2025])
        - None : Load all available seasons

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the schedule data for the specified seasons.

        ================================  ===========
        Column Name                        Type
        ================================  ===========
        season                             int
        date                               str
        home_team                          str
        away_team                          str
        home_team_set_wins                 int
        away_team_set_wins                 int
        result                             str
        match_id                           str
        phase                              str
        league                             str
        ================================  ===========
    
    Examples
    --------
    >>> load_schedule('lovb', 2025)
    >>> load_schedule('mlv', [2024, 2025])
    >>> load_schedule('au')
    """
    schedule = h.get_data(league, seasons, 'schedule')
    return schedule


def load_officials(league = None, seasons = None):
    """
    Load cleaned officials data from the volleydata repository.

    Parameters
    ----------
    league : str
        A string specifying which of 'mlv', 'pvf', or 'au' to load data for.

    seasons : int, list of int, or None, optional
        Season(s) to load. By default, None loads all available seasons.
        - int : Single season year (e.g., 2025)
        - list of int : Multiple seasons (e.g., [2024, 2025])
        - None : Load all available seasons

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the officials data for the specified seasons.

        ================================  ===========
        Column Name                        Type
        ================================  ===========
        match_id                           int
        season                             int
        match_datetime                     str
        officials_type                     str
        full_name                          str
        first_name                         str
        last_name                          str
        level                              str
        league                             str
        ================================  ===========
    
    Examples
    --------
    >>> load_officials('lovb', 2025)
    >>> load_officials('mlv', [2024, 2025])
    >>> load_officials('au')
    """
    officials = h.get_data(league, seasons, 'officials')
    return officials


def load_player_info(league = None, seasons = None):
    """
    Load cleaned player info data from the volleydata repository.

    Parameters
    ----------
    league : str
        A string specifying which of 'mlv', 'pvf', or 'au' to load data for.

    seasons : int, list of int, or None, optional
        Season(s) to load. By default, None loads all available seasons.
        - int : Single season year (e.g., 2025)
        - list of int : Multiple seasons (e.g., [2024, 2025])
        - None : Load all available seasons

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the player-info data for the specified seasons.

            ================================  ===========
            Column Name                        Type
            ================================  ===========
            match_id                           int
            season                             int
            match_datetime                     str
            player_id                          int
            player_name                        str
            first_name                         str
            last_name                          str
            jersey_number                      int
            primary_position                   int
            roster_status                      str
            is_foreign                         bool
            is_confederation                   bool
            is_captain                         bool
            is_libero                          bool
            set_1_is_starter                   bool
            set_1_starting_position            int
            set_2_is_starter                   bool
            set_2_starting_position            int
            set_3_is_starter                   bool
            set_3_starting_position            int
            set_4_is_starter                   bool
            set_4_starting_position            int
            set_5_is_starter                   bool
            set_5_starting_position            int
            team_name                          str
            team_short_name                    str
            team_code                          str
            team_color                         str
            league                             str           
            ================================  ===========
    
    Examples
    --------
    >>> load_player_info]('lovb', 2025)
    >>> load_player_info('mlv', [2024, 2025])
    >>> load_player_info('au')
    """
    player_info = h.get_data(league, seasons, "player_info")
    return player_info


def load_team_staff(league = None, seasons = None):
    """
    Load cleaned team staff data from the volleydata repository.

    Parameters
    ----------
    league : str
        A string specifying which of 'mlv', 'pvf', or 'au' to load data for.

    seasons : int, list of int, or None, optional
        Season(s) to load. By default, None loads all available seasons.
        - int : Single season year (e.g., 2025)
        - list of int : Multiple seasons (e.g., [2024, 2025])
        - None : Load all available seasons

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the team-staff data for the specified seasons.

        ================================  ===========
        Column Name                        Type
        ================================  ===========
        match_id                           int
        season                             int
        match_datetime                     str
        team_name                          str
        staff_type                         str
        full_name                          str
        first_name                         str
        last_name                          str
        league                             str        
        ================================  ===========
    
    Examples
    --------
    >>> load_team_staff('lovb', 2025)
    >>> load_team_staff('mlv', [2024, 2025])
    >>> load_team_staff('au')
    """
    team_staff = h.get_data(league, seasons, "team_staff")
    return team_staff


def load_pbp(league = None, seasons = None):
    """
    Load cleaned pbp data from the volleydata repository.

    Parameters
    ----------
    league : str
        A string specifying which of 'mlv', 'pvf', or 'au' to load data for.

    seasons : int, list of int, or None, optional
        Season(s) to load. By default, None loads all available seasons.
        - int : Single season year (e.g., 2025)
        - list of int : Multiple seasons (e.g., [2024, 2025])
        - None : Load all available seasons

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the pbp data for the specified seasons.

        ================================  ===========
        Column Name                        Type
        ================================  ===========
        match_id                           int
        season                             int
        match_datetime                     str
        home_team_name                     str
        away_team_name                     str
        team_involved                      str
        jersey_number                      int         
        action                             str
        outcome                            str
        set                                int
        point_number                       int
        point_winner                       str
        home_score                         int
        away_score                         int
        rally_length                       int
        league                             str                          
        ================================  ===========
    
    Examples
    --------
    >>> load_pbp('lovb', 2025)
    >>> load_pbp('mlv', [2024, 2025])
    >>> load_pbp('au')
    """
    pbp = h.get_data(league, seasons, "pbp")
    return pbp


def load_events_log(league = None, seasons = None):
    """
    Load cleaned events log data from the volleydata repository.

    Parameters
    ----------
    league : str
        A string specifying which of 'mlv', 'pvf', or 'au' to load data for.

    seasons : int, list of int, or None, optional
        Season(s) to load. By default, None loads all available seasons.
        - int : Single season year (e.g., 2025)
        - list of int : Multiple seasons (e.g., [2024, 2025])
        - None : Load all available seasons

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the events log data for the specified seasons.

        ================================  ===========
        Column Name                        Type
        ================================  ===========
        match_id                           int
        season                             int
        match_datetime                     str
        set                                int
        set_start_time                     str
        set_end_time                       str
        set_duration                       int
        set_final_home_score               int
        set_final_away_score               int
        event_type                         str
        event_time                         str
        libero_enters                      bool
        team_involved                      str
        libero_jersey_number               int
        libero_subsitute_jersey_number     int
        rally_start_time                   str
        rally_end_time                     str
        rally_point_winner                 str
        substitute_in_jersey_number        int
        substitute_out_jersey_number       int
        challenge_approved                 str
        challenge_reason                   str
        challenge_method                   str
        challenge_response                 str
        challenge_at_home_score            float
        challenge_at_away_score            float
        challenge_score_change             str
        serving_team                       str
        current_home_score                 float
        current_away_score                 float
        home_team_p1                       float
        home_team_p2                       float
        home_team_p3                       float
        home_team_p4                       float
        home_team_p5                       float
        home_team_p6                       float
        away_team_p1                       float
        away_team_p2                       float
        away_team_p3                       float
        away_team_p4                       float
        away_team_p5                       float
        away_team_p6                       float
        verified_time                      string
        verified_method                    str
        sanction_type                      str
        sanction_remark                    float
        sanction_staff_role                str
        staff_first_name                   str
        staff_last_name                    str
        staff_type                         str
        is_exceptional                     str
        league                             str
        ================================  ===========
    
    Examples
    --------
    >>> load_events_log('lovb', 2025)
    >>> load_events_log('mlv', [2024, 2025])
    >>> load_events_log('au')
    """
    events_log = h.get_data(league, seasons, 'events_log')
    return events_log


def load_player_boxscore(league = None, seasons = None):
    """
    Load cleaned player boxscore data from the volleydata repository.

    Parameters
    ----------
    league : str
        A string specifying which of 'mlv', 'pvf', or 'au' to load data for.
    
    seasons : int, list of int, or None, optional
        Season(s) to load. By default, None loads all available seasons.
        - int : Single season year (e.g., 2025)
        - list of int : Multiple seasons (e.g., [2024, 2025])
        - None : Load all available seasons

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the player-boxscore data for the specified seasons.

        ================================  ===========
        Column Name                        Type
        ================================  ===========
        match_id                           int
        season                             int
        match_datetime                     str
        team_involved                      str
        team_name                          str
        player_name                        str
        first_name                         str
        last_name                          str
        sets_played                        int
        player_number                      int
        is_captain                         bool
        is_libero                          bool
        set_number                         int
        set_starting_position              str
        serves                             int
        serve_errors                       int
        serve_aces                         int
        serve_efficiency                   float
        attack_attempts                    int
        attack_errors                      int
        attack_kills                       int
        attack_success_ratio               float
        attack_efficiency                  float
        receptions                         int
        reception_errors                   int
        positive_reception_ratio           float
        perfect_reception_ratio            float
        block_points                       int
        block_touches                      int
        earned_points                      int
        net_points                         int
        assists                            int
        successful_digs                    int
        id                                 str
        spike_hp                           int
        points                             int 
        league                             str            
        ================================  ===========
    
    Examples
    --------
    >>> load_player_boxscore('lovb', 2025)
    >>> load_player_boxscore('mlv', [2024, 2025])
    >>> load_player_boxscore('au')
    """
    player_boxscore = h.get_data(league, seasons, 'player_boxscore')
    return player_boxscore


def load_team_boxscore(league = None, seasons = None):
    """
    Load cleaned mlv team boxscore data from the volleydata repository.

    Parameters
    ----------
    seasons : int, list of int, or None, optional
        Season(s) to load. By default, None loads all available seasons.
        - int : Single season year (e.g., 2025)
        - list of int : Multiple seasons (e.g., [2024, 2025])
        - None : Load all available seasons

        All years must be 2024 or later.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the team-boxscore data for the specified seasons.

        ================================  ===========
        Column Name                        Type
        ================================  ===========
        match_id                           int
        season                             int
        match_datetime                     str
        team_involved                      str
        team_name                          str
        set_number                         int
        serves                             int
        serve_errors                       int
        serve_aces                         int
        serve_efficiency                   float
        attack_attempts                    int
        attack_errors                      int
        attack_kills                       int
        attack_success_ratio               float
        attack_efficiency                  float
        receptions                         int
        reception_errors                   int
        positive_reception_ratio           float
        perfect_reception_ratio            float
        block_points                       int
        block_touches                      int
        earned_points                      int
        net_points                         int
        assists                            int
        successful_digs                    int
        id                                 str
        spike_hp                           int
        points                             int 
        league                             str            
        ================================  ===========
    
    Examples
    --------
    >>> load_team_boxscore('lovb', 2025)
    >>> load_team_boxscore('mlv', [2024, 2025])
    >>> load_team_boxscore('au')
    """
    team_boxscore = h.get_data(league, seasons, 'team_box_score')
    return team_boxscore