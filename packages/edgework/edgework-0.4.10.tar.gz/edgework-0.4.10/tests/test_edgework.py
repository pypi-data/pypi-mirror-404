"""
Pytest tests for the main Edgework client class.
This file tests all methods and functionality of the Edgework class.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from edgework.edgework import Edgework
from edgework.models.player import Player
from edgework.models.stats import GoalieStats, SkaterStats, TeamStats


class TestEdgeworkInitialization:
    """Test class for Edgework initialization."""

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_init_default_user_agent(self, mock_player_client, mock_http_client):
        """Test Edgework initialization with default user agent."""
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance

        edgework = Edgework()

        # Verify HTTP client was created with default user agent
        mock_http_client.assert_called_once_with(user_agent="EdgeworkClient/2.0")

        # Verify stats models were initialized
        assert isinstance(edgework.skaters, SkaterStats)
        assert isinstance(edgework.goalies, GoalieStats)
        assert isinstance(edgework.teams, TeamStats)

        # Verify player client was initialized
        mock_player_client.assert_called_once_with(http_client=mock_client_instance)

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_init_custom_user_agent(self, mock_player_client, mock_http_client):
        """Test Edgework initialization with custom user agent."""
        custom_user_agent = "MyCustomAgent/2.0"
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance

        edgework = Edgework(user_agent=custom_user_agent)

        # Verify HTTP client was created with custom user agent
        mock_http_client.assert_called_once_with(user_agent=custom_user_agent)

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_init_creates_stats_models_with_client(
        self, mock_player_client, mock_http_client
    ):
        """Test that stats models are initialized with the HTTP client."""
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance

        edgework = Edgework()

        # Verify all stats models have the HTTP client
        assert edgework.skaters._client == mock_client_instance
        assert edgework.goalies._client == mock_client_instance
        assert edgework.teams._client == mock_client_instance


class TestEdgeworkPlayers:
    """Test class for Edgework players method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        with (
            patch("edgework.edgework.HttpClient"),
            patch("edgework.edgework.PlayerClient") as mock_player_client,
        ):
            self.mock_player_client_instance = Mock()
            mock_player_client.return_value = self.mock_player_client_instance
            self.edgework = Edgework()

    def test_players_active_only_default(self):
        """Test players method with default active_only=True."""
        mock_players = [Mock(spec=Player), Mock(spec=Player)]
        self.mock_player_client_instance.get_active_players.return_value = mock_players

        result = self.edgework.players()

        self.mock_player_client_instance.get_active_players.assert_called_once()
        self.mock_player_client_instance.get_all_players.assert_not_called()
        assert result == mock_players

    def test_players_active_only_explicit_true(self):
        """Test players method with explicit active_only=True."""
        mock_players = [Mock(spec=Player), Mock(spec=Player)]
        self.mock_player_client_instance.get_active_players.return_value = mock_players

        result = self.edgework.players(active_only=True)

        self.mock_player_client_instance.get_active_players.assert_called_once()
        self.mock_player_client_instance.get_all_players.assert_not_called()
        assert result == mock_players

    def test_players_active_only_false(self):
        """Test players method with active_only=False."""
        mock_players = [Mock(spec=Player), Mock(spec=Player), Mock(spec=Player)]
        self.mock_player_client_instance.get_all_players.return_value = mock_players

        result = self.edgework.players(active_only=False)

        self.mock_player_client_instance.get_all_players.assert_called_once()
        self.mock_player_client_instance.get_active_players.assert_not_called()
        assert result == mock_players

    def test_players_return_type(self):
        """Test that players method returns a list."""
        mock_players = []
        self.mock_player_client_instance.get_active_players.return_value = mock_players

        result = self.edgework.players()

        assert isinstance(result, list)


