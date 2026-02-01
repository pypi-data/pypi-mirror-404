import json
from datetime import datetime
from urllib.parse import urlencode

from edgework.models.base import BaseNHLModel
from edgework.utilities import dict_camel_to_snake

# Development imports


def validate_sort_direction(
    sort: str | list[str], direction: str | list[str]
) -> dict | list[dict]:
    """
    Validates and formats the sort and direction parameters.

    Makes sure that:
    - If both are strings, they are valid and compatible.
    - If both are lists, they are of the same length and contain valid values.
    - If one is a string and the other is a list, raises an error.
    - If both are empty, raises an error.
    - If the direction is not "ASC" or "DESC", raises an error.
    - Returns a dictionary or list of dictionaries representing the sort criteria.

    Args:
        sort (str | list[str]): The field(s) to sort by.
        direction (str | list[str]): The direction(s) to sort (e.g., "ASC", "DESC").

    Returns:
        dict | list[dict]: A dictionary or list of dictionaries representing the sort criteria.
    """
    if isinstance(sort, str) and isinstance(direction, str):
        if direction not in ["ASC", "DESC"]:
            raise ValueError("Direction must be either 'ASC' or 'DESC'.")
        return {"property": sort, "direction": direction}
    elif isinstance(sort, list) and isinstance(direction, list):
        if len(sort) != len(direction):
            raise ValueError("Sort and direction lists must be of the same length.")
        if any(not isinstance(s, str) for s in sort):
            raise ValueError("Sort must be a string or a list of strings.")
        if any(not isinstance(d, str) for d in direction):
            raise ValueError("Direction must be a string or a list of strings.")
        if len(sort) == 0 or len(direction) == 0:
            raise ValueError("Sort and direction lists cannot be empty.")
        if any(d not in ["ASC", "DESC"] for d in direction):
            raise ValueError("Direction must be either 'ASC' or 'DESC'.")
        return [{"property": s, "direction": d} for s, d in zip(sort, direction)]
    else:
        raise ValueError(
            "Sort and direction must be either both strings or both lists."
        )


def validate_season(season: int | None) -> int:
    """
    Validates and returns a proper season value.

    Args:
        season (int | None): The season to validate (e.g., 20232024) or None for current season.

    Returns:
        int: A valid season value.
    """
    if season is None:
        # Auto-calculate current season based on date
        current_date = datetime.now()
        if (
            current_date.month >= 7
        ):  # NHL season starts in October, but prep starts in July
            return current_date.year * 10000 + (current_date.year + 1)
        else:
            return (current_date.year - 1) * 10000 + current_date.year

    if not isinstance(season, int):
        raise ValueError("Season must be an integer (e.g., 20232024) or None.")

    # Basic validation for season format (should be 8 digits, like 20232024)
    if (
        season < 19171918 or season > 21002101
    ):  # NHL started 1917-18, reasonable upper bound
        raise ValueError(
            "Season must be in format YYYYZZZZ (e.g., 20232024) and within valid NHL history."
        )

    # Check that it follows the correct year pattern (second year should be first year + 1)
    first_year = season // 10000
    second_year = season % 10000
    if second_year != first_year + 1:
        raise ValueError(
            "Season must follow format YYYYZZZZ where ZZZZ = YYYY + 1 (e.g., 20232024)."
        )

    return season


def validate_game_type(game_type: int | None) -> str:
    """
    Validates game type and returns the appropriate cayenne expression part.

    Args:
        game_type (int | None): The game type (2 for regular season, 3 for playoffs, None for all).

    Returns:
        str: The game type part of the cayenne expression.
    """
    if game_type is None:
        return ""

    if not isinstance(game_type, int):
        raise ValueError("Game type must be an integer or None.")

    if game_type not in [2, 3]:
        raise ValueError("Game type must be either 2 (regular season) or 3 (playoffs).")

    return f" and gameTypeId={game_type}"


def validate_report_type(report: str, valid_reports: list[str]) -> str:
    """
    Validates that the report type is valid for the given context.

    Args:
        report (str): The report type to validate.
        valid_reports (list[str]): List of valid report types.

    Returns:
        str: The validated report type.
    """
    if not isinstance(report, str):
        raise ValueError("Report must be a string.")

    if report not in valid_reports:
        raise ValueError(f"Report must be one of: {', '.join(valid_reports)}")

    return report


def validate_limit_and_start(limit: int, start: int) -> tuple[int, int]:
    """
    Validates limit and start parameters.

    Args:
        limit (int): The limit value (-1 for all, or positive integer).
        start (int): The start value (non-negative integer).

    Returns:
        tuple[int, int]: Validated limit and start values.
    """
    if not isinstance(limit, int):
        raise ValueError("Limit must be an integer.")

    if not isinstance(start, int):
        raise ValueError("Start must be an integer.")

    if limit != -1 and limit <= 0:
        raise ValueError("Limit must be -1 (for all) or a positive integer.")

    if start < 0:
        raise ValueError("Start must be a non-negative integer.")

    return limit, start


