from datetime import timedelta

from edgework.edgework import Edgework
from edgework.models.base import BaseNHLModel


class PeriodTime(BaseNHLModel):
    """PeriodTime model to store period time information."""

    def __init__(self, edgework_client=None, obj_id=None, **kwargs):
        """
        Initialize a PeriodTime object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the period time
            **kwargs: Dynamic attributes for period time properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs
        # Set defaults if not provided
        if "minutes" not in self._data:
            self._data["minutes"] = 0
        if "seconds" not in self._data:
            self._data["seconds"] = 0
        self.validate()

    @classmethod
    def from_string(cls, edgework_client, time_str):
        """
        Create a PeriodTime object from a string.

        Args:
            edgework_client: The Edgework client
            time_str: The string to parse (format: "MM:SS")

        Returns:
            A PeriodTime object
        """
        minutes, seconds = map(int, time_str.split(":"))
        return cls(edgework_client, minutes=minutes, seconds=seconds)

    def validate(self):
        """Validate the period time."""
        if self.minutes < 0:
            raise ValueError("Time cannot be negative")
        if self.minutes > 20:
            raise ValueError("Minutes must be less than 20")
        if self.seconds < 0:
            raise ValueError("Time cannot be negative")
        if self.seconds >= 60:
            raise ValueError("Seconds must be less than 60")
        if self.minutes == 20 and self.seconds > 0:
            raise ValueError("Minutes must be less than 20")

    @property
    def total_seconds(self):
        """Get the total seconds."""
        return self.minutes * 60 + self.seconds

    @property
    def timedelta(self):
        """Get the timedelta representation."""
        return timedelta(minutes=self.minutes, seconds=self.seconds)

    def __sub__(self, other):
        """Subtract another PeriodTime or timedelta from this PeriodTime."""
        if isinstance(other, PeriodTime):
            return self.timedelta - other.timedelta
        if isinstance(other, timedelta):
            return self.timedelta - other

    def fetch_data(self):
        """
        Fetch the data for the period time.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")


class Shift(BaseNHLModel):
    """
    Shift model to store shift information.

    A shift is a period of time when a player is on the ice.
    """

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a Shift object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the shift object
            **kwargs: Dynamic attributes for shift properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

    @property
    def duration(self) -> timedelta:
        """Get the duration of the shift."""
        return timedelta(
            seconds=self.shift_end.total_seconds - self.shift_start.total_seconds
        )

    @property
    def shift_length(self):
        """Get the length of the shift."""
        return self.shift_end - self.shift_start

    def __str__(self):
        return f"Shift {self.shift_id} - {self.shift_length}"

    def __repr__(self):
        return str(self)

    def fetch_data(self):
        """
        Fetch the data for the shift.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")

    def __eq__(self, other):
        return self.shift_id == other.shift_id

    @classmethod
    def from_api(cls, data: dict, edgework_client: Edgework) -> "Shift":
        """
        Create a Shift object from API data.

        Args:
            data: The data dictionary from the API
            edgework_client: The Edgework client

        Returns:
            A Shift object initialized with the provided data.
        """
        return cls(
            edgework_client=None,
            shift_id=data["id"],
            game_id=data["gameId"],
            player_id=data["playerId"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            period=data["period"],
            shift_start=data["startTime"],
            shift_end=data["endTime"],
            shift_number=data["shiftNumber"],
            team_id=data["teamId"],
            team_abbrev=data["teamAbbrev"],
        )
