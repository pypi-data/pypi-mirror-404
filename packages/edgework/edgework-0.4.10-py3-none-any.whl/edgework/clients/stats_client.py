from edgework.http_client import HttpClient
from edgework.models.stats import GoalieStats, SkaterStats, TeamStats
from edgework.utilities import dict_camel_to_snake


class StatsClient:
    skate_reports: list[str] = [
        "summary",
        "bios",
        "faceoffpercentages",
        "faceoffwins",
        "goalsForAgainst",
        "realtime",
        "penalties",
        "penaltykill",
        "penaltyShots",
        "powerplay",
        "puckPossessions",
        "summaryshooting",
        "percentages",
        "scoringRates",
        "scoringpergame",
        "shootout",
        "shottype",
        "timeonice",
    ]

    goalie_reports: list[str] = [
        "summary",
        "advanced",
        "bios",
        "daysrest",
        "penaltyShots",
        "savesByStrength",
        "shootout",
        "startedVsRelieved",
    ]

    team_reports: list[str] = [
        "summary",
        "faceoffpercentages",
        "daysbetweengames",
        "faceoffwins",
        "goalsagainstbystrength",
        "goalsbyperiod",
        "goalsforbystrength",
        "leadingtrailing",
        "realtime",
        "outshootoutshotby",
        "penalties",
        "penaltykill",
        "penaltykilltime",
        "powerplay",
        "powerplaytime",
        "summaryshooting",
        "percentages",
        "scoretrailfirst",
        "shootout",
        "shottype",
        "goalgames",
    ]

    def __init__(self, client: HttpClient):
        self._client = client

    def get_skaters_stats(
        self,
        report: str,
        aggregate: bool,
        game: bool,
        limit: int,
        start: int,
        sort: str,
        season: int,
    ) -> list[SkaterStats]:
        if report not in self.skate_reports:
            raise ValueError(f"Invalid report: {report}")

        response = self._client.get(
            f"en/skater/{report}?isAggregate={aggregate}&isGame={game}&limit="
            f"{limit}&start={start}&sort={sort}&cayenneExp=seasonId={season}"
        )

        data = response.json()["data"]
        skater_stats_dict = [dict_camel_to_snake(d) for d in data]

        return [SkaterStats(**d) for d in skater_stats_dict]

    def get_goalies_stats(
        self,
        season: int,
        report: str = "summary",
        aggregate: bool = False,
        game: bool = True,
        limit: int = -1,
        start: int = 0,
        sort: str = "wins",
    ) -> list[GoalieStats]:
        if report not in self.goalie_reports:
            raise ValueError(
                f"Invalid report: {report}, must be one of "
                f"{', '.join(self.goalie_reports)}"
            )

        url_path = (
            f"en/goalie/{report}?isAggregate={aggregate}&isGame={game}&limit="
            f"{limit}&start={start}&sort={sort}&cayenneExp=seasonId={season}"
        )
        response = self._client.get(path=url_path, params=None, web=False)
        data = response.json()["data"]

        skater_stats_dict = [dict_camel_to_snake(d) for d in data]
        return [GoalieStats(**d) for d in skater_stats_dict]

    def get_team_stats(
        self,
        season: int,
        report: str = "summary",
        aggregate: bool = False,
        game: bool = True,
        limit: int = -1,
        start: int = 0,
        sort: str = "wins",
    ) -> list[TeamStats]:
        response = self._client.get(f"en/team/stats?cayenneExp=seasonId={season}")
        data = response.json()["data"]
        team_stats_dict = [dict_camel_to_snake(d) for d in data]
        return [TeamStats(**d) for d in team_stats_dict]

    def get_team_stats(
        self,
        season: int,
        report: str = "summary",
        aggregate: bool = False,
        game: bool = True,
        limit: int = -1,
        start: int = 0,
        sort: str = "wins",
    ) -> list[TeamStats]:
        """
        Get team stats

        Params
        ------
        season: int
            The season to get stats for
        report: str
            The type of report to get, must be one of the following:
            'summary', 'faceoffpercentages', 'daysbetweengames', 'faceoffwins', 'goalsagainstbystrength',
            'goalsbyperiod', 'goalsforbystrength', 'leadingtrailing', 'realtime', 'outshootoutshotby',
            'penalties', 'penaltykill', 'penaltykilltime', 'powerplay', 'powerplaytime', 'summaryshooting
            'percentages', 'scoretrailfirst', 'shootout', 'shottype', 'goalgames'. Default is 'summary'.
        aggregate: bool
            Whether to aggregate the stats for the season. Default is False. `game` takes precedence over `aggregate`.
        game: bool
            Whether to get stats for games. Default is True. `game` takes precedence over `aggregate`.
        limit: int
            The number of results to return. Default is -1. If -1, all results are returned.
        start: int
            The index to start at. Default is 0.
        sort: str
            The field to sort by. Default is 'wins'.
        """

        if report not in self.team_reports:
            raise ValueError(
                f"Invalid report: {report}, must be one of "
                f"{', '.join(self.team_reports)}"
            )

        url_path = (
            f"en/team/{report}?isAggregate={aggregate}&isGame={game}&limit="
            f"{limit}&start={start}&sort={sort}&cayenneExp=seasonId={season}"
        )
        response = self._client.get(path=url_path, params=None, web=False)
        data = response.json()["data"]

        team_stats_dict = [dict_camel_to_snake(d) for d in data]
        return [TeamStats(**d) for d in team_stats_dict]