class StatEntity(BaseNHLModel):
    """
    PlayerStats model to store player statistics.
    """

    def __init__(
        self, edgework_client, id: int | None = None, data: dict | None = None
    ):
        super().__init__(edgework_client, id)
        self._data = data
        self._fetched = True


class SkaterStats(BaseNHLModel):
    """
    SkaterStats model to store skater statistics.
    """

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a SkaterStats object with dynamic attributes.
        """
        super().__init__(edgework_client, obj_id)
        players: list[StatEntity] = []
        self._data = kwargs

    def fetch_data(
        self,
        report: str = "summary",
        season: int = None,
        aggregate: bool = False,
        game: bool = True,
        limit: int = -1,
        start: int = 0,
        sort: str | list[str] = "points",
        direction: str | list[str] = "DESC",
        game_type: int = None,
    ) -> None:
        """
        Fetch the data for the skater stats.

        Args:
            report: The type of report to get (e.g. "summary", "bios", etc.)
            season: The season to get stats for (e.g. 20232024)
            aggregate: Whether to aggregate the stats
            game: Whether to get game stats
            limit: Number of results to return (-1 for all)
            start: Starting index for results
            sort: Field to sort by
            direction: Direction to sort (e.g. "DESC", "ASC")
            game_type: Type of game (e.g. 2 for regular season, 3 for playoffs)
        """
        # Validate inputs using helper functions
        valid_skater_reports = [
            "summary",
            "bios",
            "faceoffpercentages",
            "faceoffwins",
            "goalsForAgainst",
            "realtime",
            "penalties",
            "penaltyDetails",
            "penaltyKill",
            "penaltyShots",
            "powerPlay",
            "puckPossessions",
            "summaryshooting",
            "percentages",
            "scoringRates",
            "scoringpergame",
            "shootout",
            "shottype",
            "timeonice",
        ]

        report = validate_report_type(report, valid_skater_reports)
        season = validate_season(season)
        limit, start = validate_limit_and_start(limit, start)
        sort_dict = validate_sort_direction(sort, direction)
        game_type_exp = validate_game_type(game_type)

        # Build cayenne expression
        cayenne_exp = f"seasonId={season}{game_type_exp}"

        # Convert sort_dict to JSON
        sort_json = json.dumps(sort_dict)

        # Fix encoding issue by handling sort_dict correctly
        if isinstance(sort_dict, dict):
            sort_param = sort_dict["property"]
        elif isinstance(sort_dict, list):
            sort_param = ",".join([item["property"] for item in sort_dict])
        else:
            raise ValueError(
                "Invalid sort_dict format. Must be a dict or list of dicts."
            )

        url_path = f"skater/{report}"
        params = {
            "isAggregate": aggregate,
            "isGame": game,
            "limit": limit,
            "start": start,
            "sort": sort_param,  # Fixed sort parameter
            "cayenneExp": cayenne_exp,
        }
        query_string = urlencode(params, safe="=")
        full_path = f"{url_path}?{query_string}"

        response = self._client.get(
            endpoint="stats", path=full_path, params=None, web=False
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch skater stats: {response.status_code} {response.text}"
            )

        data = response.json().get("data")
        if data is None:
            raise KeyError("Missing 'data' key in API response")

        # Convert camelCase to snake_case and update data
        if data:
            self._data = data
            self.players = [
                StatEntity(self._client, data=dict_camel_to_snake(player))
                for player in data
            ]


class GoalieStats(BaseNHLModel):
    """
    GoalieStats model to store goalie statistics.
    """

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a GoalieStats object with dynamic attributes.
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs
        self.players: list[StatEntity] = []

    def fetch_data(
        self,
        report: str = "summary",
        season: int = None,
        aggregate: bool = False,
        game: bool = True,
        limit: int = -1,
        start: int = 0,
        sort: str | list[str] = "wins",
        direction: str | list[str] = "DESC",
        game_type: int | None = None,
    ) -> None:
        """
        Fetch the data for the goalie stats.

        Args:
            report: The type of report to get (e.g. "summary", "advanced", etc.)
            season: The season to get stats for (e.g. 20232024)
            aggregate: Whether to aggregate the stats
            game: Whether to get game stats
            limit: Number of results to return (-1 for all)
            start: Starting index for results
            sort: Field to sort by
            direction: Direction to sort (e.g. "DESC", "ASC")
            game_type: Type of game (e.g. 2 for regular season, 3 for playoffs)
        """
        # Validate inputs using helper functions
        valid_goalie_reports = [
            "summary",
            "advanced",
            "bios",
            "savesByStrength",
            "startedVsRelieved",
            "daysrest",
            "shootout",
            "penaltyShots",
            "savePercentageByGametate",
        ]

        report = validate_report_type(report, valid_goalie_reports)
        season = validate_season(season)
        limit, start = validate_limit_and_start(limit, start)
        sort_dict = validate_sort_direction(sort, direction)
        game_type_exp = validate_game_type(game_type)
        if isinstance(sort_dict, dict):
            sort_param = sort_dict["property"]
        elif isinstance(sort_dict, list):
            sort_param = ",".join([item["property"] for item in sort_dict])
        else:
            raise ValueError(
                "Invalid sort_dict format. Must be a dict or list of dicts."
            )

        # Build cayenne expression
        cayenne_exp = f"seasonId={season}{game_type_exp}"

        # Convert sort_dict to JSON
        sort_json = json.dumps(sort_dict)

        url_path = f"goalie/{report}"
        params = {
            "isAggregate": aggregate,
            "isGame": game,
            "limit": limit,
            "start": start,
            "sort": sort_param,  # Fixed sort parameter
            "cayenneExp": cayenne_exp,
        }
        query_string = urlencode(params, safe="=")
        full_path = f"{url_path}?{query_string}"

        response = self._client.get(
            endpoint="stats", path=full_path, params=None, web=False
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch goalie stats: {response.status_code} {response.text}"
            )

        data = response.json().get("data")
        if data is None:
            raise KeyError("Missing 'data' key in API response")

        # Convert camelCase to snake_case and update data
        if data:
            self._data = data
            self.players = [
                StatEntity(self._client, data=dict_camel_to_snake(player))
                for player in data
            ]


class TeamStats(BaseNHLModel):
    """Team Stats model to store team statistics for a season."""

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a TeamStats object with dynamic attributes.
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs
        self.teams: list[StatEntity] = []

    def fetch_data(
        self,
        report: str = "summary",
        season: int = None,
        aggregate: bool = False,
        game: bool = True,
        limit: int = -1,
        start: int = 0,
        sort: str = "wins",
        direction: str = "DESC",
        game_type: int = 2,
    ) -> None:
        """
        Fetch the data for the team stats.

        Args:
            report: The type of report to get (e.g. "summary", "faceoffpercentages", etc.)
            season: The season to get stats for (e.g. 20232024)
            aggregate: Whether to aggregate the stats
            game: Whether to get game stats. If False, returns aggregate stats.
            limit: Number of results to return (-1 for all). Default is -1.
            start: Starting index for results. Default is 0.
            sort: Field to sort by. Can be a string (e.g. "points") or a list of dicts for multiple fields. Default is "wins".
            direction: Direction to sort (e.g. "DESC", "ASC"). Default is "DESC".
            game_type: Type of game (e.g. 2 for regular season, 3 for playoffs). Default is 2.
        """
        # Validate inputs using helper functions
        valid_team_reports = [
            "summary",
            "faceoffpercentages",
            "faceoffwins",
            "goalsForAgainst",
            "realtime",
            "penalties",
            "penaltyDetails",
            "penaltyKill",
            "powerPlay",
            "puckPossessions",
            "summaryshooting",
            "percentages",
            "scoringRates",
            "scoringpergame",
            "shootout",
            "shottype",
            "timeonice",
        ]

        report = validate_report_type(report, valid_team_reports)
        season = validate_season(season)
        limit, start = validate_limit_and_start(limit, start)
        sort_dict = validate_sort_direction(sort, direction)
        game_type_exp = validate_game_type(game_type)
        if isinstance(sort_dict, dict):
            sort_param = sort_dict["property"]
        elif isinstance(sort_dict, list):
            sort_param = ",".join([item["property"] for item in sort_dict])
        else:
            raise ValueError(
                "Invalid sort_dict format. Must be a dict or list of dicts."
            )

        # Build cayenne expression
        cayenne_exp = f"seasonId={season}"  # Removed gameTypeId from cayenneExp

        # Convert sort_dict to JSON
        sort_json = json.dumps(sort_dict)
        params = {
            "isAggregate": aggregate,
            "isGame": game,
            "limit": limit,
            "start": start,
            "sort": sort_param,  # Fixed sort parameter
            "cayenneExp": cayenne_exp,
        }
        query_string = urlencode(params, safe="=")
        full_path = f"team/{report}?{query_string}"

        response = self._client.get(
            endpoint="stats", path=full_path, params=None, web=False
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch team stats: {response.status_code} {response.text}"
            )

        data = response.json().get("data")
        if data is None:
            raise KeyError("Missing 'data' key in API response")

        if data:
            data = [dict_camel_to_snake(d) for d in data]
            self.teams = [StatEntity(self._client, data=team) for team in data]
            self._data = data
