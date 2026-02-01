# Common Patterns

Common usage patterns and best practices for Edgework.

## Initialization Patterns

### Basic Client Setup

```python
from edgework import Edgework

# Standard initialization
client = Edgework()

# With custom user agent for your application
client = Edgework(user_agent="MyHockeyApp/1.0")
```

### Error Handling Setup

```python
from edgework import Edgework

def create_client():
    """Create client with error handling."""
    try:
        client = Edgework()
        # Test the connection with a simple call
        client.players(active_only=True)
        return client
    except Exception as e:
        print(f"Failed to initialize client: {e}")
        return None

client = create_client()
if client:
    print("Client initialized successfully")
```

## Data Retrieval Patterns

### Pagination and Limiting

```python
# Get data in chunks to avoid large responses
def get_all_players_chunked(client, chunk_size=100):
    """Get all players in manageable chunks."""
    all_players = []
    offset = 0

    while True:
        # Note: Actual pagination depends on API support
        chunk = client.players(active_only=True)
        if not chunk:
            break
        all_players.extend(chunk)
        break  # For now, API doesn't support pagination

    return all_players
```

### Caching Results

```python
from functools import lru_cache
from edgework import Edgework

class CachedEdgework:
    def __init__(self):
        self.client = Edgework()

    @lru_cache(maxsize=128)
    def get_team_stats_cached(self, season):
        """Cache team stats to avoid repeated API calls."""
        return tuple(self.client.team_stats(season=season))

    @lru_cache(maxsize=128)
    def get_players_cached(self, active_only=True):
        """Cache player list."""
        return tuple(self.client.players(active_only=active_only))

# Usage
cached_client = CachedEdgework()
stats1 = cached_client.get_team_stats_cached("2023-2024")  # API call
stats2 = cached_client.get_team_stats_cached("2023-2024")  # Cached result
```

## Data Processing Patterns

### Filtering and Sorting

```python
from edgework import Edgework

client = Edgework()

def get_top_players_by_position(season, position, stat='points', limit=10):
    """Get top players for a specific position."""
    all_players = client.skater_stats(season=season, limit=200)

    # Filter by position
    position_players = [p for p in all_players if p.position == position]

    # Sort by specified stat
    sorted_players = sorted(
        position_players,
        key=lambda p: getattr(p, stat, 0),
        reverse=True
    )

    return sorted_players[:limit]

# Usage
top_centers = get_top_players_by_position("2023-2024", "C", "points", 5)
for player in top_centers:
    print(f"{player.name}: {player.points} points")
```

### Data Transformation

```python
def transform_team_data(teams):
    """Transform team data into a more usable format."""
    return [
        {
            'name': team.name,
            'abbrev': team.abbrev,
            'points': team.points,
            'wins': team.wins,
            'losses': team.losses,
            'goals_per_game': team.goals_for / team.games_played if team.games_played > 0 else 0,
            'goals_against_per_game': team.goals_against / team.games_played if team.games_played > 0 else 0,
        }
        for team in teams
    ]

# Usage
teams = client.team_stats(season="2023-2024")
transformed = transform_team_data(teams)
```

## Error Handling Patterns

### Robust API Calls

```python
import time
from edgework import Edgework

def safe_api_call(func, max_retries=3, delay=1):
    """Make API call with retry logic."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

# Usage
client = Edgework()
players = safe_api_call(lambda: client.players(active_only=True))
```

### Validation Patterns

```python
def validate_season(season):
    """Validate season format before API calls."""
    if not isinstance(season, str):
        raise ValueError("Season must be a string")

    if not season.count('-') == 1:
        raise ValueError("Season must be in format 'YYYY-YYYY'")

    years = season.split('-')
    if len(years) != 2:
        raise ValueError("Invalid season format")

    try:
        year1, year2 = int(years[0]), int(years[1])
        if year2 != year1 + 1:
            raise ValueError("Season years must be consecutive")
    except ValueError:
        raise ValueError("Season years must be integers")

    return season

# Usage
def get_stats_safe(client, season):
    validated_season = validate_season(season)
    return client.skater_stats(season=validated_season)
```

