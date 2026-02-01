# https://api.nhle.com/stats/rest/en/config

from edgework.endpoints import API_PATH
from edgework.models.base import BaseNHLModel


class Config(BaseNHLModel):
    """
    This class represents the NHL configuration.
    """

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a Config object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the config
            **kwargs: Dynamic attributes for config properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs
        self._data["api_path"] = API_PATH
        self._data["api_version"] = "v1"
        self._data["api_base_url"] = (
            f"{self._data['api_path']}/{self._data['api_version']}"
        )
        self._data["api_url"] = f"{self._data['api_base_url']}/config"

    def fetch_data(self):
        """
        Fetch the data for the config.
        """
        # Implementation depends on how data is fetched from the API
        # For example, you might want to make a GET request to the API URL
        # and populate self._data with the response.
        if not hasattr(self, "_data"):
            self._data = {}
        pass
