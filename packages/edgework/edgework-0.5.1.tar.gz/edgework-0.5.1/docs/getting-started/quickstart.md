# Quick Start

This guide will help you get started with Edgework quickly.

## Basic Setup

```python
from edgework import Edgework

# Initialize the client
client = Edgework()
```

## Your First API Call

Let's start by getting some player statistics:

```python
# Get skater stats for the current season
stats = client.skater_stats(
    season="2023-2024",
    limit=5,
    sort="points"
)

for player in stats:
    print(f"{player.name}: {player.points} points")
```

## Common Operations

### Getting Player Information

```python
# Get all active players
players = client.players(active_only=True)

# Get specific player by ID
player = players[0]  # First player from the list
print(f"Player: {player.first_name} {player.last_name}")
print(f"Team: {player.current_team_abbr}")
```

### Working with Teams

```python
# Get team statistics
team_stats = client.team_stats(
    season="2023-2024",
    sort="points",
    limit=10
)

for team in team_stats:
    print(f"{team.team_name}: {team.points} points")
```

### Getting Game Schedules

```python
# Get current schedule
schedule = client.schedule()

# Get schedule for a specific date
schedule = client.schedule(date="2024-01-15")
```

## Season Format

Edgework uses the NHL's season format: `"YYYY-YYYY"` (e.g., `"2023-2024"`).

```python
# Correct format
stats = client.skater_stats(season="2023-2024")

# This will raise a ValueError
stats = client.skater_stats(season="2024")  # Wrong format
```

## Error Handling

```python
try:
    stats = client.skater_stats(season="2023-2024")
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"API error: {e}")
```

## Next Steps

- Check out the [API Reference](../api/client.md) for detailed documentation
- Explore [Examples](../examples/basic-usage.md) for more complex use cases
- Learn about [Configuration](configuration.md) options
