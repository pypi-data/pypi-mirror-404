# NHL API Documentation

Information about the NHL APIs that Edgework interacts with.

## Overview

Edgework provides a Python interface to various NHL APIs, making it easy to access NHL data including:

- Player information and statistics
- Team information and rosters
- Game schedules and results
- League standings
- Historical data

## API Endpoints

The NHL provides several API endpoints that Edgework utilizes:

### Player Endpoints
- Active players list
- Player statistics (skaters and goalies)
- Player biographical information

### Team Endpoints
- Team information
- Team rosters
- Team statistics
- Team schedules

### Schedule Endpoints
- Game schedules
- Game results
- Season schedules

### Statistics Endpoints
- Skater statistics
- Goalie statistics
- Team statistics
- League standings

## Data Formats

### Season Format
All season parameters should be provided in the format `"YYYY-YYYY"`, for example:
- `"2023-2024"` for the 2023-2024 season
- `"2022-2023"` for the 2022-2023 season

### Game Types
- `2` - Regular season games
- `3` - Playoff games

### Player Positions
- `C` - Center
- `LW` - Left Wing
- `RW` - Right Wing
- `D` - Defenseman
- `G` - Goaltender

## Rate Limiting and Best Practices

### API Usage Guidelines
- Be respectful of the NHL's servers
- Implement caching where appropriate
- Use appropriate delays between requests
- Handle errors gracefully

### Error Handling
Common errors you might encounter:
- Network timeouts
- Invalid season formats
- API rate limiting
- Data not available for requested parameters

## Data Availability

### Current Season Data
- Live game data
- Up-to-date player statistics
- Current team standings

### Historical Data
- Previous season statistics
- Historical player data
- Archive game results

Note: Data availability may vary depending on the specific endpoint and time of year.

## Attribution

When using NHL data in your applications, please:
- Acknowledge that the data comes from the NHL
- Follow NHL's terms of service
- Respect intellectual property rights

## Technical Notes

### Response Formats
- All API responses are in JSON format
- Timestamps are typically in UTC
- Numeric values are returned as appropriate types (int, float)

### Data Consistency
- Player IDs are consistent across endpoints
- Team abbreviations are standardized
- Season formats are consistent

For more detailed information about specific data structures, see the API Reference sections for each model type.
