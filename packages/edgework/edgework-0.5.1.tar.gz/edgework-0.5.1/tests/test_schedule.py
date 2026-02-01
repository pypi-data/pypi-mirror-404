"""Tests for schedule-related functionality in the Edgework client."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from edgework.clients.schedule_client import ScheduleClient
from edgework.models.game import Game
from edgework.models.schedule import Schedule, schedule_api_to_dict


class TestScheduleApiToDict:
    """Test class for schedule_api_to_dict function."""

    def test_schedule_api_to_dict_basic(self):
        """Test schedule_api_to_dict with basic API data."""
        api_data = {
            "previousStartDate": "2024-06-01T00:00:00Z",
            "games": [{"id": 1}, {"id": 2}],
            "preSeasonStartDate": "2024-09-15T00:00:00Z",
            "regularSeasonStartDate": "2024-10-01T00:00:00Z",
            "regularSeasonEndDate": "2025-04-15T00:00:00Z",
            "playoffEndDate": "2025-06-30T00:00:00Z",
            "numberOfGames": 2,
        }

        result = schedule_api_to_dict(api_data)

        assert result["previous_start_date"] == "2024-06-01T00:00:00Z"
        assert result["games"] == [{"id": 1}, {"id": 2}]
        assert result["pre_season_start_date"] == "2024-09-15T00:00:00Z"
        assert result["regular_season_start_date"] == "2024-10-01T00:00:00Z"
        assert result["regular_season_end_date"] == "2025-04-15T00:00:00Z"
        assert result["playoff_end_date"] == "2025-06-30T00:00:00Z"
        assert result["number_of_games"] == 2

    def test_schedule_api_to_dict_with_game_week(self):
        """Test schedule_api_to_dict with gameWeek structure."""
        api_data = {
            "gameWeek": [{"games": [{"id": 1}, {"id": 2}]}, {"games": [{"id": 3}]}]
        }

        result = schedule_api_to_dict(api_data)

        assert result["games"] == [{"id": 1}, {"id": 2}, {"id": 3}]
        assert result["number_of_games"] == 3

    def test_schedule_api_to_dict_empty_data(self):
        """Test schedule_api_to_dict with empty data."""
        api_data = {}

        result = schedule_api_to_dict(api_data)

        assert result["games"] == []
        assert result["number_of_games"] == 0
        assert result["previous_start_date"] is None


class TestSchedule:
    """Test class for Schedule model."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_client = Mock()
        self.mock_http_client = Mock()
        self.mock_client.http_client = self.mock_http_client

    def test_schedule_init_basic(self):
        """Test Schedule initialization with basic data."""
        schedule = Schedule(self.mock_client, obj_id=123, games=[], number_of_games=0)

        assert schedule._client == self.mock_client
        assert schedule.obj_id == 123
        assert schedule._data["games"] == []
        assert schedule._data["number_of_games"] == 0
        assert schedule._fetched is True
        assert schedule._games_objects == []

    def test_schedule_init_without_games(self):
        """Test Schedule initialization without games data."""
        schedule = Schedule(self.mock_client)

        assert schedule._data["games"] == []
        # _fetched is False when no kwargs are provided
        assert schedule._fetched is False

    def test_schedule_str_with_dates(self):
        """Test Schedule string representation with dates."""
        schedule = Schedule(
            self.mock_client,
            number_of_games=82,
            regular_season_start_date="2024-10-01T00:00:00Z",
            regular_season_end_date="2025-04-15T00:00:00Z",
        )

        result = str(schedule)
        assert "Schedule (82 games): 2024-10-01 to 2025-04-15" == result

    def test_schedule_str_with_datetime_objects(self):
        """Test Schedule string representation with datetime objects."""
        start_date = datetime(2024, 10, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 4, 15, tzinfo=timezone.utc)

        schedule = Schedule(
            self.mock_client,
            number_of_games=82,
            regular_season_start_date=start_date,
            regular_season_end_date=end_date,
        )

        result = str(schedule)
        assert "Schedule (82 games): 2024-10-01 to 2025-04-15" == result

    def test_schedule_str_without_dates(self):
        """Test Schedule string representation without dates."""
        schedule = Schedule(self.mock_client, number_of_games=5)

        result = str(schedule)
        assert result == "Schedule (5 games)"

    def test_schedule_str_empty(self):
        """Test Schedule string representation with no data."""
        schedule = Schedule(self.mock_client)

        result = str(schedule)
        assert result == "Schedule"

    def test_schedule_repr(self):
        """Test Schedule repr representation."""
        schedule = Schedule(self.mock_client, games=[{"id": 1}, {"id": 2}])

        result = repr(schedule)
        assert result == "Schedule(games=2)"

    def test_from_dict_with_date_strings(self):
        """Test Schedule.from_dict with date strings."""
        data = {
            "regular_season_start_date": "2024-10-01T00:00:00Z",
            "regular_season_end_date": "2025-04-15T00:00:00Z",
            "games": [{"id": 1}],
            "number_of_games": 1,
        }

        schedule = Schedule.from_dict(self.mock_client, data)

        assert isinstance(schedule._data["regular_season_start_date"], datetime)
        assert isinstance(schedule._data["regular_season_end_date"], datetime)
        assert schedule._data["games"] == [{"id": 1}]
        assert schedule._data["number_of_games"] == 1

    def test_from_dict_with_datetime_objects(self):
        """Test Schedule.from_dict with datetime objects."""
        start_date = datetime(2024, 10, 1, tzinfo=timezone.utc)
        data = {
            "regular_season_start_date": start_date,
            "games": [],
            "number_of_games": 0,
        }

        schedule = Schedule.from_dict(self.mock_client, data)

        assert schedule._data["regular_season_start_date"] == start_date

    def test_from_dict_with_invalid_dates(self):
        """Test Schedule.from_dict with invalid date strings."""
        data = {
            "regular_season_start_date": "invalid-date",
            "games": [],
            "number_of_games": 0,
        }

        schedule = Schedule.from_dict(self.mock_client, data)

        assert schedule._data["regular_season_start_date"] == "invalid-date"

    def test_from_api(self):
        """Test Schedule.from_api method."""
        api_data = {
            "games": [{"id": 1}],
            "regularSeasonStartDate": "2024-10-01T00:00:00Z",
            "numberOfGames": 1,
        }

        schedule = Schedule.from_api(self.mock_client, api_data)

        assert len(schedule._data["games"]) == 1
        assert schedule._data["number_of_games"] == 1
        assert isinstance(schedule._data["regular_season_start_date"], datetime)

    def test_fetch_data_without_client(self):
        """Test fetch_data raises error without client."""
        schedule = Schedule(None)

        with pytest.raises(
            ValueError, match="No client available to fetch schedule data"
        ):
            schedule.fetch_data()

    def test_fetch_data_with_client(self):
        """Test fetch_data with client."""
        schedule = Schedule(self.mock_client)

        # Should raise NotImplementedError since fetch_data is not implemented
        with pytest.raises(NotImplementedError):
            schedule.fetch_data()

    @patch("edgework.models.game.Game")
    def test_games_property_with_client(self, mock_game_class):
        """Test games property with client creates Game objects."""
        mock_game = Mock()
        mock_game_class.from_api.return_value = mock_game

        game_data = {"id": 1, "gameState": "FINAL"}
        schedule = Schedule(self.mock_client, games=[game_data])

        games = schedule.games

        assert len(games) == 1
        assert games[0] == mock_game
        mock_game_class.from_api.assert_called_once_with(game_data, self.mock_client)

    def test_games_property_without_client(self):
        """Test games property without client returns empty list."""
        schedule = Schedule(None, games=[{"id": 1}])

        games = schedule.games

        assert games == []

    def test_games_property_no_games_data(self):
        """Test games property with no games data."""
        schedule = Schedule(self.mock_client)

        games = schedule.games

        assert games == []

    def test_games_property_cached(self):
        """Test games property uses cached objects."""
        schedule = Schedule(self.mock_client)
        mock_game = Mock()
        schedule._games_objects = [mock_game]

        games = schedule.games

        assert games == [mock_game]

    @patch("edgework.models.schedule.datetime")
    def test_games_today(self, mock_datetime):
        """Test games_today property."""
        # Mock current date
        mock_date = datetime(2024, 6, 1).date()
        mock_datetime.now.return_value.date.return_value = mock_date

        # Create mock games
        game_today = Mock()
        game_today._data = {"game_date": datetime(2024, 6, 1).date()}

        game_tomorrow = Mock()
        game_tomorrow._data = {"game_date": datetime(2024, 6, 2).date()}

        schedule = Schedule(self.mock_client)
        schedule._games_objects = [game_today, game_tomorrow]

        games_today = schedule.games_today

        assert len(games_today) == 1
        assert games_today[0] == game_today

    @patch("edgework.models.schedule.datetime")
    def test_upcoming_games(self, mock_datetime):
        """Test upcoming_games property."""
        # Mock current time
        mock_now = datetime(2024, 6, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        # Create mock games
        past_game = Mock()
        past_game._data = {"start_time_utc": datetime(2024, 5, 31, 12, 0, 0)}

        future_game = Mock()
        future_game._data = {"start_time_utc": datetime(2024, 6, 2, 12, 0, 0)}

        schedule = Schedule(self.mock_client)
        schedule._games_objects = [past_game, future_game]

        upcoming_games = schedule.upcoming_games

        assert len(upcoming_games) == 1
        assert upcoming_games[0] == future_game

    def test_upcoming_games_missing_start_time(self):
        """Test upcoming_games property with missing start_time_utc."""
        # Create mock game without start_time_utc
        game_no_time = Mock()
        game_no_time._data = {}

        schedule = Schedule(self.mock_client)
        schedule._games_objects = [game_no_time]

        # Should not crash and return empty list (uses now as default)
        upcoming_games = schedule.upcoming_games

        assert len(upcoming_games) == 0

    def test_completed_games(self):
        """Test completed_games property."""
        # Create mock games with different states
        final_game = Mock()
        final_game._data = {"game_state": "FINAL"}

        off_game = Mock()
        off_game._data = {"game_state": "OFF"}

        live_game = Mock()
        live_game._data = {"game_state": "LIVE"}

        pre_game = Mock()
        pre_game._data = {"game_state": "PRE"}

        no_state_game = Mock()
        no_state_game._data = {}

        schedule = Schedule(self.mock_client)
        schedule._games_objects = [
            final_game,
            off_game,
            live_game,
            pre_game,
            no_state_game,
        ]

        completed_games = schedule.completed_games

        assert len(completed_games) == 2
        assert final_game in completed_games
        assert off_game in completed_games
        assert live_game not in completed_games
        assert pre_game not in completed_games
        assert no_state_game not in completed_games

    def test_completed_games_empty(self):
        """Test completed_games property with no completed games."""
        live_game = Mock()
        live_game._data = {"game_state": "LIVE"}

        schedule = Schedule(self.mock_client)
        schedule._games_objects = [live_game]

        completed_games = schedule.completed_games

        assert len(completed_games) == 0


class TestScheduleClient:
    """Unit tests for ScheduleClient methods."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_http_client = Mock()
        self.schedule_client = ScheduleClient(self.mock_http_client)

    def test_get_schedule_for_date_range_uses_pagination(self):
        """Test that get_schedule_for_date_range uses pagination (nextStartDate)."""
        # Mock first response with nextStartDate
        first_response = Mock()
        first_response.json.return_value = {
            "gameWeek": [
                {
                    "games": [
                        {"id": 1, "gameDate": "2024-01-01T00:00:00Z"},
                        {"id": 2, "gameDate": "2024-01-01T19:00:00Z"},
                    ]
                }
            ],
            "nextStartDate": "2024-01-08T00:00:00Z",
            "previousStartDate": "2023-12-31T00:00:00Z",
            "preSeasonStartDate": "2023-09-15T00:00:00Z",
        }

        # Mock second response (no nextStartDate)
        second_response = Mock()
        second_response.json.return_value = {
            "gameWeek": [
                {
                    "games": [
                        {"id": 3, "gameDate": "2024-01-08T00:00:00Z"},
                    ]
                }
            ],
            "nextStartDate": None,
            "regularSeasonStartDate": "2023-10-01T00:00:00Z",
        }

        # Set up mock to return different responses
        self.mock_http_client.get.side_effect = [first_response, second_response]

        result = self.schedule_client.get_schedule_for_date_range(
            "2024-01-01", "2024-01-15"
        )

        # Verify it made 2 API calls (pagination)
        assert self.mock_http_client.get.call_count == 2

        # Verify first call used start_date
        first_call = self.mock_http_client.get.call_args_list[0]
        assert "schedule/2024-01-01" in first_call[0][0]

        # Verify second call used nextStartDate
        second_call = self.mock_http_client.get.call_args_list[1]
        assert "schedule/2024-01-08" in second_call[0][0]

        # Verify no duplicates
        game_ids = [game.get("id") for game in result._data["games"]]
        assert len(game_ids) == len(set(game_ids))

    def test_get_schedule_for_date_range_filters_by_date(self):
        """Test that get_schedule_for_date_range filters games to requested date range."""
        # Mock response with games that span beyond the requested range
        response = Mock()
        response.json.return_value = {
            "gameWeek": [
                {
                    "games": [
                        {
                            "id": 1,
                            "startTimeUTC": "2024-01-01T00:00:00Z",
                        },  # Inside range
                        {
                            "id": 2,
                            "startTimeUTC": "2024-01-15T00:00:00Z",
                        },  # Inside range
                        {
                            "id": 3,
                            "startTimeUTC": "2023-12-31T00:00:00Z",
                        },  # Before range
                        {
                            "id": 4,
                            "startTimeUTC": "2024-01-16T00:00:00Z",
                        },  # After range
                    ]
                }
            ],
            "nextStartDate": None,
        }

        self.mock_http_client.get.return_value = response

        result = self.schedule_client.get_schedule_for_date_range(
            "2024-01-01", "2024-01-15"
        )

        # Verify only games within range are included
        games = result._data["games"]
        game_ids = [game.get("id") for game in games]
        assert 1 in game_ids
        assert 2 in game_ids
        assert 3 not in game_ids  # Before range
        assert 4 not in game_ids  # After range

    def test_get_schedule_for_date_range_invalid_date_format(self):
        """Test that get_schedule_for_date_range raises ValueError for invalid date format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            self.schedule_client.get_schedule_for_date_range("2024/01/01", "2024-01-15")

        with pytest.raises(ValueError, match="Invalid date format"):
            self.schedule_client.get_schedule_for_date_range("2024-01-01", "01/15/2024")

    def test_get_schedule_for_date_range_invalid_date_range(self):
        """Test that get_schedule_for_date_range raises ValueError when start_date > end_date."""
        with pytest.raises(ValueError, match="Start date cannot be after end date"):
            self.schedule_client.get_schedule_for_date_range("2024-01-15", "2024-01-01")


class TestScheduleIntegration:
    """Integration tests for Schedule with real Edgework client (if available)."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        try:
            from edgework.edgework import Edgework

            self.client = Edgework()
            self.has_client = True
        except Exception:
            self.has_client = False

    def test_schedule_creation_from_client(self):
        """Test creating Schedule objects through the client."""
        if not self.has_client:
            pytest.skip("Edgework client not available")

        # This would test actual client integration
        # schedule = self.client.get_schedule()
        # assert isinstance(schedule, Schedule)

    def test_get_schedule_for_date_range_live_api(self):
        """Test get_schedule_for_date_range with live API."""
        if not self.has_client:
            pytest.skip("Edgework client not available")

        # Use a small date range to avoid too many API calls
        schedule = self.client.get_schedule_for_date_range("2024-01-01", "2024-01-07")

        assert schedule is not None
        assert len(schedule._data["games"]) >= 0

        # Check for duplicates
        game_ids = [game.get("id") for game in schedule._data["games"]]
        assert len(game_ids) == len(set(game_ids)), "Duplicate games found!"

    def test_get_schedule_for_single_date(self):
        """Test getting schedule for a single date."""
        if not self.has_client:
            pytest.skip("Edgework client not available")

        schedule = self.client.get_schedule_for_date("2024-01-01")

        assert schedule is not None
        assert isinstance(schedule, Schedule)
