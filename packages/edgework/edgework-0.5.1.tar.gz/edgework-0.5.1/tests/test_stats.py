from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from edgework.http_client import HttpClient
from edgework.models.stats import GoalieStats, SkaterStats, TeamStats


@pytest.fixture
def mock_client():
    client = Mock(spec=HttpClient)
    return client


@pytest.fixture
def real_client():
    return HttpClient()


@pytest.fixture
def mock_skater_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "data": [
            {
                "playerId": 8478402,
                "firstName": "Connor",
                "lastName": "McDavid",
                "points": 100,
                "goals": 40,
                "assists": 60,
                "gamesPlayed": 82,
                "timeOnIce": "1200:00",
            }
        ]
    }
    return response


@pytest.fixture
def mock_goalie_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "data": [
            {
                "playerId": 8478402,
                "firstName": "Connor",
                "lastName": "Hellebuyck",
                "wins": 30,
                "losses": 20,
                "otLosses": 5,
                "goalsAgainst": 150,
                "shotsAgainst": 2000,
                "saves": 1850,
                "savePercentage": 0.925,
                "goalsAgainstAverage": 2.50,
            }
        ]
    }
    return response


@pytest.fixture
def mock_team_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "data": [
            {
                "teamId": 10,
                "teamName": "Toronto Maple Leafs",
                "wins": 45,
                "losses": 25,
                "otLosses": 12,
                "points": 102,
                "goalsFor": 280,
                "goalsAgainst": 240,
                "powerPlayPercentage": 25.5,
                "penaltyKillPercentage": 82.5,
            }
        ]
    }
    return response


