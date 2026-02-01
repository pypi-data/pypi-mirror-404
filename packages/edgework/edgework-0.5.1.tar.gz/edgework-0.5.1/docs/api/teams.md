# Teams

Team-related functionality in Edgework.

## Team Methods

::: edgework.Edgework.team_stats
    options:
      show_root_heading: false

::: edgework.Edgework.get_teams
    options:
      show_root_heading: false

::: edgework.Edgework.get_roster
    options:
      show_root_heading: false

## Team Model

::: edgework.models.team.Team

## Roster Model

::: edgework.models.team.Roster

## Team Client

::: edgework.clients.team_client.TeamClient

## Team Model

::: edgework.models.team.Team

## Roster Model

::: edgework.models.team.Roster

## Usage Examples

### Getting Team Information

```python
from edgework import Edgework

client = Edgework()

# Get team statistics
team_stats = client.team_stats(
    season="2023-2024",
    sort="points",
    limit=10
)

for team in team_stats:
    print(f"{team.name}: {team.points} points")
```

### Working with Team Objects

```python
# Assuming you have a Team object
team = team_stats[0]  # First team from stats

print(f"Team: {team.full_name}")
print(f"Abbreviation: {team.abbrev}")
print(f"Location: {team.location}")
```

### Getting Team Rosters

```python
from edgework import Edgework

client = Edgework()

# Get team statistics first to get team objects
team_stats = client.team_stats(season="2023-2024", limit=1)
team = team_stats[0]

# Get current roster
roster = team.get_roster()

print(f"Roster for {team.name}:")
print(f"Forwards: {len(roster.forwards)}")
print(f"Defensemen: {len(roster.defensemen)}")
print(f"Goalies: {len(roster.goalies)}")
```

### Team Schedule

```python
# Get team schedule
schedule = team.get_schedule(season="2023-2024")

# Get current season schedule
current_schedule = team.get_schedule()
```

### Team Prospects

```python
# Get team prospects
prospects = team.get_prospects()
```

## Team Properties

### Basic Information
- `team_id` - Unique team identifier
- `team_abbrev` - Team abbreviation (e.g., "TOR", "MTL")
- `team_name` - Team name
- `full_name` - Full team name
- `location_name` - Team location
- `team_common_name` - Common team name
- `team_place_name` - Team place name

### Branding
- `logo` - Team logo URL
- `dark_logo` - Dark version of team logo
- `website` - Team website URL

### League Information
- `conference` - Conference name
- `division` - Division name
- `franchise_id` - Franchise identifier
- `active` - Whether team is active

### Localization
- `french_name` - French team name
- `french_place_name` - French place name

## Roster Properties

### Basic Information
- `season` - Season for the roster
- `roster_type` - Type of roster
- `team_abbrev` - Team abbreviation
- `team_id` - Team identifier

### Players
- `players` - List of all players
- `forwards` - List of forwards
- `defensemen` - List of defensemen
- `goalies` - List of goalies

## Advanced Usage

### Working with Rosters

```python
from edgework import Edgework

client = Edgework()

# Get a team
team_stats = client.team_stats(season="2023-2024", limit=1)
team = team_stats[0]

# Get roster
roster = team.get_roster()

# Analyze roster composition
print(f"Forwards:")
for player in roster.forwards:
    print(f"  {player.first_name} {player.last_name} - #{player.sweater_number}")

print(f"\nDefensemen:")
for player in roster.defensemen:
    print(f"  {player.first_name} {player.last_name} - #{player.sweater_number}")

print(f"\nGoalies:")
for player in roster.goalies:
    print(f"  {player.first_name} {player.last_name} - #{player.sweater_number}")
```

### Historical Rosters

```python
# Get roster for a specific season
historical_roster = team.get_roster(season=20222023)

print(f"Roster for {team.name} in 2022-2023:")
print(f"Total players: {len(historical_roster.players)}")
```

### Team Statistics Analysis

```python
from edgework import Edgework

client = Edgework()

# Get all team stats
all_teams = client.team_stats(season="2023-2024")

# Sort by different metrics
by_points = sorted(all_teams, key=lambda t: t.points, reverse=True)
by_goals = sorted(all_teams, key=lambda t: t.goals_for, reverse=True)
by_defense = sorted(all_teams, key=lambda t: t.goals_against)

print("Top 5 teams by points:")
for i, team in enumerate(by_points[:5], 1):
    print(f"{i}. {team.name}: {team.points} points")

print("\nTop 5 teams by goals:")
for i, team in enumerate(by_goals[:5], 1):
    print(f"{i}. {team.name}: {team.goals_for} goals")

print("\nTop 5 defensive teams:")
for i, team in enumerate(by_defense[:5], 1):
    print(f"{i}. {team.name}: {team.goals_against} goals against")
```

### Team Schedules and Stats

```python
# Get detailed team information
team_schedule = team.get_schedule(season="2023-2024")
team_stats_response = team.get_stats(season="2023-2024", game_type=2)

print(f"Schedule and stats retrieved for {team.name}")
```
