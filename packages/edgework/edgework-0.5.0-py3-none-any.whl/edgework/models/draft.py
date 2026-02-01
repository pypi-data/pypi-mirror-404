
from edgework.endpoints import API_PATH
from edgework.models.base import BaseNHLModel


class Draftee(BaseNHLModel):
    """
    This class represents a NHL draftee.
    """

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a Draftee object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the draftee
            **kwargs: Dynamic attributes for draftee properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

    def fetch_data(self):
        """
        Fetch the data for the draftee.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")


class DraftRanking(BaseNHLModel):
    """
    This class represents a NHL draft ranking.
    """

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a DraftRanking object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the draft ranking
            **kwargs: Dynamic attributes for draft ranking properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

    def fetch_data(self):
        """
        Fetch the data for the draft ranking.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")


class Draft(BaseNHLModel):
    """
    This class represents a NHL draft.
    """

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a Draft object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the draft
            **kwargs: Dynamic attributes for draft properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

    def fetch_data(self):
        """
        Fetch the data for the draft.

        This method retrieves draft data from the NHL API. If a year/season is specified
        in the _data dictionary, it fetches data for that specific season. Otherwise,
        it fetches the most recent draft data.

        Returns:
            self: Returns the Draft object with fetched data
        """
        if not hasattr(self.edgework_client, "http_client"):
            raise ValueError("Edgework client must have http_client attribute")

        http_client = self.edgework_client.http_client

        # Determine if we're fetching for a specific season or the current draft
        if "year" in self._data:
            season = str(self._data["year"])
            # Use the draft_picks endpoint with season and 'all' for the round parameter
            path = API_PATH["draft_picks"].format(season=season, round="all")
        else:
            # If no year specified, get the current draft
            path = API_PATH["draft_picks_now"]

        # Make the API request
        response = http_client.get(path)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch draft data: HTTP {response.status_code}")

        # Parse the response data
        draft_data = response.json()

        # Update the _data dictionary with the fetched data
        # If specific fields are needed, they can be extracted here
        self._data.update(draft_data)

        # Update year from the response if not already set
        if "year" not in self._data and "draftYear" in draft_data:
            self._data["year"] = draft_data["draftYear"]

        # If rounds information exists, process it
        if "rounds" in draft_data:
            self._data["rounds"] = draft_data["rounds"]

        self._fetched = True
        return self
