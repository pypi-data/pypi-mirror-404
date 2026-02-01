# Statistics

Statistical functionality in Edgework.

## Statistics Methods

::: edgework.Edgework.skater_stats
    options:
      show_root_heading: false

::: edgework.Edgework.goalie_stats
    options:
      show_root_heading: false

::: edgework.Edgework.team_stats
    options:
      show_root_heading: false

## Skater Statistics Model

::: edgework.models.stats.SkaterStats

## Goalie Statistics Model

::: edgework.models.stats.GoalieStats

## Team Statistics Model

::: edgework.models.stats.TeamStats

## Statistics Client

::: edgework.clients.stats_client.StatsClient

## Skater Statistics

::: edgework.models.stats.SkaterStats

## Goalie Statistics

::: edgework.models.stats.GoalieStats

## Team Statistics

::: edgework.models.stats.TeamStats

## Usage Examples

### Skater Statistics

```python
from edgework import Edgework

client = Edgework()

# Get top point scorers
top_scorers = client.skater_stats(
    season="2023-2024",
    sort="points",
    direction="DESC",
    limit=10
)

print("Top 10 Point Scorers:")
for i, player in enumerate(top_scorers, 1):
    print(f"{i}. {player.name}: {player.points} points ({player.goals}G, {player.assists}A)")
```

### Advanced Skater Stats

```python
# Get assists leaders
assist_leaders = client.skater_stats(
    season="2023-2024",
    sort="assists",
    limit=10
)

# Get goal scorers
goal_leaders = client.skater_stats(
    season="2023-2024",
    sort="goals",
    limit=10
)

# Get plus/minus leaders
plus_minus_leaders = client.skater_stats(
    season="2023-2024",
    sort="plusMinus",
    limit=10
)
```

### Goalie Statistics

```python
# Get top goalies by wins
top_goalies = client.goalie_stats(
    season="2023-2024",
    sort="wins",
    limit=10
)

print("Top 10 Goalies by Wins:")
for i, goalie in enumerate(top_goalies, 1):
    print(f"{i}. {goalie.name}: {goalie.wins} wins")
    print(f"   GAA: {goalie.goals_against_average:.2f}, SV%: {goalie.save_percentage:.3f}")
```

### Team Statistics

```python
# Get team standings
team_standings = client.team_stats(
    season="2023-2024",
    sort="points",
    limit=32  # All NHL teams
)

print("NHL Standings:")
for i, team in enumerate(team_standings, 1):
    print(f"{i}. {team.team_name}: {team.points} points ({team.wins}-{team.losses}-{team.ot_losses})")
```

## Statistical Categories

### Skater Stats
- **Scoring**: Goals, Assists, Points
- **Shooting**: Shots, Shooting Percentage
- **Time**: Games Played, Time on Ice
- **Advanced**: Plus/Minus, Penalty Minutes, Power Play Points, Short Handed Points
- **Faceoffs**: Faceoff Wins, Faceoff Win Percentage
- **Hits**: Hits, Blocked Shots

### Goalie Stats
- **Record**: Wins, Losses, Overtime Losses
- **Save Stats**: Saves, Save Percentage
- **Goals**: Goals Against, Goals Against Average
- **Shutouts**: Shutout wins
- **Time**: Games Played, Time on Ice

### Team Stats
- **Record**: Wins, Losses, Overtime Losses, Points
- **Scoring**: Goals For, Goals Against, Goal Differential
- **Special Teams**: Power Play %, Penalty Kill %
- **Shot Stats**: Shots For, Shots Against
- **Discipline**: Penalty Minutes

## Sorting and Filtering

### Multiple Sort Criteria

```python
# Sort by multiple criteria (if supported by API)
stats = client.skater_stats(
    season="2023-2024",
    sort=["points", "goals"],
    direction=["DESC", "DESC"],
    limit=20
)
```

### Different Report Types

```python
# Summary report (default)
summary_stats = client.skater_stats(
    season="2023-2024",
    report="summary"
)

# Advanced stats (if available)
advanced_stats = client.skater_stats(
    season="2023-2024",
    report="advanced"
)
```

### Game Type Filtering

```python
# Regular season stats (default)
regular_season = client.skater_stats(
    season="2023-2024",
    game_type=2
)

# Playoff stats
playoff_stats = client.skater_stats(
    season="2023-2024",
    game_type=3
)
```

## Advanced Usage

### Statistical Analysis

```python
from edgework import Edgework

client = Edgework()

# Get comprehensive stats
all_skaters = client.skater_stats(
    season="2023-2024",
    limit=100
)

# Calculate team-based statistics
team_scoring = {}
for player in all_skaters:
    team = player.team_abbrev
    if team not in team_scoring:
        team_scoring[team] = {'goals': 0, 'assists': 0, 'points': 0, 'players': 0}

    team_scoring[team]['goals'] += player.goals
    team_scoring[team]['assists'] += player.assists
    team_scoring[team]['points'] += player.points
    team_scoring[team]['players'] += 1

# Display team offensive statistics
for team, stats in sorted(team_scoring.items(), key=lambda x: x[1]['points'], reverse=True):
    avg_points = stats['points'] / stats['players']
    print(f"{team}: {stats['points']} total points, {avg_points:.1f} avg per player")
```

### Comparative Analysis

```python
# Compare current season to previous season
current_season = client.skater_stats(season="2023-2024", limit=50)
previous_season = client.skater_stats(season="2022-2023", limit=50)

# Find players in both seasons
current_players = {p.player_id: p for p in current_season}
previous_players = {p.player_id: p for p in previous_season}

print("Players with improved scoring:")
for player_id in current_players:
    if player_id in previous_players:
        current = current_players[player_id]
        previous = previous_players[player_id]

        if current.points > previous.points:
            improvement = current.points - previous.points
            print(f"{current.name}: +{improvement} points ({previous.points} → {current.points})")
```

### Custom Statistics

```python
# Calculate custom metrics
def calculate_efficiency_rating(player):
    """Calculate a custom efficiency rating."""
    if player.games_played == 0:
        return 0

    points_per_game = player.points / player.games_played
    shot_efficiency = player.goals / player.shots if player.shots > 0 else 0

    return (points_per_game * 10) + (shot_efficiency * 100)

# Apply to all players
stats = client.skater_stats(season="2023-2024", limit=100)
efficient_players = []

for player in stats:
    efficiency = calculate_efficiency_rating(player)
    efficient_players.append((player, efficiency))

# Sort by efficiency
efficient_players.sort(key=lambda x: x[1], reverse=True)

print("Most Efficient Players:")
for i, (player, efficiency) in enumerate(efficient_players[:10], 1):
    print(f"{i}. {player.name}: {efficiency:.2f} efficiency rating")
```
