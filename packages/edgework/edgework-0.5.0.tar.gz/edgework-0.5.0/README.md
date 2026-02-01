# Edgework - NHL API Client

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

## 📚 Documentation

Full documentation is available at: **https://problemxl.github.io/edgework/**

### Local Documentation

To view documentation locally:

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python] pymdown-extensions

# Serve documentation locally
mkdocs serve

# Or use the helper script
python docs.py serve
```

The documentation will be available at `http://127.0.0.1:8000/edgework/`

## 🔧 API Reference

### Main Client

```python
from edgework import Edgework

client = Edgework(user_agent="MyApp/1.0")  # Optional custom user agent
```

### Player Methods

- `client.players(active_only=True)` - Get player list
- `client.skater_stats(season, ...)` - Get skater statistics
- `client.goalie_stats(season, ...)` - Get goalie statistics

### Team Methods

- `client.team_stats(season, ...)` - Get team statistics
- `client.get_teams()` - Get all teams
- `client.get_roster(team_code, season)` - Get team roster

### Schedule Methods

- `client.get_schedule()` - Get current schedule
- `client.get_schedule_for_date(date)` - Get schedule for specific date
- `client.get_schedule_for_date_range(start, end)` - Get schedule for date range

## 🛠️ Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/problemxl/edgework.git
cd edgework

# Install development dependencies
pdm install --dev

# Or using pip
pip install -e .
```

### Running Tests

```bash
pytest
```

### Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python] pymdown-extensions

# Build documentation
mkdocs build

# Serve locally
mkdocs serve
```

## 📊 Examples

### Getting Player Statistics

```python
from edgework import Edgework

client = Edgework()

# Get assists leaders
assist_leaders = client.skater_stats(
    season="2023-2024",
    sort="assists",
    limit=10
)

# Get goalie wins leaders
goalie_wins = client.goalie_stats(
    season="2023-2024",
    sort="wins",
    limit=5
)
```

### Working with Teams

```python
# Get team statistics
team_stats = client.team_stats(season="2023-2024")

# Get team roster
team = team_stats[0]  # First team
roster = team.get_roster()

print(f"Roster for {team.name}:")
print(f"Forwards: {len(roster.forwards)}")
print(f"Defensemen: {len(roster.defensemen)}")
print(f"Goalies: {len(roster.goalies)}")
```

## 🎯 Season Format

All season parameters should use the format `"YYYY-YYYY"`:
- `"2023-2024"` for the 2023-2024 season
- `"2022-2023"` for the 2022-2023 season

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](https://problemxl.github.io/edgework/contributing/) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚡ API Rate Limiting

Please be respectful of the NHL's servers:
- Implement appropriate delays between requests
- Cache responses when possible
- Handle errors gracefully

## 🙏 Acknowledgments

- NHL for providing the API data
- Contributors and maintainers
- The Python community

## 📞 Support

- 📖 [Documentation](https://problemxl.github.io/edgework/)
- 🐛 [Issues](https://github.com/problemxl/edgework/issues)
- 💬 [Discussions](https://github.com/problemxl/edgework/discussions)

---

Made with ❤️ for the hockey community
