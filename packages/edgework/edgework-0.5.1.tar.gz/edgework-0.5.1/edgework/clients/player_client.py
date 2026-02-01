"""Player client for fetching player data from NHL APIs."""

from datetime import datetime
from typing import List, Optional

from edgework.http_client import HttpClient
from edgework.models.player import Player


def api_to_dict(data: dict) -> dict:
    """Convert API response data to player dictionary format."""
    name = data.get("name", "")
    slug = (
        f"{name.replace(' ', '-').lower()}-{data.get('playerId')}"
        if name
        else f"player-{data.get('playerId')}"
    )

    # Split name into first and last name
    name_parts = name.split(" ") if name else []
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    return {
        "player_id": int(data.get("playerId")) if data.get("playerId") else None,
        "first_name": first_name,
        "last_name": last_name,
        "player_slug": slug,
        "sweater_number": data.get("sweaterNumber"),
        "birth_date": data.get(
            "birthDate"
        ),  # This field doesn't seem to be in the search API
        "birth_city": data.get("birthCity"),
        "birth_country": data.get("birthCountry"),
        "birth_state_province": data.get("birthStateProvince"),
        "height": data.get("heightInCentimeters"),
        "height_inches": data.get("heightInInches"),
        "height_formatted": data.get("height"),
        "weight": data.get("weightInKilograms"),
        "weight_pounds": data.get("weightInPounds"),
        "position": data.get("positionCode"),
        "is_active": data.get("active"),
        "current_team_id": int(data.get("teamId")) if data.get("teamId") else None,
        "current_team_abbr": data.get("teamAbbrev"),
        "last_team_id": int(data.get("lastTeamId")) if data.get("lastTeamId") else None,
        "last_team_abbr": data.get("lastTeamAbbrev"),
        "last_season_id": data.get("lastSeasonId"),
    }


def landing_to_dict(data: dict) -> dict:
    """
    Convert API response data to player dictionary format with snake_case keys.

    This function generically processes any dictionary structure from the API,
    converting camelCase keys to snake_case and handling nested dictionaries.
    It automatically extracts 'default' values from nested objects when available.

    Args:
        data: Raw API response dictionary

    Returns:
        Dictionary with snake_case field names and processed values
    """

    def camel_to_snake(name: str) -> str:
        """Convert camelCase to snake_case."""
        import re

        # Insert underscores before uppercase letters (except at start)
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        # Insert underscores between lowercase/digit and uppercase
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def process_value(value):
        """Process a value, handling nested dictionaries and special cases."""
        if value is None:
            return None

        # Handle nested dictionaries
        if isinstance(value, dict):
            # If it has a 'default' key, extract that value
            if "default" in value:
                return value["default"]
            # Otherwise, recursively process the nested dictionary
            return {camel_to_snake(k): process_value(v) for k, v in value.items()}

        # Handle lists
        elif isinstance(value, list):
            return [process_value(item) for item in value]

        # Handle date strings
        elif isinstance(value, str):
            # Try to parse common date formats
            date_formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]
            for fmt in date_formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            # If not a date, return as-is
            return value

        # Return primitive types as-is
        else:
            return value

    def flatten_nested_objects(data: dict, result: dict, parent_key: str = "") -> None:
        """Flatten nested objects with special handling for known structures."""
        for key, value in data.items():
            snake_key = camel_to_snake(key)

            # Special handling for draft details
            if key == "draftDetails" and isinstance(value, dict):
                for draft_key, draft_value in value.items():
                    draft_snake_key = f"draft_{camel_to_snake(draft_key)}"
                    if draft_key == "year" and draft_value:
                        try:
                            result[draft_snake_key] = datetime(draft_value, 1, 1)
                        except (ValueError, TypeError):
                            result[draft_snake_key] = draft_value
                    else:
                        result[draft_snake_key] = process_value(draft_value)

            # For other nested objects, process normally
            elif isinstance(value, dict) and "default" not in value:
                # If it's a complex nested object, flatten it with prefix
                if parent_key:
                    new_key = f"{parent_key}_{snake_key}"
                else:
                    new_key = snake_key
                flatten_nested_objects(value, result, new_key)

            else:
                # Process the value (will handle 'default' extraction)
                final_key = f"{parent_key}_{snake_key}" if parent_key else snake_key
                result[final_key] = process_value(value)

    result = {}
    flatten_nested_objects(data, result)

    return result


class PlayerClient:
    """Client for fetching player data."""

    def __init__(self, http_client: HttpClient):
        """
        Initialize the player client.

        Args:
            http_client: HTTP client instance
        """
        self.client = http_client
        self.base_url = "https://search.d3.nhle.com/api/v1/search/player"

    def get_all_players(
        self, active: Optional[bool] = None, limit: int = 10000
    ) -> List[Player]:
        """
        Get all players from the NHL search API.

        Args:
            active: Filter by active status (True for active, False for inactive, None for all)
            limit: Maximum number of players to return

        Returns:
            List of Player objects
        """
        params = {"culture": "en-us", "limit": limit, "q": "*"}
        if active is not None:
            params["active"] = str(active).lower()

        response = self.client.get_raw(self.base_url, params=params)
        data = response.json()

        # The API returns a list directly, not a dict with "results"
        if isinstance(data, list):
            players_data = data
        else:
            # Fallback in case the API structure changes
            players_data = data.get("results", [])

        return [Player(**api_to_dict(player)) for player in players_data]

    def get_active_players(self, limit: int = 10000) -> List[Player]:
        """
        Get all active players.

        Args:
            limit: Maximum number of players to return

        Returns:
            List of active Player objects
        """
        return self.get_all_players(active=True, limit=limit)

    def get_inactive_players(self, limit: int = 10000) -> List[Player]:
        """
        Get all inactive players.

        Args:
            limit: Maximum number of players to return

        Returns:
            List of inactive Player objects
        """
        return self.get_all_players(active=False, limit=limit)
