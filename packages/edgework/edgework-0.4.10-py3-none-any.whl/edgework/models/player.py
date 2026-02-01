from datetime import datetime

from edgework.models.base import BaseNHLModel


class Player(BaseNHLModel):
    """Player model to store player information."""

    def __init__(self, edgework_client=None, obj_id=None, **kwargs):
        """
        Initialize a Player object with dynamic attributes.

        Args:
            edgework_client: The Edgework client (optional for player data from API)
            obj_id: The ID of the player object
            **kwargs: Dynamic attributes for player properties
        """
        super().__init__(edgework_client, obj_id)
        self._data = kwargs

        # Set the player_id as obj_id if provided in kwargs
        if "player_id" in kwargs:
            self.obj_id = kwargs["player_id"]

        # Mark as fetched since we're initializing with data
        if kwargs:
            self._fetched = True

    def __str__(self) -> str:
        """String representation showing player name and number.

        Returns:
            str: Formatted string with player name, number, and team abbreviation.
                Examples: "#97 Connor McDavid (EDM)", "Connor McDavid (EDM)",
                "#97 Connor McDavid", or "Connor McDavid".
        """
        first_name = self._data.get("first_name", "")
        last_name = self._data.get("last_name", "")
        sweater_number = self._data.get("sweater_number")
        team_abbr = self._data.get("current_team_abbr", "")

        name = f"{first_name} {last_name}".strip()
        if sweater_number and team_abbr:
            return f"#{sweater_number} {name} ({team_abbr})"
        elif team_abbr:
            return f"{name} ({team_abbr})"
        elif sweater_number:
            return f"#{sweater_number} {name}"
        else:
            return name

    def __repr__(self):
        """Developer representation of the Player object.

        Returns:
            str: Developer-friendly string representation showing the player ID.
                Example: "Player(id=8478402)".
        """
        player_id = self._data.get("player_id", self.obj_id)
        return f"Player(id={player_id})"

    def __eq__(self, other) -> bool:
        """Compare players by their player_id.

        Args:
            other: The other object to compare with.

        Returns:
            bool: True if both objects are Player instances with the same player_id,
                False otherwise.
        """
        if isinstance(other, Player):
            return self._data.get("player_id") == other._data.get("player_id")
        return False

    def __hash__(self):
        """Hash based on player_id for use in sets and dicts.

        Returns:
            int: Hash value based on the player_id.
        """
        return hash(self._data.get("player_id"))

    def fetch_data(self):
        """Fetch the data for the player from the API.

        Uses the NHL Web API player landing endpoint to get detailed player information.

        Raises:
            ValueError: If no client is available to fetch player data.
            ValueError: If no player ID is available to fetch data.
        """
        if not self._client:
            raise ValueError("No client available to fetch player data")
        if not self.obj_id:
            raise ValueError("No player ID available to fetch data")

        # Import here to avoid circular imports
        from edgework.clients.player_client import landing_to_dict

        # Call the NHL Web API player landing endpoint
        response = self._client.get(f"player/{self.obj_id}/landing", web=True)
        data = response.json()

        # Convert API response to our player dictionary format
        player_data = landing_to_dict(data)

        # Update our internal data with the fetched information
        self._data.update(player_data)

        # Mark as fetched
        self._fetched = True

    @property
    def full_name(self):
        """Get the player's full name.

        Returns:
            str: The player's full name (first name + last name).
                Example: "Connor McDavid".
        """
        first_name = self._data.get("first_name", "")
        last_name = self._data.get("last_name", "")
        return f"{first_name} {last_name}".strip()

    @property
    def name(self):
        """Alias for full_name.

        Returns:
            str: The player's full name (first name + last name).
                Example: "Connor McDavid".
        """
        return self.full_name

    @property
    def age(self):
        """Calculate player's age from birth_date.

        Returns:
            int | None: The player's age in years, or None if birth_date is not available
                or cannot be parsed.
        """
        birth_date = self._data.get("birth_date")
        if birth_date:
            if isinstance(birth_date, str):
                birth_date = datetime.fromisoformat(birth_date.replace("Z", "+00:00"))
            elif isinstance(birth_date, datetime):
                pass
            else:
                return None

            today = datetime.now()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (
                today.month == birth_date.month and today.day < birth_date.day
            ):
                age -= 1
            return age
        return None

    @property
    def headshot(self):
        """Get the player's headshot image URL.

        Returns:
            str | None: URL to the player's headshot image, or None if not available.
        """
        return self._data.get("headshot")

    @property
    def hero_image(self):
        """Get the player's action shot/hero image URL.

        Returns:
            str | None: URL to the player's hero image, or None if not available.
        """
        return self._data.get("hero_image")

    @property
    def awards(self):
        """Get the player's awards and trophies.

        Returns:
            list | None: List of awards with trophy names and season details,
                or None if not available.
        """
        return self._data.get("awards")

    @property
    def badges(self):
        """Get the player's special badges (e.g., All-Star, events).

        Returns:
            list | None: List of special badges with logos and titles,
                or None if not available.
        """
        return self._data.get("badges")

    @property
    def team_logo(self):
        """Get the current team's logo URL.

        Returns:
            str | None: URL to the current team's logo, or None if not available.
        """
        return self._data.get("team_logo")

    @property
    def last_5_games(self):
        """Get the player's last 5 games statistics.

        Returns:
            list | None: List of the last 5 games with stats, or None if not available.
        """
        return self._data.get("last5_games")

    @property
    def season_totals(self):
        """Get the player's season-by-season statistics.

        Returns:
            list | None: List of season totals for each year played,
                or None if not available.
        """
        return self._data.get("season_totals")

    @property
    def current_team_roster(self):
        """Get the player's current team roster.

        Returns:
            list | None: List of current teammates, or None if not available.
        """
        return self._data.get("current_team_roster")

    @property
    def birth_city(self):
        """Get the player's birth city.

        Returns:
            str | None: The player's birth city, or None if not available.
        """
        return self._data.get("birth_city")

    @property
    def birth_state_province(self):
        """Get the player's birth state or province.

        Returns:
            str | None: The player's birth state/province, or None if not available.
        """
        return self._data.get("birth_state_province")

    @property
    def birth_country(self):
        """Get the player's birth country.

        Returns:
            str | None: The player's birth country code, or None if not available.
        """
        return self._data.get("birth_country")

    @property
    def height_formatted(self):
        """Get the player's height in formatted string (e.g., '6\' 1"').

        Returns:
            str | None: Formatted height string, or None if not available.
        """
        return self._data.get("height_formatted")

    @property
    def weight(self):
        """Get the player's weight in kilograms.

        Returns:
            int | None: Weight in kilograms, or None if not available.
        """
        return self._data.get("weight")

    @property
    def weight_pounds(self):
        """Get the player's weight in pounds.

        Returns:
            int | None: Weight in pounds, or None if not available.
        """
        return self._data.get("weight_pounds")

    @property
    def draft_year(self):
        """Get the player's draft year.

        Returns:
            datetime | int | None: Draft year as datetime object or integer,
                or None if not available.
        """
        return self._data.get("draft_year")

    @property
    def draft_round(self):
        """Get the player's draft round.

        Returns:
            int | None: Draft round number, or None if not available.
        """
        return self._data.get("draft_round")

    @property
    def draft_overall_pick(self):
        """Get the player's overall draft pick number.

        Returns:
            int | None: Overall pick number, or None if not available.
        """
        return self._data.get("draft_overall_pick")

    @property
    def career_totals(self):
        """Get the player's career totals (regular season and playoffs).

        Returns:
            dict | None: Dictionary with career statistics, or None if not available.
                Contains keys like 'career_totals_regular_season_goals',
                'career_totals_playoffs_assists', etc.
        """
        # Extract all career_totals_* keys from _data
        career_data = {
            k: v for k, v in self._data.items() if k.startswith("career_totals_")
        }
        return career_data if career_data else None

    def get_attribute(self, attr_name):
        """Get any attribute from the player data.

        Args:
            attr_name (str): The name of the attribute to retrieve.

        Returns:
            Any: The value of the attribute, or None if not found.

        Example:
            >>> player.get_attribute('shop_link')
            >>> player.get_attribute('featured_stats_regular_season_sub_season_goals')
        """
        return self._data.get(attr_name)

    def get_all_attributes(self):
        """Get all available attributes for this player.

        Returns:
            dict: Dictionary of all player attributes and their values.
        """
        return dict(self._data)

    def list_attributes(self, filter_prefix=None):
        """List all available attribute names.

        Args:
            filter_prefix (str, optional): Only show attributes starting with this prefix.

        Returns:
            list: List of attribute names.

        Example:
            >>> player.list_attributes()  # All attributes
            >>> player.list_attributes('career_totals_')  # Only career totals
            >>> player.list_attributes('featured_stats_')  # Only featured stats
        """
        if filter_prefix:
            return [k for k in self._data.keys() if k.startswith(filter_prefix)]
        return list(self._data.keys())