class TestEdgeworkSkaterStats:
    """Test class for Edgework skater_stats method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        with (
            patch("edgework.edgework.HttpClient"),
            patch("edgework.edgework.PlayerClient"),
        ):
            self.edgework = Edgework()
            self.edgework.skaters = Mock(spec=SkaterStats)

    def test_skater_stats_valid_season_format(self):
        """Test skater_stats with valid season format."""
        result = self.edgework.skater_stats("2023-2024")

        self.edgework.skaters.fetch_data.assert_called_once_with(
            report="summary",
            season=20232024,
            sort="points",
            direction="DESC",
            limit=10,
            aggregate=False,
            game_type=2,
        )
        assert result == self.edgework.skaters

    def test_skater_stats_custom_parameters(self):
        """Test skater_stats with custom parameters."""
        result = self.edgework.skater_stats(
            season="2022-2023",
            report="advanced",
            sort=["goals", "assists"],
            direction=["DESC", "ASC"],
            aggregate=True,
            limit=50,
            game_type=3,
        )

        self.edgework.skaters.fetch_data.assert_called_once_with(
            report="advanced",
            season=20222023,
            sort=["goals", "assists"],
            direction=["DESC", "ASC"],
            limit=50,
            aggregate=True,
            game_type=3,
        )
        assert result == self.edgework.skaters

    def test_skater_stats_invalid_season_format(self):
        """Test skater_stats with invalid season format."""
        with pytest.raises(
            ValueError, match="Invalid season format. Expected 'YYYY-YYYY'"
        ):
            self.edgework.skater_stats("2023")

    def test_skater_stats_invalid_season_non_numeric(self):
        """Test skater_stats with non-numeric season."""
        with pytest.raises(
            ValueError, match="Invalid season format. Expected 'YYYY-YYYY'"
        ):
            self.edgework.skater_stats("abc-def")

    def test_skater_stats_invalid_season_wrong_format(self):
        """Test skater_stats with wrong season format."""
        with pytest.raises(
            ValueError, match="Invalid season format. Expected 'YYYY-YYYY'"
        ):
            self.edgework.skater_stats("2023/2024")

    def test_skater_stats_default_parameters(self):
        """Test skater_stats with only required parameter."""
        result = self.edgework.skater_stats("2023-2024")

        # Verify default parameters were used
        call_args = self.edgework.skaters.fetch_data.call_args
        assert call_args.kwargs["report"] == "summary"
        assert call_args.kwargs["sort"] == "points"
        assert call_args.kwargs["direction"] == "DESC"
        assert call_args.kwargs["aggregate"] == False
        assert call_args.kwargs["limit"] == 10
        assert call_args.kwargs["game_type"] == 2


class TestEdgeworkGoalieStats:
    """Test class for Edgework goalie_stats method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        with (
            patch("edgework.edgework.HttpClient"),
            patch("edgework.edgework.PlayerClient"),
        ):
            self.edgework = Edgework()
            self.edgework.goalies = Mock(spec=GoalieStats)

    def test_goalie_stats_valid_season_format(self):
        """Test goalie_stats with valid season format."""
        result = self.edgework.goalie_stats("2023-2024")

        self.edgework.goalies.fetch_data.assert_called_once_with(
            report="summary", season=20232024, sort="wins", limit=10
        )
        assert result == self.edgework.goalies

    def test_goalie_stats_custom_parameters(self):
        """Test goalie_stats with custom parameters."""
        result = self.edgework.goalie_stats(
            season="2022-2023",
            report="advanced",
            sort=["saves", "wins"],
            direction=["DESC", "DESC"],
            is_aggregate=True,
            limit=25,
        )

        self.edgework.goalies.fetch_data.assert_called_once_with(
            report="advanced", season=20222023, sort=["saves", "wins"], limit=25
        )
        assert result == self.edgework.goalies

    def test_goalie_stats_invalid_season_format(self):
        """Test goalie_stats with invalid season format."""
        with pytest.raises(
            ValueError, match="Invalid season format. Expected 'YYYY-YYYY'"
        ):
            self.edgework.goalie_stats("invalid")

    def test_goalie_stats_default_parameters(self):
        """Test goalie_stats with only required parameter."""
        result = self.edgework.goalie_stats("2023-2024")

        # Verify default parameters were used
        call_args = self.edgework.goalies.fetch_data.call_args
        assert call_args.kwargs["report"] == "summary"
        assert call_args.kwargs["sort"] == "wins"
        assert call_args.kwargs["limit"] == 10


