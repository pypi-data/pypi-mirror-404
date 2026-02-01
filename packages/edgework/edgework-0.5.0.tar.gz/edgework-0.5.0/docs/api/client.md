# Edgework Client

The main client class for interacting with NHL APIs.

## Main Client Class

::: edgework.Edgework

## HTTP Client

::: edgework.http_client.HttpClient

## Season Validation

::: edgework.edgework._validate_season_format

## Usage Examples

### Basic Initialization

```python
from edgework import Edgework

# Default initialization
client = Edgework()

# Custom user agent
client = Edgework(user_agent="MyApp/1.0")
```

### Season Format Validation

The client includes built-in season format validation:

```python
from edgework import Edgework

client = Edgework()

# Valid season format
stats = client.skater_stats(season="2023-2024")

# Invalid format - will raise ValueError
try:
    stats = client.skater_stats(season="2024")
except ValueError as e:
    print(f"Error: {e}")
```

## Available Methods

### Player Methods

- `players(active_only=True)` - Get list of players
- `skater_stats(season, ...)` - Get skater statistics
- `goalie_stats(season, ...)` - Get goalie statistics

### Team Methods

- `team_stats(season, ...)` - Get team statistics

### Schedule Methods

- `schedule(...)` - Get game schedules

### Draft Methods

- `draft_rankings(...)` - Get draft rankings

### Standings Methods

- `standings(...)` - Get team standings

## Error Handling

The client raises various exceptions for different error conditions:

- `ValueError` - Invalid input parameters (e.g., wrong season format)
- `HTTPError` - API request failures
- `Exception` - Other unexpected errors

```python
from edgework import Edgework

client = Edgework()

try:
    stats = client.skater_stats(season="2023-2024")
except ValueError as e:
    print(f"Invalid parameters: {e}")
except Exception as e:
    print(f"API error: {e}")
```
