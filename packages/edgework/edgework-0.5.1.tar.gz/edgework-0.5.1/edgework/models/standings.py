from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, Field


class Seeding(BaseModel):
    """
    Seeding model to store seeding information.

    Attributes:
        clinch_indicator (str): The clinch indicator.
        conference_abbrev (str): The conference abbreviation.
        conference_home_sequence (int): The conference home sequence.
    """

    conference_abbrev: str
    conference_home_sequence: int
    conference_l10_sequence: int
    conference_name: str
    conference_road_sequence: int
    conference_sequence: int
    date: datetime
    division_abbrev: str
    division_home_sequence: int
    division_l10_sequence: int
    division_name: str
    division_road_sequence: int
    division_sequence: int
    game_type_id: int
    games_played: int
    goal_differential: int
    goal_differential_pctg: float
    goal_against: int
    goal_for: int
    goals_for_pctg: float
    home_games_played: int
    home_goal_differential: int
    home_goals_against: int
    home_goals_for: int
    home_losses: int
    home_ot_losses: int
    home_points: int
    home_regulation_plus_ot_wins: int
    home_regulation_wins: int
    home_ties: int
    home_wins: int
    l10_games_played: int
    l10_goal_differential: int
    l10_goals_against: int
    l10_goals_for: int
    l10_losses: int
    l10_ot_losses: int
    l10_points: int
    l10_regulation_plus_ot_wins: int
    l10_regulation_wins: int
    l10_ties: int
    l10_wins: int
    league_home_sequence: int
    league_l10_sequence: int
    league_road_sequence: int
    league_sequence: int
    losses: int
    ot_losses: int
    place_name: Dict[str, str]
    point_pctg: float
    points: int
    regulation_plus_ot_win_pctg: float
    regulation_plus_ot_wins: int
    regulation_win_pctg: float
    regulation_wins: int
    road_games_played: int
    road_goal_differential: int
    road_goals_against: int
    road_goals_for: int
    road_losses: int
    road_ot_losses: int
    road_points: int
    road_regulation_plus_ot_wins: int
    road_regulation_wins: int
    road_ties: int
    road_wins: int
    season_id: int
    shootout_losses: int
    shootout_wins: int
    streak_code: str
    streak_count: int
    team_name: Dict[str, str]
    team_common_name: Dict[str, str]
    team_abbrev: Dict[str, str]
    team_logo: str
    ties: int
    waivers_sequence: int
    wildcard_sequence: int
    win_pctg: float
    wins: int
    clinch_indicator: str = ""


class Standings(BaseModel):
    """
    Standings model to store standings information.

    Attributes:
    season (int): The season the standings are for.
    standings (list[dict]): A list of standings for the season.
    """

    date: datetime
    seedings: List[Seeding]
    season: int = Field(default=-1)

    @property
    def east_standings(self):
        return [s for s in self.seedings if s.conference_abbrev == "E"]

    @property
    def west_standings(self):
        return [s for s in self.seedings if s.conference_abbrev == "W"]
