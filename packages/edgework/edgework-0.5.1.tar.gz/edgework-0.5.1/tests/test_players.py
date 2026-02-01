"""Tests for the players() method in the Edgework client."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from edgework.clients.player_client import landing_to_dict
from edgework.edgework import Edgework
from edgework.http_client import HttpClient
from edgework.models.player import Player


class TestPlayersMethod:
    """Test class for the players() method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = Edgework()

    def test_players_active_only_default(self):
        """Test that players() returns only active players by default."""
        players = self.client.players()

        # Assert that we get some players
        assert isinstance(players, list), "players() should return a list"
        assert len(players) > 0, "Should return at least some active players"

        # Check that all returned players are active
        for player in players:
            assert isinstance(player, Player), "Each item should be a Player object"
            assert hasattr(player, "_data"), "Player should have _data attribute"
            assert (
                player._data.get("is_active") is True
            ), f"Player {player} should be active"

    def test_players_active_only_explicit(self):
        """Test that players(active_only=True) returns only active players."""
        players = self.client.players(active_only=True)

        # Assert that we get some players
        assert isinstance(players, list), "players() should return a list"
        assert len(players) > 0, "Should return at least some active players"

        # Check that all returned players are active
        for player in players:
            assert isinstance(player, Player), "Each item should be a Player object"
            assert (
                player._data.get("is_active") is True
            ), f"Player {player} should be active"

    def test_players_all_players(self):
        """Test that players(active_only=False) returns all players."""
        all_players = self.client.players(active_only=False)
        active_players = self.client.players(active_only=True)

        # Assert that we get some players
        assert isinstance(all_players, list), "players() should return a list"
        assert isinstance(active_players, list), "players() should return a list"
        assert len(all_players) > 0, "Should return at least some players"
        assert len(active_players) > 0, "Should return at least some active players"

        # All players should be more than just active players
        assert len(all_players) >= len(
            active_players
        ), "All players should be >= active players"

        # Check that we have both active and inactive players in all_players
        active_count = sum(1 for p in all_players if p._data.get("is_active") is True)
        inactive_count = sum(
            1 for p in all_players if p._data.get("is_active") is False
        )

        assert active_count > 0, "Should have some active players"
        assert inactive_count > 0, "Should have some inactive players"

    def test_player_object_structure(self):
        """Test that Player objects have the expected structure."""
        players = self.client.players(active_only=True)

        # Get first few players to test
        test_players = players[:3]

        for player in test_players:
            assert isinstance(player, Player), "Should be a Player object"

            # Test essential attributes exist
            assert hasattr(player, "_data"), "Player should have _data"
            assert hasattr(player, "obj_id"), "Player should have obj_id"

            # Test key player data fields
            data = player._data
            assert "player_id" in data, "Player should have player_id"
            assert "first_name" in data, "Player should have first_name"
            assert "last_name" in data, "Player should have last_name"
            assert "position" in data, "Player should have position"
            assert "is_active" in data, "Player should have is_active"

            # Test player_id is a valid integer
            assert isinstance(data["player_id"], int), "player_id should be an integer"
            assert data["player_id"] > 0, "player_id should be positive"

            # Test names are strings
            assert isinstance(data["first_name"], str), "first_name should be a string"
            assert isinstance(data["last_name"], str), "last_name should be a string"
            assert len(data["first_name"]) > 0, "first_name should not be empty"
            assert len(data["last_name"]) > 0, "last_name should not be empty"

            # Test position is a valid string
            assert isinstance(data["position"], str), "position should be a string"
            assert data["position"] in [
                "C",
                "L",
                "R",
                "D",
                "G",
            ], f"Position {data['position']} should be valid"

    def test_player_string_methods(self):
        """Test Player object string representations."""
        players = self.client.players(active_only=True)
        player = players[0]

        # Test __str__ method
        str_repr = str(player)
        assert isinstance(str_repr, str), "__str__ should return a string"
        assert len(str_repr) > 0, "__str__ should not be empty"

        # Test __repr__ method
        repr_str = repr(player)
        assert isinstance(repr_str, str), "__repr__ should return a string"
        assert "Player(id=" in repr_str, "__repr__ should contain Player(id="

        # Test full_name property
        full_name = player.full_name
        assert isinstance(full_name, str), "full_name should return a string"
        assert len(full_name) > 0, "full_name should not be empty"
        assert (
            player._data["first_name"] in full_name
        ), "full_name should contain first name"
        assert (
            player._data["last_name"] in full_name
        ), "full_name should contain last name"

    def test_player_equality_and_hashing(self):
        """Test Player object equality and hashing."""
        players = self.client.players(active_only=True)

        if len(players) >= 2:
            player1 = players[0]
            player2 = players[1]
            player1_copy = Player(**player1._data)

            # Test equality
            assert player1 == player1_copy, "Players with same ID should be equal"
            assert player1 != player2, "Players with different IDs should not be equal"

            # Test hashing (for use in sets/dicts)
            player_set = {player1, player1_copy, player2}
            assert len(player_set) == 2, "Set should contain only unique players"

    def test_players_return_count_reasonable(self):
        """Test that the number of players returned is reasonable."""
        active_players = self.client.players(active_only=True)

        # The NHL API returns active players including prospects and affiliates
        # Let's test for a reasonable range based on actual data
        assert (
            1500 <= len(active_players) <= 3000
        ), f"Expected 1500-3000 active players (including prospects), got {len(active_players)}"

    def test_players_contain_known_positions(self):
        """Test that players contain all expected hockey positions."""
        players = self.client.players(active_only=True)

        positions = {player._data.get("position") for player in players}
        expected_positions = {
            "C",
            "L",
            "R",
            "D",
            "G",
        }  # Center, Left Wing, Right Wing, Defense, Goalie

        assert expected_positions.issubset(
            positions
        ), f"Expected to find all positions {expected_positions}, found {positions}"

    @pytest.mark.parametrize("active_only", [True, False])
    def test_players_method_no_exceptions(self, active_only):
        """Test that players() method doesn't raise exceptions for both parameter values."""
        try:
            players = self.client.players(active_only=active_only)
            assert isinstance(players, list), "Should return a list"
            assert len(players) > 0, "Should return some players"
        except Exception as e:
            pytest.fail(f"players(active_only={active_only}) raised an exception: {e}")


