from datetime import datetime
from typing import List, Optional, Union

from edgework.models.base import BaseNHLModel
from edgework.models.player import Player


def roster_api_to_dict(data: dict) -> dict:
    """Convert roster API response data to roster dictionary format."""
    # The API returns forwards, defensemen, goalies arrays directly
    players = []
    players.extend(data.get("forwards", []))
    players.extend(data.get("defensemen", []))
    players.extend(data.get("goalies", []))

    return {
        "season": data.get("season"),
        "roster_type": data.get("rosterType"),
        "team_abbrev": data.get("teamAbbrev"),
        "team_id": data.get("teamId"),
        "players": players,
    }


def team_api_to_dict(data: dict) -> dict:
    """
    Convert team API response data to team dictionary format with snake_case keys.

    This function processes team dictionary structures from various NHL APIs,
    converting camelCase keys to snake_case and handling nested dictionaries.
    It automatically extracts 'default' values from nested objects when available.

    Args:
        data: Raw API response dictionary from standings, roster, or other team endpoints

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
            from datetime import datetime

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
        """Flatten nested objects with special handling for known team structures."""
        for key, value in data.items():
            snake_key = camel_to_snake(key)

            # Special handling for franchise details
            if key == "franchise" and isinstance(value, dict):
                for franchise_key, franchise_value in value.items():
                    franchise_snake_key = f"franchise_{camel_to_snake(franchise_key)}"
                    result[franchise_snake_key] = process_value(franchise_value)

            # Special handling for venue details
            elif key == "venue" and isinstance(value, dict):
                for venue_key, venue_value in value.items():
                    venue_snake_key = f"venue_{camel_to_snake(venue_key)}"
                    result[venue_snake_key] = process_value(venue_value)

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

    # Ensure we have standard team fields with fallbacks
    result["team_id"] = result.get("team_id") or result.get("id")

    return result


class Roster(BaseNHLModel):
    """Roster model to store a team's roster information."""

    def __init__(self, edgework_client, obj_id=None, **kwargs):
        """
        Initialize a Roster object with dynamic attributes.

        Args:
            edgework_client: The Edgework client
            obj_id: The ID of the roster (team_id)
            **kwargs: Dynamic attributes for roster properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs
        self._players: List[Player] = []

        # Process players data if provided
        if "players" in self._data and self._data["players"]:
            self._process_players()
        # Mark as fetched if we have data
        if kwargs:
            self._fetched = True

    def _process_players(self):
        """Process raw player data into Player objects."""
        players_data = self._data.get("players", [])
        self._players = []

        for player_data in players_data:
            # Handle nested name structure
            first_name = player_data.get("firstName", {})
            if isinstance(first_name, dict):
                first_name = first_name.get("default", "")

            last_name = player_data.get("lastName", {})
            if isinstance(last_name, dict):
                last_name = last_name.get("default", "")

            birth_city = player_data.get("birthCity", {})
            if isinstance(birth_city, dict):
                birth_city = birth_city.get("default", "")

            birth_country = player_data.get("birthCountry", "")
            if isinstance(birth_country, dict):
                birth_country = birth_country.get("default", "")

            birth_state_province = player_data.get("birthStateProvince", {})
            if isinstance(birth_state_province, dict):
                birth_state_province = birth_state_province.get("default", "")

            # Convert player data to expected format
            player_dict = {
                "player_id": player_data.get("id"),
                "first_name": first_name,
                "last_name": last_name,
                "sweater_number": player_data.get("sweaterNumber"),
                "position": player_data.get("positionCode"),
                "shoots_catches": player_data.get("shootsCatches"),
                "height": player_data.get("heightInCentimeters"),
                "weight": player_data.get("weightInKilograms"),
                "birth_date": player_data.get("birthDate"),
                "birth_city": birth_city,
                "birth_country": birth_country,
                "birth_state_province": birth_state_province,
                "current_team_id": self._data.get("team_id"),
                "current_team_abbr": self._data.get("team_abbrev"),
                "is_active": True,
                "headshot": player_data.get("headshot"),
            }

            player = Player(self._client, player_dict["player_id"], **player_dict)
            self._players.append(player)

    @property
    def players(self) -> List[Player]:
        """
        Get all players in the roster.

        Returns:
            List[Player]: List of all players in the roster.
        """
        return self._players

    def get_player_by_number(self, sweater_number: int) -> Optional[Player]:
        """
        Get a player by their sweater number.

        Args:
            sweater_number: The player's sweater number

        Returns:
            Player: The player with the given number, or None if not found.
        """
        for player in self._players:
            if player.sweater_number == sweater_number:
                return player
        return None

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """
        Get a player by their full name.

        Args:
            name: The player's full name

        Returns:
            Player: The player with the given name, or None if not found.
        """
        for player in self._players:
            if player.full_name == name:
                return player
        return None

    @property
    def forwards(self) -> list[Player]:
        """
        Get the forwards from the roster.

        Returns:
            list[Player]: List of forwards in the roster.
        """
        return [p for p in self._players if p.position in {"C", "LW", "RW"}]

    @property
    def defensemen(self) -> list[Player]:
        """
        Get the defensemen from the roster.

        Returns:
            list[Player]: List of defensemen in the roster.
        """
        return [p for p in self._players if p.position == "D"]

    @property
    def goalies(self) -> list[Player]:
        """
        Get the goalies from the roster.

        Returns:
            list[Player]: List of goalies in the roster.
        """
        return [p for p in self._players if p.position == "G"]

    def fetch_data(self):
        """
        Fetch the roster data from the API.
        """
        if not self._client:
            raise ValueError("No client available to fetch roster data")
        if not self.obj_id:
            raise ValueError("No team ID available to fetch roster data")
        # Use current roster endpoint
        response = self._client.get(f"roster/{self.obj_id}/current", web=True)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch roster: {response.status_code} {response.text}"
            )

        data = response.json()
        self._data = roster_api_to_dict(data)
        self._process_players()
        self._fetched = True


class Team(BaseNHLModel):
    """Team model to store team information."""

    def __init__(self, edgework_client=None, obj_id=None, **kwargs):
        """
        Initialize a Team object with dynamic attributes.

        Args:
            edgework_client: The Edgework client (optional for team data from API)
            obj_id: The ID of the team object
            **kwargs: Dynamic attributes for team properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

        # Set the team_id as obj_id if provided in kwargs
        if "team_id" in kwargs:
            self.obj_id = kwargs["team_id"]

        # Mark as fetched since we're initializing with data
        self._fetched = True

    def __str__(self) -> str:
        """String representation showing team name and abbreviation.

        Returns:
            str: Formatted string with team name and abbreviation.
                Examples: "Toronto Maple Leafs (TOR)", "Edmonton Oilers (EDM)",
                or just "Toronto Maple Leafs" if no abbreviation available.
        """
        team_name = self._data.get("team_name") or self._data.get("full_name", "")
        team_abbrev = self._data.get("team_abbrev", "")

        if team_name and team_abbrev:
            return f"{team_name} ({team_abbrev})"
        elif team_name:
            return team_name
        elif team_abbrev:
            return team_abbrev
        else:
            return "Unknown Team"

    def __repr__(self):
        """Developer representation of the Team object.

        Returns:
            str: Developer-friendly string representation showing the team ID.
                Example: "Team(id=10)".
        """
        team_id = self._data.get("team_id", self.obj_id)
        return f"Team(id={team_id})"

    def __eq__(self, other) -> bool:
        """Compare teams by their team_id.

        Args:
            other: The other object to compare with.

        Returns:
            bool: True if both objects are Team instances with the same team_id,
                False otherwise.
        """
        if isinstance(other, Team):
            return self._data.get("team_id") == other._data.get("team_id")
        return False

    def __hash__(self):
        """Hash based on team_id for use in sets and dicts.

        Returns:
            int: Hash value based on the team_id.
        """
        return hash(self._data.get("team_id"))

    def fetch_data(self):
        """Fetch the data for the team from the API.

        Uses the NHL Stats API team endpoint to get detailed team information.

        Raises:
            ValueError: If no client is available to fetch team data.
            ValueError: If no team ID is available to fetch data.
        """
        if not self._client:
            raise ValueError("No client available to fetch team data")
        if not self.obj_id:
            raise ValueError("No team ID available to fetch data")

        # Use the NHL Stats API team endpoint
        response = self._client.get(f"team/{self.obj_id}", web=False)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch team data: {response.status_code} {response.text}"
            )

        data = response.json()

        # Convert API response to our team dictionary format
        team_data = team_api_to_dict(data)

        # Update our internal data with the fetched information
        self._data.update(team_data)

        # Mark as fetched
        self._fetched = True

    @property
    def name(self) -> str:
        """Get the team's name.

        Returns:
            str: The team's name.
                Example: "Toronto Maple Leafs".
        """
        return (
            self._data.get("team_name") or self._data.get("full_name") or "Unknown Team"
        )

    @property
    def abbrev(self) -> str:
        """Get the team's abbreviation.

        Returns:
            str: The team's abbreviation.
                Example: "TOR".
        """
        return self._data.get("tri_code", "UNK")

    @property
    def full_name(self) -> str:
        """Get the team's full name.

        Returns:
            str: The team's full name.
                Example: "Toronto Maple Leafs".
        """
        return self._data.get("full_name") or self.name

    @property
    def location(self) -> str:
        """Get the team's location.

        Returns:
            str: The team's location/city.
                Example: "Toronto".
        """
        return self._data.get("location_name", "")

    @property
    def common_name(self) -> str:
        """Get the team's common name.

        Returns:
            str: The team's common name.
                Example: "Maple Leafs".
        """
        return self._data.get("team_common_name", "")

    def get_roster(self, season: Optional[int] = None) -> Roster:
        """
        Get the roster for this team.

        Args:
            season: Optional season (e.g., 20232024). If None, gets current roster.

        Returns:
            Roster: The team's roster.
        """
        if not self._client:
            raise ValueError("No client available to fetch roster")

        team_abbrev = self.abbrev
        if season:
            response = self._client.get(f"roster/{team_abbrev}/{season}", web=True)
        else:
            response = self._client.get(f"roster/{team_abbrev}/current", web=True)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch roster: {response.status_code} {response.text}"
            )

        data = response.json()
        roster_data = roster_api_to_dict(data)
        roster_data["team_id"] = self._data.get("team_id")
        roster_data["team_abbrev"] = team_abbrev

        return Roster(self._client, self._data.get("team_id"), **roster_data)

    def get_stats(self, season: Optional[int] = None, game_type: int = 2):
        """
        Get team stats.

        Args:
            season: Optional season (e.g., 20232024). If None, gets current season.
            game_type: Game type (2 for regular season, 3 for playoffs).

        Returns:
            Response with team stats.
        """
        if not self._client:
            raise ValueError("No client available to fetch stats")

        team_abbrev = self.abbrev
        if season:
            response = self._client.get(
                f"club-stats/{team_abbrev}/{season}/{game_type}", web=True
            )
        else:
            response = self._client.get(f"club-stats/{team_abbrev}/now", web=True)

        return response

    def get_schedule(self, season: Optional[int] = None):
        """
        Get team schedule.

        Args:
            season: Optional season (e.g., 20232024). If None, gets current season.

        Returns:
            Response with team schedule.
        """
        if not self._client:
            raise ValueError("No client available to fetch schedule")

        team_abbrev = self.abbrev
        if season:
            response = self._client.get(
                f"club-schedule-season/{team_abbrev}/{season}", web=True
            )
        else:
            response = self._client.get(
                f"club-schedule-season/{team_abbrev}/now", web=True
            )

        return response

    def get_prospects(self):
        """
        Get team prospects.

        Returns:
            Response with team prospects.
        """
        if not self._client:
            raise ValueError("No client available to fetch prospects")

        team_abbrev = self.abbrev
        response = self._client.get(f"prospects/{team_abbrev}", web=True)

        return response
