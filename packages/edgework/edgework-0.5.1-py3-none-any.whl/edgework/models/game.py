from datetime import datetime
from typing import List, Optional

from edgework.http_client import HttpClient
from edgework.models.base import BaseNHLModel
from edgework.models.shift import Shift


class Game(BaseNHLModel):
    """Game model to store game information."""

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a Game object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the game object
            **kwargs: Dynamic attributes for game properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs
        self._shifts: Optional[List[Shift]] = None

    @property
    def game_time(self):
        return self._data.get("start_time_utc").strftime("%I:%M %p")

    def __str__(self):
        return f"{self._data.get('away_team_abbrev')} @ {self._data.get('home_team_abbrev')} | {self.game_time} | {self._data.get('away_team_score')} - {self._data.get('home_team_score')}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        # Compare using game_id only
        return self._data.get("game_id") == getattr(other, "game_id", None)

    def __hash__(self):
        return hash(self._data.get("game_id"))

    def _get(self):
        """Get the game information."""
        raise NotImplementedError("Use from_api or from_dict to create Game instances")

    @property
    def shifts(self) -> List[Shift]:
        if not self._shifts:
            self._shifts = self._get_shifts()
        return self._shifts

    @classmethod
    def from_dict(cls, data: dict, client: HttpClient):
        game = cls(edgework_client=client, **data)
        return game

    @classmethod
    def from_api(cls, data: dict, client: HttpClient):
        game_dict = {
            "game_id": data.get("id"),
            "start_time_utc": datetime.strptime(
                data.get("startTimeUTC"), "%Y-%m-%dT%H:%M:%SZ"
            ),
            "game_state": data.get("gameState"),
            "away_team_abbrev": data.get("awayTeam").get("abbrev"),
            "away_team_id": data.get("awayTeam").get("id"),
            "away_team_score": data.get("awayTeam").get("score"),
            "home_team_abbrev": data.get("homeTeam").get("abbrev"),
            "home_team_id": data.get("homeTeam").get("id"),
            "home_team_score": data.get("homeTeam").get("score"),
            "season": data.get("season"),
            "venue": data.get("venue").get("default"),
        }
        game = cls.from_dict(game_dict, client)
        game._fetched = True
        return game

    @classmethod
    def get_game(cls, game_id: int, client: HttpClient):
        response = client.get(f"gamecenter/{game_id}/boxscore", web=True)
        data = response.json()
        return cls.from_api(data, client)

    def fetch_data(self):
        """Fetch the game data from the API.

        Uses the NHL API gamecenter endpoint to get detailed game information.

        Raises:
            ValueError: If no client is available to fetch game data.
            ValueError: If no game ID is available to fetch data.
        """
        if not self._client:
            raise ValueError("No client available to fetch game data")
        if not self.obj_id:
            raise ValueError("No game ID available to fetch data")

        response = self._client.get(f"gamecenter/{self.obj_id}/boxscore", web=True)
        data = response.json()

        game_dict = {
            "game_id": data.get("id"),
            "start_time_utc": datetime.strptime(
                data.get("startTimeUTC"), "%Y-%m-%dT%H:%M:%SZ"
            ),
            "game_state": data.get("gameState"),
            "away_team_abbrev": data.get("awayTeam").get("abbrev"),
            "away_team_id": data.get("awayTeam").get("id"),
            "away_team_score": data.get("awayTeam").get("score"),
            "home_team_abbrev": data.get("homeTeam").get("abbrev"),
            "home_team_id": data.get("homeTeam").get("id"),
            "home_team_score": data.get("homeTeam").get("score"),
            "season": data.get("season"),
            "venue": data.get("venue").get("default"),
        }

        self._data.update(game_dict)
        self._fetched = True

    def _get_shifts(self):
        """Get the shifts for the game."""
        response = self._client.get(
            "rest/en/shiftcharts",
            params={"cayenneExp": f"gameId={self.game_id}"},
            web=False,
        )
        data = response.json()["data"]
        shifts = [Shift.from_api(d) for d in data]
        self._shifts = shifts
        return shifts