class TestEdgeworkTeamStats:
    """Test class for Edgework team_stats method."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        with (
            patch("edgework.edgework.HttpClient"),
            patch("edgework.edgework.PlayerClient"),
        ):
            self.edgework = Edgework()
            self.edgework.teams = Mock(spec=TeamStats)

    def test_team_stats_valid_season_format(self):
        """Test team_stats with valid season format."""
        result = self.edgework.team_stats("2023-2024")

        self.edgework.teams.fetch_data.assert_called_once_with(
            report="summary",
            season=20232024,
            sort="points",
            direction="DESC",
            limit=10,
            aggregate=False,
            game=True,
        )
        assert result == self.edgework.teams

    def test_team_stats_custom_parameters(self):
        """Test team_stats with custom parameters."""
        result = self.edgework.team_stats(
            season="2022-2023",
            report="advanced",
            sort=["wins", "points"],
            direction=["DESC", "ASC"],
            limit=32,
            aggregate=True,
            game=False,
        )

        self.edgework.teams.fetch_data.assert_called_once_with(
            report="advanced",
            season=20222023,
            sort=["wins", "points"],
            direction=["DESC", "ASC"],
            limit=32,
            aggregate=True,
            game=False,
        )
        assert result == self.edgework.teams

    def test_team_stats_invalid_season_format(self):
        """Test team_stats with invalid season format."""
        with pytest.raises(
            ValueError, match="Invalid season format. Expected 'YYYY-YYYY'"
        ):
            self.edgework.team_stats("2023")

    def test_team_stats_default_parameters(self):
        """Test team_stats with only required parameter."""
        result = self.edgework.team_stats("2023-2024")

        # Verify default parameters were used
        call_args = self.edgework.teams.fetch_data.call_args
        assert call_args.kwargs["report"] == "summary"
        assert call_args.kwargs["sort"] == "points"
        assert call_args.kwargs["direction"] == "DESC"
        assert call_args.kwargs["limit"] == 10
        assert call_args.kwargs["aggregate"] == False
        assert call_args.kwargs["game"] == True


class TestEdgeworkContextManager:
    """Test class for Edgework context manager functionality."""

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_context_manager_enter(self, mock_player_client, mock_http_client):
        """Test Edgework as context manager __enter__ method."""
        with Edgework() as edgework:
            assert isinstance(edgework, Edgework)

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_context_manager_exit_with_close_method(
        self, mock_player_client, mock_http_client
    ):
        """Test Edgework context manager __exit__ calls close if available."""
        mock_client_instance = Mock()
        mock_client_instance.close = Mock()
        mock_http_client.return_value = mock_client_instance

        with Edgework() as edgework:
            pass  # Exit the context

        mock_client_instance.close.assert_called_once()

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_context_manager_exit_without_close_method(
        self, mock_player_client, mock_http_client
    ):
        """Test Edgework context manager __exit__ handles client without close method."""
        mock_client_instance = Mock()
        # Don't add close method to simulate client without close
        del mock_client_instance.close
        mock_http_client.return_value = mock_client_instance

        # Should not raise an exception
        with Edgework() as edgework:
            assert isinstance(edgework, Edgework)

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_close_method_directly(self, mock_player_client, mock_http_client):
        """Test calling close method directly."""
        mock_client_instance = Mock()
        mock_client_instance.close = Mock()
        mock_http_client.return_value = mock_client_instance

        edgework = Edgework()
        edgework.close()

        mock_client_instance.close.assert_called_once()

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_close_method_no_close_attribute(
        self, mock_player_client, mock_http_client
    ):
        """Test close method when client doesn't have close attribute."""
        mock_client_instance = Mock()
        # Simulate client without close method
        del mock_client_instance.close
        mock_http_client.return_value = mock_client_instance

        edgework = Edgework()
        # Should not raise an exception
        edgework.close()


