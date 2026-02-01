from typing import List

from edgework.models.base import BaseNHLModel


class GameEvent(BaseNHLModel):
    """GameEvent model to store game event information."""

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a GameEvent object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the event
            **kwargs: Dynamic attributes for game event properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

    def fetch_data(self):
        """
        Fetch the data for the game event.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")


class GameLog(BaseNHLModel):
    """GameLog model to store game log information."""

    def __init__(
        self,
        edgework_client,
        obj_id=None,
        game_id=None,
        season=None,
        date=None,
        events=None,
    ):
        """
        Initialize a GameLog object.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the game log
            game_id: Game ID is the unique identifier for the game
            season: Season is the season the game was played in
            date: Date is the date the game was played
            events: Events is a list of GameEvent objects that occurred in the game
        """
        super().__init__(edgework_client, obj_id)
        self.game_id = game_id
        self.season = season
        self.date = date
        self.events = events or []

    def fetch_data(self):
        """
        Fetch the data for the game log.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")
