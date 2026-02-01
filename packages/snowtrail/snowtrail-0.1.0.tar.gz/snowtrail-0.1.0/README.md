# Snowtrail Python SDK

Python SDK for the [Snowtrail Research API](https://api.snowtrail.ai) - commodities intelligence for systematic trading.

## Installation

```bash
pip install snowtrail
```

## Quick Start

```python
from snowtrail import Snowtrail

# Initialize the client (uses SNOWTRAIL_API_KEY env var if set)
client = Snowtrail(api_key="your-api-key")

# Get latest GBSI-US system stress signal
df = client.gbsi_us.system_stress()
print(df)

# Get historical data
df = client.gbsi_us.system_stress(
    start="2024-01-01",
    end="2024-12-31",
    limit=500
)
```

## Authentication

Set your API key via environment variable (recommended):

```bash
export SNOWTRAIL_API_KEY="your-api-key"
```

```python
from snowtrail import Snowtrail

# Automatically uses SNOWTRAIL_API_KEY
client = Snowtrail()
df = client.gbsi_us.system_stress()
```

Or pass it directly:

```python
client = Snowtrail(api_key="your-api-key")
```

## Products

| Product | Description | Frequency |
|---------|-------------|-----------|
| `gbsi_us` | US Natural Gas Balance Stress Index | Weekly |
| `gbsi_eu` | EU Natural Gas Balance Stress Index | Daily |
| `pemi` | Power Event Market Intelligence | Daily |
| `glmi` | Global LNG Market Intelligence | Weekly |
| `wrsi` | Weather Risk Signal Intelligence | Daily |
| `wssi_us` | Weather Storage Shock Index | Daily |

## Usage Examples

### GBSI-US (US Natural Gas)

```python
# Signals
df = client.gbsi_us.system_stress()

# Features
df = client.gbsi_us.balance_momentum()
df = client.gbsi_us.storage_inventory()
df = client.gbsi_us.supply_elasticity()
df = client.gbsi_us.features()

# Events
df = client.gbsi_us.storage_surprise()
df = client.gbsi_us.regime_shift()
```

### GBSI-EU (EU Natural Gas)

```python
# Filter by country
df = client.gbsi_eu.system_stress(country="DE")
df = client.gbsi_eu.composite(country="NL")
df = client.gbsi_eu.dispersion()
```

### WRSI (Weather Risk)

```python
# Filter by geography
df = client.wrsi.weather_risk(geography="US")
df = client.wrsi.forecast_dynamics(region_type="state")
```

### Historical Data

All endpoints support date range queries:

```python
# Get history instead of latest
df = client.gbsi_us.system_stress(
    latest=False,
    start="2023-01-01",
    end="2024-01-01",
    limit=1000
)
```

## Error Handling

The SDK automatically retries failed requests (rate limits, server errors) with exponential backoff.

```python
from snowtrail import Snowtrail, AuthenticationError, RateLimitError, NotFoundError, APIError

client = Snowtrail(api_key="your-api-key")

try:
    df = client.gbsi_us.system_stress()
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded after retries")
except NotFoundError:
    print("Endpoint not found")
except APIError as e:
    print(f"API error: {e}")
```

## API Reference

Full API documentation: https://api.snowtrail.ai/docs

Product documentation: https://docs.snowtrail.ai

## Support

- Email: support@snowtrail.ai
- Documentation: https://docs.snowtrail.ai