class TestSkaterStats:

    @pytest.fixture(autouse=True)
    def test_init(self, mock_client: Mock):
        # Test with obj_id and no kwargs
        stats1 = SkaterStats(mock_client, obj_id=8478402)
        # skipcq: BAN-B101
        assert stats1._client == mock_client
        assert stats1.obj_id == 8478402
        assert stats1._data == {}

        # Test with kwargs
        extra_data = {"key": "value", "another_key": 123}
        stats2 = SkaterStats(mock_client, obj_id=123, **extra_data)
        assert stats2._client == mock_client
        assert stats2.obj_id == 123
        assert stats2._data == extra_data
        assert stats2._data["key"] == "value"
        assert stats2._data["another_key"] == 123

    @pytest.fixture(autouse=True)
    def test_fetch_data(self, mock_client: Mock, mock_skater_response: Mock):
        mock_client.get.return_value = mock_skater_response

        stats = SkaterStats(mock_client, obj_id=8478402)
        stats.fetch_data(report="summary", season=20232024)

        # Verify the API call
        mock_client.get.assert_called_once_with(
            endpoint="stats",
            path="skater/summary?isAggregate=False&isGame=True&limit=-1&start=0&sort=points&cayenneExp=seasonId=20232024",
            params=None,
            web=False,
        )

        player = stats.players[0]
        assert player.player_id == 8478402
        assert player.first_name == "Connor"
        assert player.last_name == "McDavid"
        assert player.points == 100
        assert player.goals == 40
        assert player.assists == 60

    @pytest.fixture(autouse=True)
    def test_fetch_data_default_season(
        self, mock_client: Mock, mock_skater_response: Mock
    ):
        mock_client.get.return_value = mock_skater_response

        stats = SkaterStats(mock_client, obj_id=8478402)
        with patch("edgework.models.stats.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 1)
            stats.fetch_data()

            # Verify the API call used current season
            mock_client.get.assert_called_once_with(
                endpoint="stats",
                path="skater/summary?isAggregate=False&isGame=True&limit=-1&start=0&sort=points&cayenneExp=seasonId=20232024",
                params=None,
                web=False,
            )

    @pytest.fixture(autouse=True)
    def test_fetch_data_empty_response(self, mock_client: Mock):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_client.get.return_value = mock_response

        stats = SkaterStats(mock_client, obj_id=8478402)
        initial_data = {"existing": "data"}
        stats._data = initial_data.copy()  # Simulate some pre-existing data

        stats.fetch_data(report="summary", season=20232024)

        # Verify data wasn't updated since response was empty, or rather, it remains what it was
        assert stats._data == initial_data

    @pytest.fixture(autouse=True)
    def test_fetch_data_key_error_if_data_key_missing(self, mock_client: Mock):
        mock_response = Mock()
        mock_response.status_code = 200  # Status code is fine, but data key is missing
        mock_response.json.return_value = {"not_data": []}  # Missing "data" key
        mock_client.get.return_value = mock_response

        stats = SkaterStats(mock_client, obj_id=8478402)
        with pytest.raises(KeyError) as exc_info:
            stats.fetch_data(report="summary", season=20232024)
        assert "'data'" in str(exc_info.value)

    @pytest.fixture(autouse=True)
    def test_fetch_data_with_all_params(
        self, mock_client: Mock, mock_skater_response: Mock
    ):
        mock_client.get.return_value = mock_skater_response
        stats = SkaterStats(mock_client, obj_id=8478402)
        stats.fetch_data(
            report="bios",
            season=20222023,
            aggregate=True,
            game=False,
            limit=10,
            start=5,
            sort="goals",
        )
        mock_client.get.assert_called_once_with(
            endpoint="stats",
            path="skater/bios?isAggregate=True&isGame=False&limit=10&start=5&sort=goals&cayenneExp=seasonId=20222023",
            params=None,
            web=False,
        )

    @pytest.fixture(autouse=True)
    def test_fetch_data_live(self, real_client: HttpClient):
        stats = SkaterStats(real_client, obj_id=8478402)  # Connor McDavid
        stats.fetch_data(season=20232024)  # Use a recent season

        # Check that some data is populated. We can't assert specific values
        # as they might change, but we can check for presence and type.
        assert stats._data, "Data should be populated by the live API call"
        assert stats.players, "Players should be populated by the live API call"
        assert (
            len(stats.players) > 0
        ), "Players should be populated by the live API call"
        for player in stats.players:
            assert player.player_id, "Player should have a player_id"
            assert player.skater_full_name, "Player should have a full_name"
            assert player.points is not None, "Player should have points"
            assert player.goals is not None, "Player should have goals"
            assert player.assists is not None, "Player should have assists"


class TestGoalieStats:

    @pytest.fixture(autouse=True)
    def test_init(self, mock_client: Mock):
        stats1 = GoalieStats(mock_client, obj_id=8478402)
        assert stats1._client == mock_client
        assert stats1.obj_id == 8478402
        assert stats1._data == {}

        stats2 = GoalieStats(mock_client, obj_id=123, custom_field="test")
        assert stats2._data == {"custom_field": "test"}

    def test_fetch_data(self, mock_client: Mock, mock_goalie_response: Mock):
        mock_client.get.return_value = mock_goalie_response

        stats = GoalieStats(mock_client, obj_id=8478402)
        stats.fetch_data(report="summary", season=20232024)

        # Verify the API call
        mock_client.get.assert_called_once_with(
            endpoint="stats",
            path="goalie/summary?isAggregate=False&isGame=True&limit=-1&start=0&sort=wins&cayenneExp=seasonId=20232024",
            params=None,
            web=False,
        )

        player = stats.players[0]
        assert player.player_id == 8478402
        assert player.first_name == "Connor"
        assert player.last_name == "Hellebuyck"
        assert player.wins == 30
        assert player.losses == 20
        assert player.ot_losses == 5
        assert player.goals_against == 150
        assert player.shots_against == 2000
        assert player.saves == 1850
        assert player.save_percentage == 0.925
        assert player.goals_against_average == 2.50

    def test_fetch_data_default_season(
        self, mock_client: Mock, mock_goalie_response: Mock
    ):
        mock_client.get.return_value = mock_goalie_response

        stats = GoalieStats(mock_client, obj_id=8478402)
        with patch("edgework.models.stats.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2022, 8, 15)  # Year is 2022
            stats.fetch_data()  # Default sort is "wins"

            expected_season = 20222023  # Corrected: 2022 * 10000 + (2022 + 1)
            mock_client.get.assert_called_once_with(
                endpoint="stats",
                path=f"goalie/summary?isAggregate=False&isGame=True&limit=-1&start=0&sort=wins&cayenneExp=seasonId={expected_season}",
                params=None,
                web=False,
            )

    def test_fetch_data_empty_response(self, mock_client: Mock):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_client.get.return_value = mock_response

        stats = GoalieStats(mock_client, obj_id=8478402)
        stats.fetch_data(report="summary", season=20232024)
        assert stats._data == {}

    def test_fetch_data_key_error_if_data_key_missing(self, mock_client: Mock):
        mock_response = Mock()
        mock_response.status_code = 200  # Status code is fine, but data key is missing
        mock_response.json.return_value = {}  # Missing "data" key
        mock_client.get.return_value = mock_response

        stats = GoalieStats(mock_client, obj_id=8478402)
        with pytest.raises(KeyError):
            stats.fetch_data(report="summary", season=20232024)

    def test_fetch_data_live(self, real_client: HttpClient):
        stats = GoalieStats(real_client, obj_id=0)  # Connor Hellebuyck
        stats.fetch_data(season=20232024)  # Use a recent season

        players = stats.players
        assert players, "Players should be populated by the live API call"
        assert len(players) > 0, "Players should be populated by the live API call"
        for player in players:
            assert player.player_id, "Player should have a player_id"
            assert player.goalie_full_name, "Player should have a full_name"
            assert player.wins is not None, "Player should have wins"
            assert player.losses is not None, "Player should have losses"
            assert player.ot_losses is not None, "Player should have ot_losses"
            assert player.goals_against is not None, "Player should have goals_against"
            assert player.shots_against is not None, "Player should have shots_against"
            assert player.saves is not None, "Player should have saves"
            assert (
                player.goals_against_average is not None
            ), "Player should have goals_against_average"


class TestTeamStats:
    def test_init(self, mock_client: Mock):
        stats1 = TeamStats(mock_client, obj_id=10)
        assert stats1._client == mock_client
        assert stats1.obj_id == 10
        assert stats1._data == {}

        stats2 = TeamStats(mock_client, team_location="Toronto")
        assert stats2._client == mock_client
        assert stats2.obj_id is None  # No obj_id passed
        assert stats2._data == {"team_location": "Toronto"}

    def test_fetch_data(self, mock_client: Mock, mock_team_response: Mock):
        mock_client.get.return_value = mock_team_response

        stats = TeamStats(mock_client, obj_id=10)
        stats.fetch_data(report="summary", season=20232024)

        # Verify the API call
        mock_client.get.assert_called_once_with(
            endpoint="stats",
            path="team/summary?isAggregate=False&isGame=True&limit=-1&start=0&sort=wins&cayenneExp=seasonId=20232024",
            params=None,
            web=False,
        )

        teams = stats.teams
        assert len(teams) == 1
        team = teams[0]

        assert team.team_id == 10
        assert team.team_name == "Toronto Maple Leafs"
        assert team.wins == 45
        assert team.losses == 25
        assert team.ot_losses == 12
        assert team.points == 102
        assert team.goals_for == 280
        assert team.goals_against == 240
        assert team.power_play_percentage == 25.5
        assert team.penalty_kill_percentage == 82.5

    def test_fetch_data_default_season(
        self, mock_client: Mock, mock_team_response: Mock
    ):
        mock_client.get.return_value = mock_team_response

        stats = TeamStats(mock_client, obj_id=10)
        with patch("edgework.models.stats.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1)  # Year is 2024
            stats.fetch_data(report="powerPlay")  # Default sort is "wins"

            expected_season = (
                20232024  # Corrected: (2024-1) * 10000 + 2024 since January < 7
            )
            mock_client.get.assert_called_once_with(
                endpoint="stats",
                path=f"team/powerPlay?isAggregate=False&isGame=True&limit=-1&start=0&sort=wins&cayenneExp=seasonId={expected_season}",
                params=None,
                web=False,
            )

    def test_fetch_data_empty_response(self, mock_client: Mock):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_client.get.return_value = mock_response

        stats = TeamStats(mock_client, obj_id=10)
        stats.fetch_data(report="summary", season=20232024)

        # Verify data wasn't updated since response was empty
        assert stats._data == {}

    def test_fetch_data_key_error_if_data_key_missing(self, mock_client: Mock):
        mock_response = Mock()
        mock_response.status_code = 200  # Status code is fine, but data key is missing
        mock_response.json.return_value = {
            "message": "No data found"
        }  # Missing "data" key
        mock_client.get.return_value = mock_response

        stats = TeamStats(mock_client, obj_id=10)
        with pytest.raises(KeyError) as exc_info:
            stats.fetch_data(report="summary", season=20232024)
        assert "'data'" in str(exc_info.value)

    def test_fetch_data_live(self, real_client: HttpClient):
        stats = TeamStats(real_client, obj_id=10)  # Toronto Maple Leafs
        stats.fetch_data(season=20232024)  # Use a recent season

        assert stats._data, "Data should be populated by the live API call"
        for team in stats.teams:
            assert team.team_id, "Team should have a team_id"
            assert team.team_full_name, "Team should have a team_full_name"
            assert team.wins is not None, "Team should have wins"
            assert team.points is not None, "Team should have points"
