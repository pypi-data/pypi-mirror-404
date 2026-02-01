import re

from edgework.clients.player_client import PlayerClient
from edgework.clients.schedule_client import ScheduleClient
from edgework.clients.team_client import TeamClient
from edgework.http_client import HttpClient

# Import the SkaterStats model
from edgework.models.player import Player
from edgework.models.schedule import Schedule
from edgework.models.stats import GoalieStats, SkaterStats, TeamStats
from edgework.models.team import Roster, Team


def _validate_season_format(season: str) -> int:
    """
    Validates season string format and converts to integer.

    Args:
        season (str): Season string in format "YYYY-YYYY" (e.g., "2023-2024")

    Returns:
        int: Season as integer in format YYYYYYYY (e.g., 20232024)

    Raises:
        ValueError: If season format is invalid
    """
    if not isinstance(season, str):
        raise ValueError("Invalid season format. Expected 'YYYY-YYYY'")

    # Check if format matches exactly "YYYY-YYYY"
    if not re.match(r"^\d{4}-\d{4}$", season):
        raise ValueError("Invalid season format. Expected 'YYYY-YYYY'")

    # Split and validate years
    try:
        first_year_str, second_year_str = season.split("-")
        first_year = int(first_year_str)
        second_year = int(second_year_str)
    except ValueError:
        raise ValueError("Invalid season format. Expected 'YYYY-YYYY'")

    # Validate that second year is first year + 1
    if second_year != first_year + 1:
        raise ValueError("Invalid season format. Expected 'YYYY-YYYY'")

    # Convert to integer format (e.g., "2023-2024" -> 20232024)
    return first_year * 10000 + second_year


