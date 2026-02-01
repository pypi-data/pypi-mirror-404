# Basic Usage Examples

This guide provides basic examples for getting started with Edgework.

## Installation

```bash
pip install edgework
```

## Basic Client Setup

```python
from edgework import Edgework

# Initialize the client
client = Edgework()

# Optional: use custom user agent
client = Edgework(user_agent="MyApp/1.0")
```

## Getting Player Data

### Active Players

```python
from edgework import Edgework

client = Edgework()

# Get all active players
active_players = client.players(active_only=True)
print(f"Found {len(active_players)} active players")

# Get a single player
player = active_players[0]
print(f"Player: {player.first_name} {player.last_name}")
print(f"Team: {player.current_team_abbr}")
print(f"Position: {player.position}")
```

### Player Statistics

```python
# Get top scorers for the 2023-2024 season
top_scorers = client.skater_stats(
    season="2023-2024",
    sort="points",
    limit=10
)

print("Top 10 Point Scorers:")
for i, player in enumerate(top_scorers, 1):
    print(f"{i}. {player.name}: {player.points} points")
```

### Goalie Statistics

```python
# Get top goalies by wins
top_goalies = client.goalie_stats(
    season="2023-2024",
    sort="wins",
    limit=5
)

print("Top 5 Goalies by Wins:")
for goalie in top_goalies:
    print(f"{goalie.name}: {goalie.wins} wins")
```

## Getting Team Data

### Team Statistics

```python
# Get team standings/statistics
team_stats = client.team_stats(season="2023-2024")

print("Team Standings:")
for team in team_stats[:10]:  # Top 10 teams
    print(f"{team.name}: {team.points} points")
```

### Team Rosters

```python
# Get a team from stats and then get its roster
teams = client.team_stats(season="2023-2024", limit=1)
team = teams[0]

# Get the team's current roster
roster = team.get_roster()

print(f"Roster for {team.name}:")
print(f"Forwards: {len(roster.forwards)}")
print(f"Defensemen: {len(roster.defensemen)}")
print(f"Goalies: {len(roster.goalies)}")
```

## Schedule Data

```python
# Get current schedule
current_schedule = client.schedule()

print(f"Found {len(current_schedule.games)} games")

# Get schedule for specific date range
schedule = client.schedule(
    start_date="2024-01-01",
    end_date="2024-01-07"
)
```

## Error Handling

```python
from edgework import Edgework

client = Edgework()

try:
    # This will raise a ValueError due to invalid season format
    stats = client.skater_stats(season="2024")
except ValueError as e:
    print(f"Invalid season format: {e}")

try:
    # Handle API errors
    players = client.players()
except Exception as e:
    print(f"API error: {e}")
```

## Working with Results

```python
# Most methods return lists of model objects
players = client.players(active_only=True)

# Filter results
centers = [p for p in players if p.position == "C"]
maple_leafs = [p for p in players if p.current_team_abbr == "TOR"]

# Sort results
sorted_by_number = sorted(players, key=lambda p: p.sweater_number or 0)

print(f"Found {len(centers)} centers")
print(f"Found {len(maple_leafs)} Maple Leafs players")
```
