# Unrealon SDK Examples

Examples demonstrating SDK usage with gRPC.

## Prerequisites

1. Start Django + gRPC server:
```bash
cd solution/projects/django
make dev   # Django on :8000
make grpc  # gRPC on :50051 (in another terminal)
```

2. Create API key in Django admin:
   - Go to http://localhost:8000/admin/
   - Services > API Keys > Add
   - Copy the generated key

3. Export API key:
```bash
export UNREALON_API_KEY=pk_xxxxx
```

## Examples

### Simple Demo (sync)
```bash
python demo_simple.py --dev
```

### Async Demo
```bash
python demo_async.py --dev
```

## Options

- `--dev` - Use local gRPC server (localhost:50051)
- `--api-key KEY` - API key (alternative to env var)
- `--grpc-server HOST:PORT` - Custom gRPC server
