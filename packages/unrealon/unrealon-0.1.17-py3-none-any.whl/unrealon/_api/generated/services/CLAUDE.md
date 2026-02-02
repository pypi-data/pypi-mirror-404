# Unrealon API - Python Client

Auto-generated. **Do not edit manually.**

```bash
python manage.py generate_client --groups services --python
```

## Stats

| | |
|---|---|
| Version | 3.0.3 |
| Operations | 48 |
| Schemas | 46 |

## Resources

- **API Keys** (7 ops)
- **Process Control** (5 ops)
- **Process Jobs** (3 ops)
- **Schedule Events** (2 ops)
- **Schedule Runs** (2 ops)
- **Schedules** (10 ops)
- **Service Commands** (2 ops)
- **Service Control** (2 ops)
- **Service Logs** (2 ops)
- **Service SDK** (5 ops)
- **Services** (6 ops)
- **services** (2 ops)

## Usage

```python
from .client import APIClient

client = APIClient(base_url="...", token="...")

await client.api keys.list()
await client.api keys.retrieve(id=1)
await client.services.retrieve(id=1)
```

## How It Works

```
DRF ViewSets → drf-spectacular → OpenAPI → IR Parser → Generator → This Client
```

**Configuration** (`api/config.py`):
```python
openapi_client = OpenAPIClientConfig(
    enabled=True,
    groups=[OpenAPIGroupConfig(name="services", apps=["..."])],
)
```

@see https://djangocfg.com/docs/features/api-generation

