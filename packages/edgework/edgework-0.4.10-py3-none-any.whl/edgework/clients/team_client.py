from typing import List, Optional

from httpx import Client

from edgework.models.team import Roster, Team, roster_api_to_dict, team_api_to_dict


class TeamClient:
    """Client for team-related API operations."""

    def __init__(self, client: Client):
        self.client = client

    def get_teams(self) -> List[Team]:
        """
        Fetch a list of teams from NHL Stats API.

        Returns
        -------
        List[Team]
            A list of teams.
        """
        # Use the NHL Stats API teams endpoint
        response = self.client.get("team", web=False)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch teams: {response.status_code} {response.text}"
            )

        data = response.json()
        teams = []

        # The response should have a 'data' array containing team objects
        teams_data = data.get("data", [])

        for team_data in teams_data:
            processed_team_data = team_api_to_dict(team_data)
            team = Team(
                self.client, processed_team_data.get("team_id"), **processed_team_data
            )
            teams.append(team)

        return teams

    def get_team(self, team_id: int) -> Team:
        """
        Fetch a single team by ID from NHL Stats API.

        Parameters
        ----------
        team_id : int
            The team ID

        Returns
        -------
        Team
            A Team object.
        """
        # Use the NHL Stats API team endpoint for a specific team
        response = self.client.get(f"team/{team_id}", web=False)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch team {team_id}: {response.status_code} {response.text}"
            )

        data = response.json()

        # The response should have the team data directly or in a 'data' field
        team_data = data.get("data", [])
        if isinstance(team_data, list) and len(team_data) > 0:
            team_data = team_data[0]
        elif not isinstance(team_data, dict):
            team_data = data

        processed_team_data = team_api_to_dict(team_data)
        return Team(
            self.client, processed_team_data.get("team_id"), **processed_team_data
        )

    def get_roster(self, team_code: str, season: Optional[int] = None) -> Roster:
        """
        Fetch a roster for a team from NHL.

        Parameters
        ----------
        team_code : str
            The team code for the team (e.g., 'TOR', 'NYR')
        season : Optional[int]
            The season in YYYYYYYY format (e.g., 20232024). If None, gets current roster.

        Returns
        -------
        Roster
            A roster for the team.
        """
        if season:
            endpoint = f"roster/{team_code}/{season}"
        else:
            endpoint = f"roster/{team_code}/current"

        response = self.client.get(endpoint, web=True)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch roster: {response.status_code} {response.text}"
            )

        data = response.json()
        roster_data = roster_api_to_dict(data)

        # Extract team_id if available, otherwise use team_code
        team_id = roster_data.get("team_id")

        return Roster(self.client, team_id, **roster_data)

    def get_team_stats(
        self, team_code: str, season: Optional[int] = None, game_type: int = 2
    ):
        """
        Get team statistics.

        Parameters
        ----------
        team_code : str
            The team code for the team (e.g., 'TOR', 'NYR')
        season : Optional[int]
            The season in YYYYYYYY format (e.g., 20232024). If None, gets current stats.
        game_type : int
            Game type (2 for regular season, 3 for playoffs). Default is 2.

        Returns
        -------
        dict
            Team statistics data.
        """
        if season:
            endpoint = f"club-stats/{team_code}/{season}/{game_type}"
        else:
            endpoint = f"club-stats/{team_code}/now"

        response = self.client.get(endpoint, web=True)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch team stats: {response.status_code} {response.text}"
            )

        return response.json()

    def get_team_schedule(self, team_code: str, season: Optional[int] = None):
        """
        Get team schedule.

        Parameters
        ----------
        team_code : str
            The team code for the team (e.g., 'TOR', 'NYR')
        season : Optional[int]
            The season in YYYYYYYY format (e.g., 20232024). If None, gets current schedule.

        Returns
        -------
        dict
            Team schedule data.
        """
        if season:
            endpoint = f"club-schedule-season/{team_code}/{season}"
        else:
            endpoint = f"club-schedule-season/{team_code}/now"

        response = self.client.get(endpoint, web=True)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch team schedule: {response.status_code} {response.text}"
            )

        return response.json()

    def get_team_prospects(self, team_code: str):
        """
        Get team prospects.

        Parameters
        ----------
        team_code : str
            The team code for the team (e.g., 'TOR', 'NYR')

        Returns
        -------
        dict
            Team prospects data.
        """
        endpoint = f"prospects/{team_code}"
        response = self.client.get(endpoint, web=True)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch team prospects: {response.status_code} {response.text}"
            )

        return response.json()

    def get_scoreboard(self, team_code: str):
        """
        Get team scoreboard.

        Parameters
        ----------
        team_code : str
            The team code for the team (e.g., 'TOR', 'NYR')

        Returns
        -------
        dict
            Team scoreboard data.
        """
        endpoint = f"scoreboard/{team_code}/now"
        response = self.client.get(endpoint, web=True)

        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch team scoreboard: {response.status_code} {response.text}"
            )

        return response.json()
