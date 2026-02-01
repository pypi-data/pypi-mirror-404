from typing import List

from edgework.models.base import BaseNHLModel


class Term(BaseNHLModel):
    """Term model to store terminology information."""

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a Term object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the term object
            **kwargs: Dynamic attributes for term properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

    def fetch_data(self):
        """
        Fetch the data for the term.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")


class Glossary(BaseNHLModel):
    """Glossary model to store terminology entries."""

    def __init__(self, edgework_client, obj_id=None, terms=None):
        """
        Initialize a Glossary object.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the glossary
            terms: List of terminology entries
        """
        super().__init__(edgework_client, obj_id)
        self.terms = terms or []

    def fetch_data(self):
        """
        Fetch the data for the glossary.
        """
        # Implementation depends on how data is fetched from the API
        raise NotImplementedError("fetch_data() must be implemented in subclasses")