## Working with Rosters

### Team Roster Analysis

```python
def analyze_team_roster(team):
    """Analyze a team's roster composition."""
    roster = team.get_roster()

    analysis = {
        'total_players': len(roster.players),
        'forwards': len([p for p in roster.players if p.position in ['C', 'LW', 'RW']]),
        'defensemen': len([p for p in roster.players if p.position == 'D']),
        'goalies': len([p for p in roster.players if p.position == 'G']),
        'positions': {}
    }

    # Count by specific position
    for player in roster.players:
        pos = player.position
        analysis['positions'][pos] = analysis['positions'].get(pos, 0) + 1

    return analysis

# Usage
teams = client.team_stats(season="2023-2024", limit=5)
for team in teams:
    analysis = analyze_team_roster(team)
    print(f"{team.name}: {analysis['forwards']}F, {analysis['defensemen']}D, {analysis['goalies']}G")
```

## Statistical Analysis Patterns

### Comparison Functions

```python
def compare_players(player1, player2, stats=['goals', 'assists', 'points']):
    """Compare two players across multiple statistics."""
    comparison = {}

    for stat in stats:
        val1 = getattr(player1, stat, 0)
        val2 = getattr(player2, stat, 0)
        comparison[stat] = {
            'player1': val1,
            'player2': val2,
            'difference': val1 - val2,
            'better': player1.name if val1 > val2 else player2.name
        }

    return comparison

# Usage
players = client.skater_stats(season="2023-2024", limit=10)
if len(players) >= 2:
    comparison = compare_players(players[0], players[1])
    for stat, data in comparison.items():
        print(f"{stat}: {data['better']} is better ({data['difference']:+d})")
```

### League Leaders

```python
def get_league_leaders(client, season, categories):
    """Get league leaders in multiple categories."""
    leaders = {}

    for category in categories:
        try:
            stats = client.skater_stats(
                season=season,
                sort=category,
                limit=5
            )
            leaders[category] = stats
        except Exception as e:
            print(f"Error getting {category} leaders: {e}")
            leaders[category] = []

    return leaders

# Usage
categories = ['goals', 'assists', 'points', 'plus_minus']
leaders = get_league_leaders(client, "2023-2024", categories)

for category, players in leaders.items():
    print(f"\n{category.title()} Leaders:")
    for i, player in enumerate(players, 1):
        stat_value = getattr(player, category, 'N/A')
        print(f"{i}. {player.name}: {stat_value}")
```

## Data Export Patterns

### JSON Export

```python
import json
from datetime import datetime

def export_to_json(data, filename, include_metadata=True):
    """Export data to JSON with metadata."""
    export_data = {
        'data': data,
    }

    if include_metadata:
        export_data['metadata'] = {
            'exported_at': datetime.now().isoformat(),
            'record_count': len(data) if isinstance(data, list) else 1,
            'source': 'Edgework NHL API Client'
        }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, default=str)

# Usage
teams = client.team_stats(season="2023-2024")
team_data = [
    {
        'name': team.name,
        'points': team.points,
        'wins': team.wins,
        'losses': team.losses
    }
    for team in teams
]
export_to_json(team_data, 'team_standings.json')
```

## Performance Patterns

### Batch Processing

```python
def process_teams_batch(client, season, batch_size=5):
    """Process teams in batches to manage memory."""
    teams = client.team_stats(season=season)

    for i in range(0, len(teams), batch_size):
        batch = teams[i:i + batch_size]

        # Process each team in the batch
        for team in batch:
            try:
                roster = team.get_roster()
                print(f"Processed {team.name}: {len(roster.players)} players")
            except Exception as e:
                print(f"Error processing {team.name}: {e}")

        # Optional: Add delay between batches
        time.sleep(0.5)

# Usage
process_teams_batch(client, "2023-2024")
```