class TestEdgeworkSeasonConversion:
    """Test class for season string conversion functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        with (
            patch("edgework.edgework.HttpClient"),
            patch("edgework.edgework.PlayerClient"),
        ):
            self.edgework = Edgework()
            self.edgework.skaters = Mock(spec=SkaterStats)
            self.edgework.goalies = Mock(spec=GoalieStats)
            self.edgework.teams = Mock(spec=TeamStats)

    @pytest.mark.parametrize(
        "season_str,expected_int",
        [
            ("2023-2024", 20232024),
            ("2022-2023", 20222023),
            ("2021-2022", 20212022),
            ("2020-2021", 20202021),
            ("1999-2000", 19992000),
        ],
    )
    def test_season_conversion_valid_formats(self, season_str, expected_int):
        """Test season string conversion for various valid formats."""
        self.edgework.skater_stats(season_str)

        call_args = self.edgework.skaters.fetch_data.call_args
        assert call_args.kwargs["season"] == expected_int

    @pytest.mark.parametrize(
        "invalid_season",
        [
            "2023",
            "23-24",
            "2023-24",
            "2023/2024",
            "2023_2024",
            "2023 2024",
            "abc-def",
            "2023-abcd",
            "",
            "2023-",
            "-2024",
        ],
    )
    def test_season_conversion_invalid_formats(self, invalid_season):
        """Test season string conversion for various invalid formats."""
        with pytest.raises(
            ValueError, match="Invalid season format. Expected 'YYYY-YYYY'"
        ):
            self.edgework.skater_stats(invalid_season)


class TestEdgeworkIntegration:
    """Integration tests for Edgework class functionality."""

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_multiple_method_calls_same_instance(
        self, mock_player_client, mock_http_client
    ):
        """Test that multiple method calls work on the same instance."""
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance
        mock_player_client_instance = Mock()
        mock_player_client.return_value = mock_player_client_instance

        edgework = Edgework()

        # Mock the stats objects
        edgework.skaters = Mock(spec=SkaterStats)
        edgework.goalies = Mock(spec=GoalieStats)
        edgework.teams = Mock(spec=TeamStats)

        # Test players method
        mock_players = [Mock(spec=Player)]
        mock_player_client_instance.get_active_players.return_value = mock_players
        players_result = edgework.players()

        # Test skater_stats method
        skater_result = edgework.skater_stats("2023-2024")

        # Test goalie_stats method
        goalie_result = edgework.goalie_stats("2023-2024")

        # Test team_stats method
        team_result = edgework.team_stats("2023-2024")

        # Verify all methods work and return expected objects
        assert players_result == mock_players
        assert skater_result == edgework.skaters
        assert goalie_result == edgework.goalies
        assert team_result == edgework.teams

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_client_shared_across_stats_models(
        self, mock_player_client, mock_http_client
    ):
        """Test that the HTTP client is shared across all stats models."""
        mock_client_instance = Mock()
        mock_http_client.return_value = mock_client_instance

        edgework = Edgework()

        # All stats models should share the same HTTP client
        assert edgework.skaters._client == mock_client_instance
        assert edgework.goalies._client == mock_client_instance
        assert edgework.teams._client == mock_client_instance
        assert edgework._client == mock_client_instance

    def test_stats_models_are_different_instances(self):
        """Test that stats models are different instances."""
        with (
            patch("edgework.edgework.HttpClient"),
            patch("edgework.edgework.PlayerClient"),
        ):
            edgework = Edgework()

            assert edgework.skaters is not edgework.goalies
            assert edgework.goalies is not edgework.teams
            assert edgework.teams is not edgework.skaters

    @patch("edgework.edgework.HttpClient")
    @patch("edgework.edgework.PlayerClient")
    def test_error_handling_preserves_instance_state(
        self, mock_player_client, mock_http_client
    ):
        """Test that errors in one method don't affect instance state."""
        edgework = Edgework()
        edgework.skaters = Mock(spec=SkaterStats)

        # Test that an error in skater_stats doesn't break the instance
        with pytest.raises(ValueError):
            edgework.skater_stats("invalid-season")

        # Instance should still be functional
        edgework.skater_stats("2023-2024")
        edgework.skaters.fetch_data.assert_called_once()


class TestEdgeworkTypeHints:
    """Test class for type hints and return types."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        with (
            patch("edgework.edgework.HttpClient"),
            patch("edgework.edgework.PlayerClient"),
        ):
            self.edgework = Edgework()
            self.edgework.skaters = Mock(spec=SkaterStats)
            self.edgework.goalies = Mock(spec=GoalieStats)
            self.edgework.teams = Mock(spec=TeamStats)

    def test_skater_stats_return_type(self):
        """Test that skater_stats returns SkaterStats instance."""
        result = self.edgework.skater_stats("2023-2024")
        assert isinstance(result, type(self.edgework.skaters))

    def test_goalie_stats_return_type(self):
        """Test that goalie_stats returns GoalieStats instance."""
        result = self.edgework.goalie_stats("2023-2024")
        assert isinstance(result, type(self.edgework.goalies))

    def test_team_stats_return_type(self):
        """Test that team_stats returns TeamStats instance."""
        result = self.edgework.team_stats("2023-2024")
        assert isinstance(result, type(self.edgework.teams))

    def test_context_manager_return_type(self):
        """Test that context manager returns Edgework instance."""
        with (
            patch("edgework.edgework.HttpClient"),
            patch("edgework.edgework.PlayerClient"),
        ):
            with Edgework() as edgework:
                assert isinstance(edgework, Edgework)
