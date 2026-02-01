# Changelog

All notable changes to Edgework project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.9] - 2025-01-30

### Added
- **Game Model**: Implement `fetch_data()` method to fetch detailed game information from NHL API
- **Game Model**: Add comprehensive test suite for Game model with 25 test cases
- **Game Model**: Fix `Game.from_dict()` to properly pass `edgework_client` parameter

### Changed
- **Game Model**: Enable lazy loading for Game objects via BaseNHLModel `_fetch_if_not_fetched()`

## [0.4.8] - 2025-01-28

### Fixed
- **Schedule**: Fix date filtering to use correct API field `startTimeUTC` instead of non-existent `gameDate`
- **Tests**: Update test mocks to use `startTimeUTC` field matching actual API response

## [0.4.7] - 2025-01-28

### Fixed
- **Schedule**: Use nextStartDate pagination to avoid duplicate games when fetching schedule by date range
- **Schedule Client**: Added web=True parameter to get_schedule_for_date_range for correct API endpoint usage
- **Tests**: Added TestScheduleClient unit tests and TestScheduleIntegration live API tests

## [0.4.6] - 2025-01-28

### Fixed
- **Schedule**: Use nextStartDate pagination to avoid duplicate games when fetching schedule by date range
- **Schedule Client**: Added web=True parameter to get_schedule_for_date and get_schedule_for_date_range for correct API endpoint usage

## [0.4.5] - 2025-01-28

### Fixed
- **Schedule**: Use nextStartDate pagination to avoid duplicate games when fetching schedule by date range
- **Schedule Client**: Added web=True parameter to get_schedule_for_date and get_schedule_for_date_range for correct API endpoint usage

## [0.4.3] - 2025-01-28

### Fixed
- **Schedule**: Use nextStartDate pagination to avoid duplicate games when fetching schedule by date range
- **Schedule Client**: Added web=True parameter to get_schedule_for_date and get_schedule_for_date_range for correct API endpoint usage

## [0.3.1] - 2025-06-24

### Added
- **Teams**: Player retrieval methods to Roster class for easier access to team player data
- **Schedule**: String representation (`__str__`) method and fetched data flag for better debugging and state tracking
- **Models**: Enhanced string representations and improved type hints across Player, Schedule, and Team models
- **Documentation**: Comprehensive documentation suite including:
  - API reference documentation for all clients and models
  - Getting started guides (installation, quickstart, configuration)
  - Usage examples (basic, advanced, and common patterns)
  - Contributing guidelines and changelog documentation
  - MkDocs configuration for documentation site generation

### Enhanced
- **Schedule Client**: Improved error handling and data management capabilities
- **Models**: Better string representations for debugging and development experience
- **Type Hints**: Enhanced type annotations throughout the codebase for better IDE support

### Changed
- Updated User-Agent to EdgeworkClient/0.3.1

## [0.2.1] - 2025-06-19

### Fixed
- **Critical**: Fixed player client HTTP method causing 400 Bad Request errors
- Corrected `get()` to `get_raw()` for NHL search API endpoints in PlayerClient
- Added missing `datetime` import in player_client.py
- Ensured all 21 player attributes are properly mapped from NHL search API
- Fixed data type conversions for player_id and team_id fields

### Changed
- Updated User-Agent to EdgeworkClient/0.2.1

## [0.2.0] - 2025-06-19

### Added
- Version constant in `__init__.py` for programmatic access
- Comprehensive pytest test suite for `edgework.py` module
- `players()` method to fetch list of NHL players with active/inactive filtering
  - Returns list of Player objects with full player information
  - Supports `active_only=True` (default) for current players
  - Supports `active_only=False` for all players including retired/inactive
  - Player objects include name, position, team, and other NHL data

### Changed
- Updated project version from 0.1.0 to 0.2.0
- Updated default User-Agent from "EdgeworkClient/1.0" to "EdgeworkClient/0.2.0"

### Fixed
- Robust season string validation that properly validates "YYYY-YYYY" format
- Season validation now raises appropriate `ValueError` for invalid formats

## [0.1.0] - Previous Release

### Added
- Initial release of Edgework NHL API client
- Core functionality for fetching player, skater, goalie, and team statistics
- HTTP client with proper NHL API integration
- Basic model classes for data representation
