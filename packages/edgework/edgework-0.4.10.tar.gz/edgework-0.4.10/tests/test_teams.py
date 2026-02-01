"""Tests for team-related functionality in the Edgework client."""

import pytest

from edgework.edgework import Edgework
from edgework.models.player import Player
from edgework.models.team import Roster, Team


class TestTeamMethods:
    """Test class for team-related methods."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = Edgework()

    def test_get_teams(self):
        """Test that get_teams() returns a list of teams."""
        teams = self.client.get_teams()

        # Assert that we get teams
        assert isinstance(teams, list), "get_teams() should return a list"
        assert len(teams) > 0, "Should return at least some teams"
        assert len(teams) == 62, "Should return exactly 32 teams"

        # Check that all returned items are Team objects
        for team in teams:
            assert isinstance(team, Team), "Each item should be a Team object"
            assert hasattr(team, "_data"), "Team should have _data attribute"
            assert hasattr(team, "abbrev"), "Team should have abbrev property"
            assert hasattr(team, "name"), "Team should have name property"

    def test_get_roster_current(self):
        """Test that get_roster() returns a roster for a team."""
        # Use Toronto Maple Leafs as test team
        roster = self.client.get_roster("TOR")

        # Assert that we get a roster
        assert isinstance(roster, Roster), "get_roster() should return a Roster object"
        assert hasattr(roster, "players"), "Roster should have players property"

        # Check that roster has players
        players = roster.players
        assert isinstance(players, list), "Roster.players should return a list"
        assert len(players) > 0, "Roster should have at least some players"

        # Check that all players are Player objects
        for player in players:
            assert isinstance(player, Player), "Each player should be a Player object"

    def test_roster_position_properties(self):
        """Test that roster position properties work correctly."""
        roster = self.client.get_roster("TOR")

        # Test position properties
        forwards = roster.forwards
        defensemen = roster.defensemen
        goalies = roster.goalies

        assert isinstance(forwards, list), "forwards should return a list"
        assert isinstance(defensemen, list), "defensemen should return a list"
        assert isinstance(goalies, list), "goalies should return a list"

        # Check that we have players in each position
        assert len(forwards) > 0, "Should have at least some forwards"
        assert len(defensemen) > 0, "Should have at least some defensemen"
        assert len(goalies) > 0, "Should have at least some goalies"

        # Check position codes
        for forward in forwards:
            assert forward.position in [
                "C",
                "L",
                "R",
                "LW",
                "RW",
            ], f"Forward {forward} has invalid position: {forward.position}"

        for defenseman in defensemen:
            assert (
                defenseman.position == "D"
            ), f"Defenseman {defenseman} has invalid position: {defenseman.position}"

        for goalie in goalies:
            assert (
                goalie.position == "G"
            ), f"Goalie {goalie} has invalid position: {goalie.position}"

    def test_team_properties(self):
        """Test that Team objects have correct properties."""
        teams = self.client.get_teams()

        if teams:
            team = teams[0]  # Test with first team

            # Test basic properties
            assert hasattr(team, "name"), "Team should have name property"
            assert hasattr(team, "abbrev"), "Team should have abbrev property"
            assert hasattr(team, "full_name"), "Team should have full_name property"

            # Test string representation
            assert str(team) != "", "Team string representation should not be empty"
            assert repr(team) != "", "Team repr should not be empty"

            # Test equality
            same_team = teams[0]
            assert team == same_team, "Same team should be equal to itself"

    def test_team_methods(self):
        """Test that Team methods work correctly."""
        teams = self.client.get_teams()

        if teams:

            for team in teams:
                if team.tri_code == "TOR":
                    break

            # Test get_roster method
            roster = team.get_roster()
            assert isinstance(
                roster, Roster
            ), "Team.get_roster() should return a Roster object"

            # Test get_stats method (should return response object)
            stats_response = team.get_stats()
            assert hasattr(
                stats_response, "status_code"
            ), "get_stats should return a response object"

            # Test get_schedule method (should return response object)
            schedule_response = team.get_schedule()
            assert hasattr(
                schedule_response, "status_code"
            ), "get_schedule should return a response object"

    def test_roster_utility_methods(self):
        """Test roster utility methods."""
        roster = self.client.get_roster("TOR")

        # Test get_player_by_number if we have players with numbers
        players = roster.players
        if players:
            for player in players:
                if player.sweater_number:
                    found_player = roster.get_player_by_number(player.sweater_number)
                    assert (
                        found_player is not None
                    ), f"Should find player with number {player.sweater_number}"
                    assert (
                        found_player == player
                    ), "Found player should be the same as original"
                    break

        # Test get_player_by_name if we have players
        if players:
            player = players[0]
            found_player = roster.get_player_by_name(player.full_name)
            assert (
                found_player is not None
            ), f"Should find player with name {player.full_name}"
            assert found_player == player, "Found player should be the same as original"

    def teardown_method(self):
        """Clean up after each test method."""
        if hasattr(self.client, "close"):
            self.client.close()


class TestTeamIntegration:
    """Integration tests for team functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = Edgework()

    def test_full_team_workflow(self):
        """Test a complete workflow with teams and rosters."""
        # Get all teams
        teams = self.client.get_teams()
        assert len(teams) > 0, "Should have teams"

        # Pick a team (Toronto Maple Leafs)
        tor_team = None
        for team in teams:
            if team.abbrev == "TOR":
                tor_team = team
                break

        if tor_team:
            # Get roster
            roster = tor_team.get_roster()
            assert isinstance(roster, Roster), "Should get a roster"

            # Check positions
            assert len(roster.forwards) > 0, "Should have forwards"
            assert len(roster.defensemen) > 0, "Should have defensemen"
            assert len(roster.goalies) > 0, "Should have goalies"

            # Test player search
            if roster.players:
                first_player = roster.players[0]
                found_by_name = roster.get_player_by_name(first_player.full_name)
                assert found_by_name == first_player, "Should find player by name"

    def teardown_method(self):
        """Clean up after each test method."""
        if hasattr(self.client, "close"):
            self.client.close()