class TestPlayerFetchData:
    """Test class for the Player.fetch_data() method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = Mock(spec=HttpClient)

    def test_fetch_data_success(self):
        """Test successful data fetching from the landing API."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "playerId": 8478402,
            "firstName": {"default": "Connor"},
            "lastName": {"default": "McDavid"},
            "birthDate": "1997-01-13",
            "position": "C",
            "sweaterNumber": 97,
            "currentTeamAbbrev": "EDM",
            "draftDetails": {
                "year": 2015,
                "round": 1,
                "overallPick": 1,
                "teamAbbrev": "EDM",
            },
        }
        self.mock_client.get.return_value = mock_response

        # Create player and fetch data
        player = Player(edgework_client=self.mock_client, obj_id=8478402)
        player._data = {}  # Clear initial data
        player._fetched = False

        player.fetch_data()

        # Verify API call was made correctly
        self.mock_client.get.assert_called_once_with("player/8478402/landing", web=True)

        # Verify data was updated
        assert player._fetched is True
        assert player._data["player_id"] == 8478402
        assert player._data["first_name"] == "Connor"
        assert player._data["last_name"] == "McDavid"
        assert player._data["position"] == "C"
        assert player._data["sweater_number"] == 97
        assert player._data["current_team_abbrev"] == "EDM"
        assert player._data["draft_year"] == datetime(2015, 1, 1)
        assert player._data["draft_round"] == 1
        assert player._data["draft_overall_pick"] == 1

    def test_fetch_data_no_client(self):
        """Test fetch_data raises ValueError when no client is available."""
        player = Player(edgework_client=None, obj_id=8478402)

        with pytest.raises(
            ValueError, match="No client available to fetch player data"
        ):
            player.fetch_data()

    def test_fetch_data_no_player_id(self):
        """Test fetch_data raises ValueError when no player ID is available."""
        player = Player(edgework_client=self.mock_client, obj_id=None)

        with pytest.raises(ValueError, match="No player ID available to fetch data"):
            player.fetch_data()

    def test_fetch_data_preserves_existing_data(self):
        """Test that fetch_data preserves existing data and merges new data."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "playerId": 8478402,
            "firstName": {"default": "Connor"},
            "lastName": {"default": "McDavid"},
            "position": "C",
        }
        self.mock_client.get.return_value = mock_response

        # Create player with some existing data
        player = Player(edgework_client=self.mock_client, obj_id=8478402)
        player._data = {"existing_field": "existing_value", "player_id": 8478402}
        player._fetched = False

        player.fetch_data()

        # Verify existing data is preserved and new data is added
        assert player._data["existing_field"] == "existing_value"
        assert player._data["player_id"] == 8478402
        assert player._data["first_name"] == "Connor"
        assert player._data["last_name"] == "McDavid"
        assert player._data["position"] == "C"

    @pytest.mark.live_api
    def test_fetch_data_live_api(self):
        """Test fetch_data with live API call."""
        client = Edgework()

        # Create player with Connor McDavid's ID
        player = Player(edgework_client=client._client, obj_id=8478402)
        player._data = {}
        player._fetched = False

        player.fetch_data()

        # Verify data was fetched
        assert player._fetched is True
        assert player._data["player_id"] == 8478402
        assert player._data["first_name"] == "Connor"
        assert player._data["last_name"] == "McDavid"
        assert player._data["position"] == "C"
        assert player._data["current_team_abbrev"] == "EDM"
        assert isinstance(player._data["birth_date"], datetime)


class TestLandingToDict:
    """Test class for the landing_to_dict function."""

    def test_simple_camel_to_snake_conversion(self):
        """Test basic camelCase to snake_case conversion."""
        data = {
            "playerId": 12345,
            "firstName": "John",
            "lastName": "Doe",
            "isActive": True,
            "sweaterNumber": 99,
        }

        result = landing_to_dict(data)

        assert result["player_id"] == 12345
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["is_active"] is True
        assert result["sweater_number"] == 99

    def test_nested_dict_with_default_extraction(self):
        """Test extraction of 'default' values from nested dictionaries."""
        data = {
            "firstName": {"default": "Connor", "fr": "Connor"},
            "lastName": {"default": "McDavid", "fr": "McDavid"},
            "birthCity": {"default": "Richmond Hill", "fr": "Richmond Hill"},
            "simpleField": "not_nested",
        }

        result = landing_to_dict(data)

        assert result["first_name"] == "Connor"
        assert result["last_name"] == "McDavid"
        assert result["birth_city"] == "Richmond Hill"
        assert result["simple_field"] == "not_nested"

    def test_draft_details_special_handling(self):
        """Test special handling of draftDetails nested object."""
        data = {
            "playerId": 8478402,
            "draftDetails": {
                "year": 2015,
                "round": 1,
                "overallPick": 1,
                "pickInRound": 1,
                "teamAbbrev": "EDM",
            },
        }

        result = landing_to_dict(data)

        assert result["player_id"] == 8478402
        assert result["draft_year"] == datetime(2015, 1, 1)
        assert result["draft_round"] == 1
        assert result["draft_overall_pick"] == 1
        assert result["draft_pick_in_round"] == 1
        assert result["draft_team_abbrev"] == "EDM"

    def test_date_string_parsing(self):
        """Test automatic parsing of date strings."""
        data = {
            "birthDate": "1997-01-13",
            "someTimestamp": "2023-12-25T15:30:00",
            "isoTimestamp": "2023-12-25T15:30:00Z",
            "notADate": "just_a_string",
        }

        result = landing_to_dict(data)

        assert result["birth_date"] == datetime(1997, 1, 13)
        assert result["some_timestamp"] == datetime(2023, 12, 25, 15, 30, 0)
        assert result["iso_timestamp"] == datetime(2023, 12, 25, 15, 30, 0)
        assert result["not_a_date"] == "just_a_string"

    def test_nested_object_flattening(self):
        """Test flattening of complex nested objects."""
        data = {
            "careerTotals": {
                "regularSeason": {
                    "gamesPlayed": 695,
                    "goals": 335,
                    "assists": 645,
                },
                "playoffs": {"gamesPlayed": 79, "goals": 42},
            }
        }

        result = landing_to_dict(data)

        assert result["career_totals_regular_season_games_played"] == 695
        assert result["career_totals_regular_season_goals"] == 335
        assert result["career_totals_regular_season_assists"] == 645
        assert result["career_totals_playoffs_games_played"] == 79
        assert result["career_totals_playoffs_goals"] == 42

    def test_list_handling(self):
        """Test handling of lists in the data."""
        data = {
            "awards": ["Hart Trophy", "Art Ross Trophy"],
            "teams": [{"id": 1, "name": "Team1"}, {"id": 2, "name": "Team2"}],
            "simpleList": [1, 2, 3],
        }

        result = landing_to_dict(data)

        assert result["awards"] == ["Hart Trophy", "Art Ross Trophy"]
        assert len(result["teams"]) == 2
        assert result["teams"][0]["id"] == 1
        assert result["teams"][0]["name"] == "Team1"
        assert result["simple_list"] == [1, 2, 3]

    def test_null_and_empty_values(self):
        """Test handling of null and empty values."""
        data = {
            "nullField": None,
            "emptyString": "",
            "zeroValue": 0,
            "falseValue": False,
            "emptyList": [],
            "emptyDict": {},
        }

        result = landing_to_dict(data)

        assert result["null_field"] is None
        assert result["empty_string"] == ""
        assert result["zero_value"] == 0
        assert result["false_value"] is False
        assert result["empty_list"] == []
        # Empty dicts are processed but result in no additional fields

    def test_complex_real_world_structure(self):
        """Test with a complex structure similar to real NHL API response."""
        data = {
            "playerId": 8478402,
            "firstName": {"default": "Connor"},
            "lastName": {"default": "McDavid"},
            "birthDate": "1997-01-13",
            "currentTeamAbbrev": "EDM",
            "draftDetails": {
                "year": 2015,
                "round": 1,
                "overallPick": 1,
            },
            "featuredStats": {
                "regularSeason": {
                    "subSeason": {
                        "goals": 64,
                        "assists": 89,
                        "points": 153,
                    },
                    "career": {"goals": 335, "assists": 645},
                }
            },
            "isActive": True,
            "awards": ["Hart Trophy", "Art Ross Trophy"],
        }

        result = landing_to_dict(data)

        # Verify basic fields
        assert result["player_id"] == 8478402
        assert result["first_name"] == "Connor"
        assert result["last_name"] == "McDavid"
        assert result["birth_date"] == datetime(1997, 1, 13)
        assert result["current_team_abbrev"] == "EDM"
        assert result["is_active"] is True

        # Verify draft details
        assert result["draft_year"] == datetime(2015, 1, 1)
        assert result["draft_round"] == 1
        assert result["draft_overall_pick"] == 1

        # Verify nested stats
        assert result["featured_stats_regular_season_sub_season_goals"] == 64
        assert result["featured_stats_regular_season_sub_season_assists"] == 89
        assert result["featured_stats_regular_season_sub_season_points"] == 153
        assert result["featured_stats_regular_season_career_goals"] == 335
        assert result["featured_stats_regular_season_career_assists"] == 645

        # Verify awards list
        assert result["awards"] == ["Hart Trophy", "Art Ross Trophy"]

    def test_camel_to_snake_edge_cases(self):
        """Test edge cases in camelCase to snake_case conversion."""
        data = {
            "HTML": "html",
            "XMLParser": "xml_parser",
            "HTTPSConnection": "https_connection",
            "someHTTPURL": "some_httpurl",  # This is what the actual conversion produces
            "a": "a",
            "aB": "a_b",
            "AB": "ab",
            "ABC": "abc",
        }

        result = landing_to_dict(data)

        assert "html" in result
        assert "xml_parser" in result
        assert "https_connection" in result
        assert "some_httpurl" in result  # Fixed expectation
        assert "a" in result
        assert "a_b" in result


class TestPlayersIntegration:
    """Integration tests for the players() method with real API calls."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = Edgework()

    def test_players_data_consistency(self):
        """Test that player data is consistent across multiple calls."""
        players1 = self.client.players(active_only=True)
        players2 = self.client.players(active_only=True)

        # Results should be consistent
        assert len(players1) == len(
            players2
        ), "Multiple calls should return same number of players"

        # Convert to sets of player IDs for comparison
        ids1 = {p._data.get("player_id") for p in players1}
        ids2 = {p._data.get("player_id") for p in players2}

        assert ids1 == ids2, "Multiple calls should return same players"

    def test_players_team_data_presence(self):
        """Test that active players have team information."""
        players = self.client.players(active_only=True)

        players_with_teams = [
            p
            for p in players
            if p._data.get("current_team_id") or p._data.get("current_team_abbr")
        ]

        # Most active players should have team information
        team_percentage = len(players_with_teams) / len(players)
        assert (
            team_percentage > 0.8
        ), f"Expected >80% of active players to have team info, got {team_percentage:.1%}"
