from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from edgework.models.base import BaseNHLModel

if TYPE_CHECKING:
    from edgework.models.game import Game


def schedule_api_to_dict(data: dict) -> dict:
    """Convert schedule API response data to schedule dictionary format."""
    # Extract games from gameWeek structure if present, otherwise use games directly
    games = data.get("games") or []
    if not games and "gameWeek" in data:
        games = [
            game for day in data.get("gameWeek", []) for game in day.get("games", [])
        ]

    return {
        "previous_start_date": data.get("previousStartDate"),
        "games": games,
        "pre_season_start_date": data.get("preSeasonStartDate"),
        "regular_season_start_date": data.get("regularSeasonStartDate"),
        "regular_season_end_date": data.get("regularSeasonEndDate"),
        "playoff_end_date": data.get("playoffEndDate"),
        "number_of_games": data.get("numberOfGames", len(games)),
    }


class Schedule(BaseNHLModel):
    """Schedule model to store schedule information."""

    def __init__(self, http_client, obj_id=None, **kwargs):
        """
        Initialize a Schedule object with dynamic attributes.

          Args:
            http_client: The HttpClient
            obj_id: The ID of the schedule (optional)
            **kwargs: Dynamic attributes for schedule properties
        """
        super().__init__(http_client, obj_id)
        self._data = kwargs.copy()  # Create a copy to avoid modifying original kwargs
        self._games_objects: List[Game] = []

        # Initialize empty games list if not provided
        if "games" not in self._data:
            self._data["games"] = []

        # Set _fetched to True if we have any data
        if kwargs:
            self._fetched = True

    @classmethod
    def from_dict(cls, http_client, data: dict) -> "Schedule":
        """
        Create a Schedule object from a dictionary.

        Args:
            http_client: The HttpClient
            data: Dictionary containing schedule data

        Returns:
            Schedule: A Schedule object
        """
        previous = (
            datetime.fromisoformat(data["previousStartDate"])
            if data.get("previousStartDate")
            else None
        )
        games = data.get("games") or [
            game for day in data.get("gameWeek", []) for game in day.get("games", [])
        ]
        pre_season = (
            datetime.fromisoformat(data["preSeasonStartDate"])
            if data.get("preSeasonStartDate")
            else None
        )
        reg_start = (
            datetime.fromisoformat(data["regularSeasonStartDate"])
            if data.get("regularSeasonStartDate")
            else None
        )
        reg_end = (
            datetime.fromisoformat(data["regularSeasonEndDate"])
            if data.get("regularSeasonEndDate")
            else None
        )
        playoff = (
            datetime.fromisoformat(data["playoffEndDate"])
            if data.get("playoffEndDate")
            else None
        )
        number_of_games = data.get("numberOfGames") or 0
        return cls(
            http_client=http_client,
            previous_start_date=previous,
            games=games,
            pre_season_start_date=pre_season,
            regular_season_start_date=reg_start,
            regular_season_end_date=reg_end,
            playoff_end_date=playoff,
            number_of_games=number_of_games,
        )

    @classmethod
    def from_dict(cls, http_client, data: dict) -> "Schedule":
        """
        Create a Schedule object from dictionary data.

        Args:
            http_client: The HttpClient
            data: Dictionary containing schedule data

        Returns:
            Schedule: A Schedule object
        """
        # Convert date strings to datetime objects if they exist
        processed_data = {}

        date_fields = [
            "previous_start_date",
            "pre_season_start_date",
            "regular_season_start_date",
            "regular_season_end_date",
            "playoff_end_date",
        ]

        for field in date_fields:
            if field in data and data[field]:
                try:
                    if isinstance(data[field], str):
                        processed_data[field] = datetime.fromisoformat(
                            data[field].replace("Z", "+00:00")
                        )
                    else:
                        processed_data[field] = data[field]
                except (ValueError, TypeError):
                    processed_data[field] = data[field]
            else:
                processed_data[field] = data.get(field)

        # Copy other fields
        processed_data["games"] = data.get("games", [])
        processed_data["number_of_games"] = data.get(
            "number_of_games", len(processed_data["games"])
        )

        return cls(http_client=http_client, **processed_data)

    @classmethod
    def from_api(cls, http_client, data: dict) -> "Schedule":
        """
        Create a Schedule object from raw API response data.

        Args:
            http_client: The HttpClient
            data: Raw API response data

        Returns:
            Schedule: A Schedule object
        """
        schedule_dict = schedule_api_to_dict(data)
        return cls.from_dict(http_client, schedule_dict)

    def fetch_data(self):
        """
        Fetch the data for the schedule.
        This method would be called if the schedule needs to be refreshed from the API.
        """
        if not self._client:
            raise ValueError(
                "No client available to fetch schedule data"
            )  # For now, schedule data is typically loaded when created
        # If specific schedule fetching is needed, it would be implemented here
        raise NotImplementedError("fetch_data() is not implemented for Schedule model")

    @property
    def games(self) -> List["Game"]:
        """
        Get the games as Game objects.

        Returns:
            List[Game]: List of Game objects
        """
        if not self._games_objects and self._data.get("games"):
            # Lazy import to avoid circular dependencies
            from edgework.models.game import Game

            self._games_objects = []
            for game_data in self._data["games"]:
                if self._client:
                    game = Game.from_api(game_data, self._client)
                    self._games_objects.append(game)
        return self._games_objects

    @property
    def games_today(self) -> List["Game"]:
        """
        Get games scheduled for today.        Returns:
            List[Game]: List of games scheduled for today
        """
        today = datetime.now().date()
        result = []
        for game in self.games:
            game_date = game._data.get("game_date")
            if game_date:
                # Handle both datetime and date objects
                if hasattr(game_date, "date"):
                    # It's a datetime object
                    game_date_obj = game_date.date()
                elif hasattr(game_date, "year"):
                    # It's already a date object
                    game_date_obj = game_date
                else:
                    # Skip if it's neither
                    continue

                if game_date_obj == today:
                    result.append(game)
        return result

    @property
    def upcoming_games(self) -> List["Game"]:
        """
        Get upcoming games (future games only).

        Returns:
            List[Game]: List of upcoming games
        """
        now = datetime.now()
        return [
            game for game in self.games if game._data.get("start_time_utc", now) > now
        ]

    @property
    def completed_games(self) -> List["Game"]:
        """
        Get completed games.

        Returns:
            List[Game]: List of completed games
        """
        return [
            game
            for game in self.games
            if game._data.get("game_state") in ["OFF", "FINAL"]
        ]

    def __str__(self) -> str:
        """
        Return a human-readable string representation of the schedule.

        Returns:
            str: String representation of the schedule
        """
        # Get number of games
        num_games = self._data.get("number_of_games")

        # Get start and end dates
        start_date = self._data.get("regular_season_start_date")
        end_date = self._data.get("regular_season_end_date")

        # Format the string representation
        if num_games is not None and num_games > 0:
            result = f"Schedule ({num_games} games)"

            # Add date range if both dates are available
            if start_date and end_date:
                # Handle both string and datetime objects
                if isinstance(start_date, str):
                    try:
                        start_date = datetime.fromisoformat(
                            start_date.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        raise ValueError("Invalid start date format")

                if isinstance(end_date, str):
                    try:
                        end_date = datetime.fromisoformat(
                            end_date.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        raise ValueError("Invalid end date format")

                # Format dates if they are datetime objects
                if hasattr(start_date, "strftime") and hasattr(end_date, "strftime"):
                    start_str = start_date.strftime("%Y-%m-%d")
                    end_str = end_date.strftime("%Y-%m-%d")
                    result += f": {start_str} to {end_str}"

            return result
        else:
            return "Schedule"

    def __repr__(self) -> str:
        """
        Return a detailed string representation of the schedule.

        Returns:
            str: Detailed representation of the schedule
        """
        games = self._data.get("games", [])
        if games:
            return f"Schedule(games={len(games)})"
        else:
            return f"Schedule(id={self.obj_id})"
