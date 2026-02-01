from edgework.models.base import BaseNHLModel
from edgework.models.team import Team


class Series(BaseNHLModel):
    """Represents a playoff series between two teams."""

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a Series object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the series
            **kwargs: Dynamic attributes for series properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

    def fetch_data(self):
        """
        Fetch the data for the series.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")


class Playoffs(BaseNHLModel):
    """Represents the playoffs for a given season."""

    def __init__(
        self,
        edgework_client,
        obj_id=None,
        year=None,
        series=None,
        bracket_logo=None,
        bracket_logo_fr=None,
    ):
        """
        Initialize a Playoffs object.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the playoffs
            year: The year of the playoffs
            series: A list of playoff series in the playoffs
            bracket_logo: The URL for the playoffs bracket logo
            bracket_logo_fr: The URL for the playoffs bracket logo french
        """
        super().__init__(edgework_client, obj_id)
        self.year = year
        self.series = series or []
        self.bracket_logo = bracket_logo
        self.bracket_logo_fr = bracket_logo_fr

    def fetch_data(self):
        """
        Fetch the data for the playoffs.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")
