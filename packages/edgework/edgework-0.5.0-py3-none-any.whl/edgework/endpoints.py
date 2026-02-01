from .const import API_VERSION

API_PATH: dict = {
    # Player endpoints
    "player_game_logs": "/{API_VERSION}/player/{player_id}/game-log/{season}/{game-type}",
    "player_game_log_now": "/{API_VERSION}/player/{player_id}/game-log/now",
    "player_landing": "/{API_VERSION}/player/{player_id}/landing",
    "player_spotlight": "/{API_VERSION}/player-spotlight",
    # Stats endpoints
    "skater_stats_now": "/{API_VERSION}/skater-stats-leaders/current",
    "skater_stats_season_game_type": "/{API_VERSION}/skater-stats-leaders/{season}/{game_type}",
    "goalie_stats_now": "/{API_VERSION}/goalie-stats-leaders/current",
    "goalie_stats_season_game_type": "/{API_VERSION}/goalie-stats-leaders/{season}/{game_type}",
    # Standings endpoints
    "standings": "/{API_VERSION}/standings/now",
    "standings_date": "/{API_VERSION}/standings/{date}",
    "standings_season": "/{API_VERSION}/standings-season",
    # Club stats endpoints
    "club_stats": "/{API_VERSION}/club-stats/{team}/now",
    "club_stats_season": "/{API_VERSION}/club-stats-season/{team}",
    "club_stats_season_season_game_type": "/{API_VERSION}/club-stats-season/{team}/{season}/{game_type}",
    "team_scoreboard": "/{API_VERSION}/scoreboard/{team}/now",
    # Team endpoints
    "teams": "team",
    # Roster endpoints
    "roster_current": "/{API_VERSION}/roster/{team}/current",
    "roster_season": "/{API_VERSION}/roster/{team}/{season}",
    "roster_season_team": "/{API_VERSION}/roster-season/{team}",
    "team_prospects": "/{API_VERSION}/prospects/{team}",
    # Schedule endpoints
    "club_schedule_season_now": "/{API_VERSION}/club-schedule-season/{team}/now",
    "club_schedule_season": "/{API_VERSION}/club-schedule-season/{team}/{season}",
    "club_schedule_month_now": "/{API_VERSION}/club-schedule/{team}/month/now",
    "club_schedule_month": "/{API_VERSION}/club-schedule/{team}/month/{month}",
    "club_schedule_week": "/{API_VERSION}/club-schedule/{team}/week/{date}",
    "club_schedule_week_now": "/{API_VERSION}/club-schedule/{team}/week/now",
    "schedule_now": "/{API_VERSION}/schedule/now",
    "schedule_date": "/{API_VERSION}/schedule/{date}",
    "schedule_calendar_now": "/{API_VERSION}/schedule-calendar/now",
    "schedule_calendar_date": "/{API_VERSION}/schedule-calendar/{date}",
    # Game endpoints
    "score_now": "/{API_VERSION}/score/now",
    "score_date": "/{API_VERSION}/score/{date}",
    "scoreboard_now": "/{API_VERSION}/scoreboard/now",
    "where_to_watch": "/{API_VERSION}/where-to-watch",
    "play_by_play": "/{API_VERSION}/gamecenter/{game_id}/play-by-play",
    "game_landing": "/{API_VERSION}/gamecenter/{game_id}/landing",
    "game_boxscore": "/{API_VERSION}/gamecenter/{game_id}/boxscore",
    "game_story": "/{API_VERSION}/wsc/game-story/{game_id}",
    "game_right_rail": "/{API_VERSION}/gamecenter/{game_id}/right-rail",
    "wsc_play_by_play": "/{API_VERSION}/wsc/play-by-play/{game_id}",
    # Network endpoints
    "tv_schedule_date": "/{API_VERSION}/network/tv-schedule/{date}",
    "tv_schedule_now": "/{API_VERSION}/network/tv-schedule/now",
    # Odds endpoints
    "partner_game": "/{API_VERSION}/partner-game/{country_code}/now",
    # Playoff endpoints
    "playoff_series_carousel": "/{API_VERSION}/playoff-series/carousel/{season}/",
    "playoff_series_schedule": "/{API_VERSION}/schedule/playoff-series/{season}/{series_letter}/",
    "playoff_bracket": "/{API_VERSION}/playoff-bracket/{year}",
    # Season endpoints
    "season": "/{API_VERSION}/season",
    # Draft endpoints
    "draft_rankings_now": "/{API_VERSION}/draft/rankings/now",
    "draft_rankings": "/{API_VERSION}/draft/rankings/{season}/{prospect_category}",
    "draft_tracker_picks_now": "/{API_VERSION}/draft-tracker/picks/now",
    "draft_picks_now": "/{API_VERSION}/draft/picks/now",
    "draft_picks": "/{API_VERSION}/draft/picks/{season}/{round}",
    # Miscellaneous endpoints
    "meta": "/{API_VERSION}/meta",
    "meta_game": "/{API_VERSION}/meta/game/{game_id}",
    "location": "/{API_VERSION}/location",
    "meta_playoff_series": "/{API_VERSION}/meta/playoff-series/{year}/{series_letter}",
    "postal_lookup": "/{API_VERSION}/postal-lookup/{postal_code}",
    "goal_replay": "/{API_VERSION}/ppt-replay/goal/{game_id}/{event_number}",
    "play_replay": "/{API_VERSION}/ppt-replay/{game_id}/{event_number}",
    "openapi_spec": "/model/{API_VERSION}/openapi.json",
}
