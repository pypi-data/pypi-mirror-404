# Configuration

Edgework provides several configuration options to customize its behavior.

## User Agent

You can customize the User-Agent string used for API requests:

```python
from edgework import Edgework

# Default user agent
client = Edgework()

# Custom user agent
client = Edgework(user_agent="MyApp/1.0")
```

## HTTP Client Configuration

The underlying HTTP client can be configured for various scenarios:

### Timeout Settings

```python
# The HTTP client uses sensible defaults, but you can customize
# timeouts by modifying the client after initialization
client = Edgework()

# Access the underlying HTTP client if needed
# (Advanced usage - not typically required)
```

### Proxy Configuration

If you're behind a corporate firewall or need to use a proxy:

```python
import httpx
from edgework import Edgework

# For advanced proxy configuration, you may need to modify
# the HTTP client directly (this is advanced usage)
```

## Rate Limiting

The NHL APIs may implement rate limiting. Edgework handles common HTTP errors gracefully:

```python
import time
from edgework import Edgework

client = Edgework()

# Implement your own rate limiting if needed
def get_stats_with_delay(season, delay=1):
    try:
        return client.skater_stats(season=season)
    except Exception as e:
        if "rate limit" in str(e).lower():
            time.sleep(delay)
            return client.skater_stats(season=season)
        raise
```

## Error Handling Configuration

Configure how your application handles different types of errors:

```python
from edgework import Edgework
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

client = Edgework()

def safe_api_call(func, *args, **kwargs):
    """Wrapper for safe API calls with logging."""
    try:
        return func(*args, **kwargs)
    except ValueError as e:
        logging.error(f"Invalid input: {e}")
        return None
    except Exception as e:
        logging.error(f"API error: {e}")
        return None

# Usage
stats = safe_api_call(client.skater_stats, season="2023-2024")
```

## Environment Variables

While Edgework doesn't use environment variables by default, you can implement your own configuration system:

```python
import os
from edgework import Edgework

# Example: Use environment variable for user agent
user_agent = os.getenv("NHL_API_USER_AGENT", "Edgework/0.3.1")
client = Edgework(user_agent=user_agent)
```

## Best Practices

### 1. Singleton Pattern

For applications that make multiple API calls, consider using a singleton pattern:

```python
from edgework import Edgework

class NHLApiClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = Edgework()
        return cls._instance

# Usage
client = NHLApiClient()
```

### 2. Configuration Class

Create a configuration class for your application:

```python
from dataclasses import dataclass
from edgework import Edgework

@dataclass
class EdgeworkConfig:
    user_agent: str = "MyApp/1.0"
    default_season: str = "2023-2024"
    default_limit: int = 50

class ConfiguredEdgework:
    def __init__(self, config: EdgeworkConfig):
        self.config = config
        self.client = Edgework(user_agent=config.user_agent)

    def get_top_scorers(self, limit=None):
        return self.client.skater_stats(
            season=self.config.default_season,
            limit=limit or self.config.default_limit,
            sort="points"
        )

# Usage
config = EdgeworkConfig(user_agent="MyHockeyApp/2.0")
client = ConfiguredEdgework(config)
scorers = client.get_top_scorers()
```

### 3. Caching

For applications that make repeated requests, consider implementing caching:

```python
from functools import lru_cache
from edgework import Edgework

class CachedEdgework:
    def __init__(self):
        self.client = Edgework()

    @lru_cache(maxsize=128)
    def get_skater_stats(self, season, sort="points", limit=50):
        """Cached version of skater_stats."""
        return self.client.skater_stats(
            season=season,
            sort=sort,
            limit=limit
        )

# Usage
client = CachedEdgework()
stats1 = client.get_skater_stats("2023-2024")  # API call
stats2 = client.get_skater_stats("2023-2024")  # Cached result
```
