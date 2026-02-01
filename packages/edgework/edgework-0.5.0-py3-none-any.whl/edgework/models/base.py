from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from edgework.edgework import Edgework


class BaseNHLModel:
    """
    Base class for all NHL models.
    """

    def __init__(self, edgework_client: "Edgework", obj_id: int = None):

        self._client: "Edgework" = edgework_client
        self.obj_id: int = obj_id
        self._fetched: bool = False

    def _fetch_if_not_fetched(self):
        """
        Fetch the object if it has not been fetched yet.
        """
        if not self._fetched:
            self.fetch_data()
            self._fetched = True

    def fetch_data(self):
        """
        Fetch the data for the object.
        """
        raise NotImplementedError("fetch_data() must be implemented in subclasses")

    def __repr__(self):
        """
        Return a string representation of the object.
        """
        return f"{self.__class__.__name__}(id={self.obj_id})"

    def __getattr__(self, name):
        """
        Handles access to attributes. If the attribute isn't found directly,
        it triggers lazy loading and then looks for the attribute name as a
        key in the internal _data dictionary.
        """
        self._fetch_if_not_fetched()  # Ensure core data is fetched

        # --- Dynamic Part ---
        # After fetching, look for 'name' as a key in the _data dictionary
        if name in self._data:
            return self._data[name]
        # --------------------
        else:
            # If still not found after fetching, raise the original error
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