class Edgework:
    def __init__(self, user_agent: str = "EdgeworkClient/2.0"):
        """
        Initializes the Edgework API client.

        Args:
            user_agent (str, optional): The User-Agent string to use for requests.
                                        Defaults to "EdgeworkClient/2.0".
        """
        self._client = HttpClient(user_agent=user_agent)

        # Initialize model handlers, passing the shared HTTP client
        self.skaters = SkaterStats(edgework_client=self._client)
        self.goalies = GoalieStats(edgework_client=self._client)
        self.teams = TeamStats(edgework_client=self._client)

        # Initialize client handlers
        self._player_client = PlayerClient(http_client=self._client)
        self._team_client = TeamClient(client=self._client)
        self._schedule_client = ScheduleClient(client=self._client)

    def players(self, active_only: bool = True) -> list[Player]:
        """
        Fetch a list of players.

        Args:
            active_only (bool): If True, fetch only active players.
                               If False, fetch all players (active and inactive).
                               Defaults to True.

        Returns:
            list[Player]: A list of Player objects.
        """
        if active_only:
            return self._player_client.get_active_players()
        else:
            return self._player_client.get_all_players()

    def skater_stats(
        self,
        season: str,
        report: str = "summary",
        sort: str | list[str] = "points",
        direction: str | list[str] = "DESC",
        aggregate: bool = False,
        limit: int = 10,
        game_type: int = 2,
    ) -> SkaterStats:
        """
        Fetch skater stats for a given season.
        Args:
            season (str): The season to fetch stats for (e.g., "2024-2025").
            report (str): The type of report to fetch (e.g., "summary", "detailed").
            sort (str | list[str]): The field to sort the results by (e.g., "points", "goals").
            direction (str | list[str]): The direction to sort the results (e.g., "DESC", "ASC").
            aggregate (bool): Whether to aggregate the stats. Defaults to False.
            limit (int): The maximum number of results to return.

        Returns:
            SkaterStats: An instance of the SkaterStats model, populated with the fetched data.
                         The actual player statistics can be accessed via `instance.players`.
        """
        # Convert season string "YYYY-YYYY" to integer YYYYYYYY
        converted_season = _validate_season_format(season)

        self.skaters.fetch_data(
            report=report,
            season=converted_season,
            sort=sort,
            direction=direction,
            limit=limit,
            aggregate=aggregate,
            game_type=game_type,
        )
        return self.skaters

    def goalie_stats(
        self,
        season: str,
        report: str = "summary",
        sort: str | list[str] = "wins",
        direction: str | list[str] = "DESC",
        is_aggregate: bool = False,
        limit: int = 10,
    ) -> GoalieStats:
        """
        Fetch goalie stats for a given season.
        Args:
            season (str): The season to fetch stats for (e.g., "2024-2025").
            report (str): The type of report to fetch (e.g., "summary", "detailed").
            sort (str): The field to sort the results by (e.g., "wins", "goalsAgainst").
            is_aggregate (bool): Whether to aggregate the stats. Defaults to False.
            limit (int): The maximum number of results to return.

        Returns:
            GoalieStats: An instance of the GoalieStats model, populated with the fetched data.
                         The actual goalie statistics can be accessed via `instance.players`.
        """
        # Convert season string "YYYY-YYYY" to integer YYYYYYYY
        converted_season = _validate_season_format(season)

        self.goalies.fetch_data(
            report=report, season=converted_season, sort=sort, limit=limit
        )
        return self.goalies

    def team_stats(
        self,
        season: str,
        report: str = "summary",
        sort: str | list[str] = "points",
        direction: str | list[str] = "DESC",
        limit: int = 10,
        aggregate: bool = False,
        game: bool = True,
    ) -> TeamStats:
        """
        Fetch team stats for a given season.
        Args:
            season (str): The season to fetch stats for (e.g., "2024-2025").
            report (str): The type of report to fetch (e.g., "summary", "detailed").
            sort (dict): The field to sort the results by (e.g., "points", "wins").
            limit (int): The maximum number of results to return. Defaults to 10.
            aggregate (bool): Whether to aggregate the stats. Defaults to False.

        Returns:
            TeamStats: An instance of the TeamStats model, populated with the fetched data.
                         The actual team statistics can be accessed via `instance.teams`.
        """
        # Convert season string "YYYY-YYYY" to integer YYYYYYYY
        converted_season = _validate_season_format(season)

        self.teams.fetch_data(
            report=report,
            season=converted_season,
            sort=sort,
            direction=direction,
            limit=limit,
            aggregate=aggregate,
            game=game,
        )
        return self.teams

    def get_teams(self) -> list[Team]:
        """
        Fetch a list of all NHL teams.

        Returns:
            list[Team]: A list of Team objects.
        """
        return self._team_client.get_teams()

    def get_roster(self, team_code: str, season: str = None) -> Roster:
        """
        Fetch a roster for a specific team.

        Args:
            team_code (str): The team code (e.g., 'TOR', 'NYR').
            season (str, optional): The season in format "YYYY-YYYY" (e.g., "2023-2024").
                                   If None, gets current roster.

        Returns:
            Roster: A Roster object containing the team's players.
        """
        converted_season = None
        if season:
            converted_season = _validate_season_format(season)

        return self._team_client.get_roster(team_code, converted_season)

    def get_team_stats(
        self, team_code: str, season: str = None, game_type: int = 2
    ) -> dict:
        """
        Get team statistics.

        Args:
            team_code (str): The team code (e.g., 'TOR', 'NYR').
            season (str, optional): The season in format "YYYY-YYYY" (e.g., "2023-2024").
                                   If None, gets current season stats.
            game_type (int): Game type (2 for regular season, 3 for playoffs). Default is 2.

        Returns:
            dict: Team statistics data.
        """
        converted_season = None
        if season:
            converted_season = _validate_season_format(season)

        return self._team_client.get_team_stats(team_code, converted_season, game_type)

    def get_team_schedule(self, team_code: str, season: str = None) -> dict:
        """
        Get team schedule.

        Args:
            team_code (str): The team code (e.g., 'TOR', 'NYR').
            season (str, optional): The season in format "YYYY-YYYY" (e.g., "2023-2024").
                                   If None, gets current season schedule.

        Returns:
            dict: Team schedule data.
        """
        converted_season = None
        if season:
            converted_season = _validate_season_format(season)

        return self._team_client.get_team_schedule(team_code, converted_season)

    def get_team_prospects(self, team_code: str) -> dict:
        """
        Get team prospects.

        Args:
            team_code (str): The team code (e.g., 'TOR', 'NYR').

        Returns:
            dict: Team prospects data.
        """
        return self._team_client.get_team_prospects(team_code)

    def get_team_scoreboard(self, team_code: str) -> dict:
        """
        Get team scoreboard.

        Args:
            team_code (str): The team code (e.g., 'TOR', 'NYR').

        Returns:
            dict: Team scoreboard data.
        """
        return self._team_client.get_scoreboard(team_code)

    # Schedule methods
    def get_schedule(self) -> Schedule:
        """
        Get the current NHL schedule.

        Returns:
            Schedule: Current NHL schedule with games and season information.
        """
        return self._schedule_client.get_schedule()

    def get_schedule_for_date(self, date: str) -> Schedule:
        """
        Get the NHL schedule for a specific date.

        Args:
            date (str): The date in format 'YYYY-MM-DD'.

        Returns:
            Schedule: NHL schedule for the specified date.
        """
        return self._schedule_client.get_schedule_for_date(date)

    def get_schedule_for_date_range(self, start_date: str, end_date: str) -> Schedule:
        """
        Get the NHL schedule for a date range.

        Args:
            start_date (str): The start date in format 'YYYY-MM-DD'.
            end_date (str): The end date in format 'YYYY-MM-DD'.

        Returns:
            Schedule: NHL schedule for the specified date range.
        """
        return self._schedule_client.get_schedule_for_date_range(start_date, end_date)

    def get_team_schedule_full(self, team_abbr: str) -> Schedule:
        """
        Get the full season schedule for a specific team.

        Args:
            team_abbr (str): The team abbreviation (e.g., 'TOR', 'NYR').

        Returns:
            Schedule: Full season schedule for the specified team.
        """
        return self._schedule_client.get_schedule_for_team(team_abbr)

    def get_team_schedule_week(self, team_abbr: str) -> Schedule:
        """
        Get the weekly schedule for a specific team.

        Args:
            team_abbr (str): The team abbreviation (e.g., 'TOR', 'NYR').

        Returns:
            Schedule: Weekly schedule for the specified team.
        """
        return self._schedule_client.get_schedule_for_team_for_week(team_abbr)

    def get_team_schedule_month(self, team_abbr: str) -> Schedule:
        """
        Get the monthly schedule for a specific team.

        Args:
            team_abbr (str): The team abbreviation (e.g., 'TOR', 'NYR').

        Returns:
            Schedule: Monthly schedule for the specified team.
        """
        return self._schedule_client.get_schedule_for_team_for_month(team_abbr)

    def get_schedule_calendar(self) -> dict:
        """
        Get the current NHL schedule calendar.

        Returns:
            dict: Schedule calendar showing available dates with games.
        """
        return self._schedule_client.get_schedule_calendar()

    def get_schedule_calendar_for_date(self, date: str) -> dict:
        """
        Get the NHL schedule calendar for a specific date.

        Args:
            date (str): The date in format 'YYYY-MM-DD'.

        Returns:
            dict: Schedule calendar for the specified date.
        """
        return self._schedule_client.get_schedule_calendar_for_date(date)

    def close(self):
        """Closes the underlying HTTP client session."""
        if hasattr(self._client, "close"):
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
