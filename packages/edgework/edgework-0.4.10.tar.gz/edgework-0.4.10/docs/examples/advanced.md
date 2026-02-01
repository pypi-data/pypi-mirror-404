# Advanced Examples

Advanced usage patterns and examples for Edgework.

## Custom Filtering and Analysis

### Player Analysis

```python
from edgework import Edgework
from collections import defaultdict

client = Edgework()

# Get player statistics
players = client.skater_stats(season="2023-2024", limit=100)

# Analyze by position
position_stats = defaultdict(list)
for player in players:
    position_stats[player.position].append(player)

for position, players_list in position_stats.items():
    avg_points = sum(p.points for p in players_list) / len(players_list)
    print(f"{position}: {len(players_list)} players, avg {avg_points:.1f} points")
```

### Team Performance Analysis

```python
# Compare team offensive and defensive performance
teams = client.team_stats(season="2023-2024")

# Sort by different metrics
by_offense = sorted(teams, key=lambda t: t.goals_for, reverse=True)
by_defense = sorted(teams, key=lambda t: t.goals_against)

print("Top 5 Offensive Teams:")
for team in by_offense[:5]:
    print(f"{team.name}: {team.goals_for} goals for")

print("\nTop 5 Defensive Teams:")
for team in by_defense[:5]:
    print(f"{team.name}: {team.goals_against} goals against")
```

## Historical Data Comparison

### Multi-Season Player Analysis

```python
seasons = ["2022-2023", "2023-2024"]
player_comparison = {}

for season in seasons:
    stats = client.skater_stats(season=season, limit=50)
    player_comparison[season] = {p.name: p.points for p in stats}

# Find players who improved
for player in player_comparison["2023-2024"]:
    if player in player_comparison["2022-2023"]:
        old_points = player_comparison["2022-2023"][player]
        new_points = player_comparison["2023-2024"][player]
        improvement = new_points - old_points
        if improvement > 10:
            print(f"{player}: +{improvement} points ({old_points} → {new_points})")
```

## Data Export and Visualization

### Export to CSV

```python
import csv
from edgework import Edgework

client = Edgework()
players = client.skater_stats(season="2023-2024", limit=100)

# Export player stats to CSV
with open('player_stats.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['name', 'team', 'position', 'games', 'goals', 'assists', 'points']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for player in players:
        writer.writerow({
            'name': player.name,
            'team': player.team_abbr,
            'position': player.position,
            'games': player.games_played,
            'goals': player.goals,
            'assists': player.assists,
            'points': player.points
        })

print("Player stats exported to player_stats.csv")
```

### Data Visualization with Matplotlib

```python
import matplotlib.pyplot as plt
from edgework import Edgework

client = Edgework()
teams = client.team_stats(season="2023-2024")

# Create scatter plot of goals for vs goals against
goals_for = [team.goals_for for team in teams]
goals_against = [team.goals_against for team in teams]
team_names = [team.abbrev for team in teams]

plt.figure(figsize=(10, 8))
plt.scatter(goals_for, goals_against, alpha=0.7)

# Add team labels
for i, name in enumerate(team_names):
    plt.annotate(name, (goals_for[i], goals_against[i]),
                xytext=(5, 5), textcoords='offset points')

plt.xlabel('Goals For')
plt.ylabel('Goals Against')
plt.title('Team Offensive vs Defensive Performance')
plt.grid(True, alpha=0.3)
plt.show()
```

## Roster Management

### Team Roster Analysis

```python
from edgework import Edgework

client = Edgework()

# Get a team and analyze its roster
teams = client.team_stats(season="2023-2024", limit=5)

for team in teams:
    roster = team.get_roster()

    # Analyze roster by age (if birth_date available)
    ages = []
    for player in roster.players:
        if hasattr(player, 'birth_date') and player.birth_date:
            # Calculate age from birth_date
            from datetime import datetime
            birth_year = int(player.birth_date[:4])
            age = 2024 - birth_year
            ages.append(age)

    if ages:
        avg_age = sum(ages) / len(ages)
        print(f"{team.name}: {len(roster.players)} players, avg age {avg_age:.1f}")
```

### Position Distribution

```python
# Analyze position distribution across teams
position_counts = defaultdict(int)

teams = client.team_stats(season="2023-2024", limit=10)
for team in teams:
    roster = team.get_roster()
    for player in roster.players:
        position_counts[player.position] += 1

print("Position Distribution Across Teams:")
for position, count in position_counts.items():
    print(f"{position}: {count} players")
```

## Schedule Analysis

### Game Scheduling Patterns

```python
from edgework import Edgework
from datetime import datetime
from collections import Counter

client = Edgework()

# Get schedule for a month
schedule = client.schedule(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# Analyze games by day of week
game_days = []
for game in schedule.games:
    game_date = datetime.fromisoformat(game.start_time_utc.replace('Z', '+00:00'))
    game_days.append(game_date.strftime('%A'))

day_counts = Counter(game_days)
print("Games by Day of Week:")
for day, count in day_counts.items():
    print(f"{day}: {count} games")
```

## Performance Monitoring

### API Response Timing

```python
import time
from edgework import Edgework

client = Edgework()

# Time different API calls
operations = [
    ("Get Players", lambda: client.players(active_only=True)),
    ("Get Skater Stats", lambda: client.skater_stats(season="2023-2024", limit=50)),
    ("Get Team Stats", lambda: client.team_stats(season="2023-2024")),
    ("Get Schedule", lambda: client.schedule()),
]

for name, operation in operations:
    start_time = time.time()
    result = operation()
    end_time = time.time()

    print(f"{name}: {end_time - start_time:.2f}s ({len(result)} items)")
```

## Custom Data Models

### Creating Summary Objects

```python
from dataclasses import dataclass
from typing import List
from edgework import Edgework

@dataclass
class TeamSummary:
    name: str
    points: int
    goals_for: int
    goals_against: int
    goal_differential: int

    @classmethod
    def from_team_stats(cls, team_stats):
        return cls(
            name=team_stats.name,
            points=team_stats.points,
            goals_for=team_stats.goals_for,
            goals_against=team_stats.goals_against,
            goal_differential=team_stats.goals_for - team_stats.goals_against
        )

# Usage
client = Edgework()
teams = client.team_stats(season="2023-2024")
summaries = [TeamSummary.from_team_stats(team) for team in teams]

# Sort by goal differential
summaries.sort(key=lambda s: s.goal_differential, reverse=True)

print("Teams by Goal Differential:")
for summary in summaries[:10]:
    print(f"{summary.name}: +{summary.goal_differential}")
```
