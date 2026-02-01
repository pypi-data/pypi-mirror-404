# Installation

## Requirements

- Python 3.11 or higher
- Internet connection (for API requests)

## Install from PyPI

```bash
pip install edgework
```

## Install for Development

If you want to contribute to the project or run the latest development version:

```bash
# Clone the repository
git clone https://github.com/problemxl/edgework.git
cd edgework

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Dependencies

Edgework has the following main dependencies:

- **httpx**: Modern HTTP client for making API requests
- **pydantic**: Data validation and parsing
- **loguru**: Logging library

All dependencies will be installed automatically when you install Edgework.

## Verify Installation

To verify that Edgework is installed correctly:

```python
import edgework
print(edgework.__version__)

# Create a client instance
client = edgework.Edgework()
print("Edgework installed successfully!")
```

## Troubleshooting

### Common Issues

**Import Error**: If you encounter import errors, make sure you have Python 3.11+ installed and that Edgework was installed in the correct environment.

**Network Issues**: Edgework requires internet access to communicate with NHL APIs. If you're behind a corporate firewall, you may need to configure proxy settings.

**Rate Limiting**: The NHL APIs may rate limit requests. Edgework handles this gracefully, but you may need to implement delays between requests for high-volume usage.
