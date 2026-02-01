# Usage with LLMs & AI Agents

This page provides context-optimized documentation for Large Language Models (LLMs) and AI agents interacting with the `edgework` library.

## System Prompt

When using an LLM to generate `edgework` code, provide the following context:

> You are an expert in the `edgework` Python library for the NHL API. 
> The library uses a main `Edgework` client class.
> - **Seasons** are often passed as strings "YYYY-YYYY" (e.g., "2023-2024") to the high-level API, but internally converted to integers (20232024).
> - **Sorting** uses parameters `sort` (snake_case property) and `direction` ("ASC" or "DESC").
> - **Models** (`Player`, `Team`) are dynamic; access attributes via properties or `get_attribute()`.
> - **Stats** are fetched via `client.skater_stats()` or `client.goalie_stats()`, which return model instances containing lists of data entities.

## API Map

### Main Client: `Edgework`

```python
from edgework import Edgework
client = Edgework()
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `players` | `(active_only: bool = True) -> list[Player]` | Get list of players. |
| `get_teams` | `() -> list[Team]` | Get list of all teams. |
| `skater_stats` | `(season="YYYY-YYYY", report="summary", sort="points", limit=10, ...) -> SkaterStats` | Get skater statistics. |
| `goalie_stats` | `(season="YYYY-YYYY", report="summary", sort="wins", limit=10, ...) -> GoalieStats` | Get goalie statistics. |
| `team_stats` | `(season="YYYY-YYYY", report="summary", sort="points", ...) -> TeamStats` | Get team statistics. |
| `get_schedule` | `() -> Schedule` | Get current schedule. |
| `get_schedule_for_date` | `(date: str) -> Schedule` | Get schedule for "YYYY-MM-DD". |
| `get_roster` | `(team_code: str, season="YYYY-YYYY") -> Roster` | Get team roster. |

### Data Models

#### `Player`
*   **Properties**: `name`, `full_name`, `position`, `sweater_number`, `current_team_abbr`, `age`, `height_formatted`, `weight`, `birth_city`, `birth_country`.
*   **Methods**: `get_attribute(name)`, `fetch_data()` (loads deep stats).

#### `Team`
*   **Properties**: `name` (e.g., "Toronto Maple Leafs"), `abbrev` ("TOR"), `location` ("Toronto"), `full_name`.
*   **Methods**: `get_roster()`, `get_schedule()`, `get_stats()`.

#### `Roster`
*   **Properties**: `players` (list of `Player`), `forwards`, `defensemen`, `goalies`.
*   **Methods**: `get_player_by_name(name)`, `get_player_by_number(num)`.

## One-Shot Examples

### 1. Find Top Scorers
```python
from edgework import Edgework

client = Edgework()
stats = client.skater_stats(
    season="2023-2024",
    report="summary", 
    sort="points", 
    limit=5
)

for player in stats.players:
    print(f"{player.player_name} ({player.team_abbrevs}): {player.points} pts")
```

### 2. Analyze Team Roster
```python
from edgework import Edgework

client = Edgework()
team_code = "EDM"
roster = client.get_roster(team_code)

print(f"{team_code} Roster:")
print(f"Forwards: {len(roster.forwards)}")
print(f"Defensemen: {len(roster.defensemen)}")
print(f"Goalies: {len(roster.goalies)}")

# Find specific player
mcdavid = roster.get_player_by_name("Connor McDavid")
if mcdavid:
    print(f"Captain: {mcdavid.name} (#{mcdavid.sweater_number})")
```

### 3. Get Schedule for Date
```python
from edgework import Edgework

client = Edgework()
schedule = client.get_schedule_for_date("2023-11-18")

print(f"Games on {schedule.date}:")
for game in schedule.games:
    print(f"{game.away_team.abbrev} @ {game.home_team.abbrev} - {game.start_time}")
```

### 4. Advanced Stats Filtering
```python
from edgework import Edgework

client = Edgework()
# Get top power play goal scorers
pp_leaders = client.skater_stats(
    season="2023-2024",
    report="powerPlay",
    sort="ppGoals",
    limit=10
)

for p in pp_leaders.players:
    print(f"{p.player_name}: {p.pp_goals} PPG")
```
