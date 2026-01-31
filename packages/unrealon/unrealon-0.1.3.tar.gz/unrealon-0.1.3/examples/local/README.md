# Unrealon SDK - Local Examples

Demo parsers for testing SDK integration with Django backend and CMDOP.

## Quick Start

```bash
# Terminal 1: Start Django server
./start_env.sh

# Terminal 2: Run demo
# Option A: Environment variable
export UNREALON_API_KEY=pk_xxxxx
python demo_simple.py

# Option B: Create config_local.py
echo 'UNREALON_API_KEY = "pk_xxxxx"' > config_local.py
python demo_simple.py
```

## Setup

### 1. Install SDK

```bash
./start_env.sh setup
# or: pip install -e ../..
```

### 2. Start Django Server

```bash
./start_env.sh
# or: cd ../../../../projects/django && make dev
```

### 3. Create API Key

```bash
./start_env.sh api-key  # Show instructions
```

Manual steps:
1. Open http://localhost:8000/admin/
2. Login (create superuser with `make superuser` if needed)
3. Go to Services → API Keys → Add
4. Create key with `can_register=True`, `is_global=True`
5. Copy the generated key (shown only once!)

### 4. Configure API Key

```bash
# Option A: Environment variable
export UNREALON_API_KEY=pk_your_key_here

# Option B: Create config_local.py (gitignored)
echo 'UNREALON_API_KEY = "pk_your_key_here"' > config_local.py
```

## Examples

### demo_simple.py - SDK Only

Tests SDK functionality without CMDOP browser:

```bash
python demo_simple.py
```

- Registers service with Django
- Sends heartbeats
- Logs at different levels
- Simulates processing

### demo_parser.py - Full Integration

SDK + CMDOP browser automation:

```bash
# Requires cmdop_go agent running
python demo_parser.py
```

- Connects to CMDOP (local mode, no API key needed)
- Parses https://quotes.toscrape.com/
- Logs results to Django
- Handles pause/resume/stop commands

## Files

```
examples/local/
├── config.py          # Configuration loader
├── config_local.py    # Your API key (gitignored)
├── demo_simple.py     # SDK-only demo
├── demo_parser.py     # Full SDK+CMDOP demo
├── start_env.sh       # Helper script
└── README.md
```

## Troubleshooting

- **"UNREALON_API_KEY not set"** - Export env var or create config_local.py
- **"Connection refused"** - Django not running on port 8000
- **"Failed to connect to CMDOP"** - cmdop_go not running (use demo_simple.py instead)
- **"401 Unauthorized"** - API key invalid, create new in admin
