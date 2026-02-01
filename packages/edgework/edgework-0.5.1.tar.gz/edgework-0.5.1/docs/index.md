# Edgework - NHL API Client

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/problemxl/edgework/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://problemxl.github.io/edgework/)

A Python client library for interacting with NHL APIs, providing easy access to player statistics, team information, schedules, and more.

## 🏒 Features

- **Player Data**: Access active and historical player information
- **Statistics**: Get skater and goalie statistics with flexible filtering
- **Team Information**: Retrieve team rosters, stats, and schedules
- **Game Data**: Access game schedules and results
- **Easy to Use**: Simple, intuitive API with comprehensive documentation

## 📦 Installation

```bash
pip install edgework
```

## 🚀 Quick Start

```python
from edgework import Edgework

# Initialize the client
client = Edgework()

# Get active players
players = client.players(active_only=True)
print(f"Found {len(players)} active players")

# Get top scorers
top_scorers = client.skater_stats(
    season="2023-2024",
    sort="points",
    limit=10
)

for player in top_scorers:
    print(f"{player.name}: {player.points} points")
```

# Get player statistics for a season
stats = client.skater_stats(
    season="2023-2024",
    sort="points",
    limit=10
)

# Get team information
team_stats = client.team_stats(
    season="2023-2024",
    sort="points"
)
```

## Installation

```bash
pip install edgework
```

## Documentation

Full documentation is available at [https://markf.github.io/edgework/](https://markf.github.io/edgework/)

## API Coverage

Edgework provides access to:

### NHL Web API (api-web.nhle.com)
- Player information and statistics
- Team rosters and statistics
- Game data and schedules
- Standings and playoff information
- Draft data and prospects

### NHL Stats API (api.nhle.com/stats/rest)
- Advanced player statistics
- Team performance metrics
- Historical data
- Detailed game information

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/problemxl/edgework/blob/main/LICENSE) file for details.

## Disclaimer

This is an unofficial NHL API client. It is not affiliated with or endorsed by the National Hockey League.
