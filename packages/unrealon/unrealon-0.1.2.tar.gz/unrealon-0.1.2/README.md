# Unrealon SDK

Parser management SDK for Unrealon platform. Provides registration, heartbeat, logging, and command handling.

## Installation

```bash
pip install unrealon
```

## Quick Start

```python
from unrealon import ParserClient

# Using context manager (recommended)
with ParserClient(
    api_key="pk_live_xxx",
    parser_name="my-parser",
) as client:
    client.info("Processing started")

    for item in items:
        process(item)
        client.increment_processed()

    client.info("Processing complete")
```

## Configuration

Configuration via environment variables (recommended):

```bash
export UNREALON_API_KEY=pk_live_xxx
export UNREALON_PARSER_NAME=my-parser
export UNREALON_API_URL=https://api.unrealon.com  # optional
```

Or pass directly to client:

```python
client = ParserClient(
    api_key="pk_live_xxx",
    parser_name="my-parser",
    api_url="https://api.unrealon.com",
    source_code="encar",
    heartbeat_interval=30,
)
```

### Available Settings

| Env Variable | Default | Description |
|-------------|---------|-------------|
| `UNREALON_API_KEY` | required | API key |
| `UNREALON_PARSER_NAME` | required | Parser identifier |
| `UNREALON_API_URL` | `http://127.0.0.1:8000` | API endpoint |
| `UNREALON_HEARTBEAT_INTERVAL` | `30` | Heartbeat interval (seconds) |
| `UNREALON_LOG_BATCH_SIZE` | `100` | Max logs per batch |
| `UNREALON_LOG_FLUSH_INTERVAL` | `5.0` | Log flush interval (seconds) |
| `UNREALON_COMMAND_POLL_INTERVAL` | `10` | Command poll interval (seconds) |
| `UNREALON_TIMEOUT` | `30.0` | HTTP timeout (seconds) |

## Features

### Registration & Lifecycle

```python
# Manual control
client = ParserClient(api_key="...", parser_name="...")
parser_id = client.start(description="Production parser")
# ... work ...
client.stop()

# Context manager
with ParserClient(...) as client:
    # Auto-registered, auto-deregistered
    pass
```

### Heartbeat

Heartbeats are sent automatically in background. Update status as needed:

```python
with ParserClient(...) as client:
    # Update metrics
    client.update_status(
        items_processed=1000,
        errors_count=5,
    )

    # Or use convenience methods
    client.increment_processed(100)
    client.increment_errors(1)
```

### Logging

Logs are batched and sent automatically:

```python
with ParserClient(...) as client:
    client.debug("Debug message")
    client.info("Info message")
    client.warning("Warning message")
    client.error("Error message", exception=e)
    client.critical("Critical error")
```

### Commands

Handle commands from server:

```python
def handle_restart(cmd):
    print(f"Restart requested: {cmd.params}")
    return {"status": "restarted"}

client = ParserClient(...)
client.on_command("restart", handle_restart)
client.on_command("stop", lambda cmd: sys.exit(0))

with client:
    # Commands are automatically polled and executed
    while True:
        process_items()
```

## Async Support

```python
from unrealon import AsyncParserClient

async with AsyncParserClient(
    api_key="...",
    parser_name="...",
) as client:
    await client.send_heartbeat(items_processed=100)
    await client.log.log(client.parser_id, "info", "Message")
```

## Individual Services

Use services directly for more control:

```python
from unrealon import (
    UnrealonConfig,
    RegistrarService,
    HeartbeatService,
    LoggerService,
    CommandService,
)

config = UnrealonConfig(api_key="...", parser_name="...")

# Registration
registrar = RegistrarService(config)
response = registrar.register()
parser_id = response.parser_id

# Heartbeat
heartbeat = HeartbeatService(config)
heartbeat.start_background(parser_id)

# Logging
logger_svc = LoggerService(config)
logger_svc.start_batching(parser_id)
logger_svc.info("Message")
logger_svc.flush()

# Commands
commands = CommandService(config)
pending = commands.poll(parser_id)
for cmd in pending:
    commands.acknowledge(cmd.id, "completed")
```

## Error Handling

```python
from unrealon import (
    UnrealonError,
    AuthenticationError,
    RegistrationError,
    NetworkError,
)

try:
    with ParserClient(...) as client:
        pass
except AuthenticationError as e:
    print(f"Invalid API key: {e}")
except RegistrationError as e:
    print(f"Registration failed: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except UnrealonError as e:
    print(f"SDK error: {e}")
```

## Parser Status

```python
from unrealon import ParserClient, ParserStatus

with ParserClient(...) as client:
    client.update_status(status=ParserStatus.RUNNING)

    # Available statuses:
    # ParserStatus.INITIALIZING
    # ParserStatus.RUNNING
    # ParserStatus.PAUSED
    # ParserStatus.STOPPING
    # ParserStatus.STOPPED
    # ParserStatus.ERROR
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/unrealon

# Linting
ruff check src/unrealon
```

## License

MIT
