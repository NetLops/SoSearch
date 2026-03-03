---
name: sosearch-api-ops
description: Operations skill for building, running, testing, and deploying the SoSearch API. Covers local dev, Docker, troubleshooting, and API testing patterns.
---

# SoSearch API Operations Skill

> Use this skill when asked to run, test, deploy, or troubleshoot the SoSearch API.

## Build & Run

### Local Development

```bash
# Build release binary
cargo build --release

# Run (foreground)
PORT=10080 cargo run --release

# Run (background, non-blocking)
PORT=10080 cargo run --release > /tmp/sosearch.log 2>&1 &
```

### Docker

```bash
# Build + start via Docker Compose (port 11380)
make docker-compose-up

# Or manually
docker build -t sosearch:latest .
docker run -d -p 11380:11380 -e PORT=11380 --name sosearch-api sosearch:latest

# Stop
make docker-compose-down
```

## Port Management

> **CRITICAL**: Always check port availability before starting.

```bash
# Check if port is in use
lsof -i :10080

# If occupied, use a different port — NEVER kill the occupying process
PORT=10081 cargo run --release
```

Default ports:
- **Local dev**: `10080`
- **Docker**: `11380`

## API Testing

### Basic Search

```bash
curl -s "http://localhost:10080/search?q=rust+lang" | python3 -m json.tool
```

### Expected Response

```json
{
    "query": "rust lang",
    "results": [
        {
            "title": "Rust Programming Language",
            "url": "https://rust-lang.org/",
            "snippet": "Rust is a fast, reliable...",
            "engine": "duckduckgo"
        }
    ]
}
```

### Batch Test Script

```bash
for q in "rust lang" "python tutorials" "linux kernel"; do
  echo "=== Query: $q ==="
  curl -s "http://localhost:10080/search?q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$q'))")" \
    | python3 -c "import sys,json; r=json.load(sys.stdin); print(f'{len(r[\"results\"])} results from engines: {set(x[\"engine\"] for x in r[\"results\"])}')"
  echo
done
```

## Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| 0 results from all engines | Network/proxy issue | Check internet connectivity, try `curl https://duckduckgo.com` |
| 0 results from one engine | Engine blocking or selector broken | Re-run `fetch_html` example, check HTML for CAPTCHA |
| Connection refused on port | Server not running | Check `lsof -i :PORT`, restart server |
| Build fails | Missing deps or broken lock | Run `cargo clean && cargo build --release` |
| Docker build fails | Cache stale | `docker build --no-cache -t sosearch:latest .` |
| Slow responses | First request, cold TLS handshake | Normal; subsequent requests are faster |

## Makefile Reference

```
make build              # cargo build --release
make run                # PORT=11380 cargo run --release
make docker-build       # docker build
make docker-compose-up  # docker compose up -d --build
make docker-compose-down # docker compose down
make clean              # cargo clean
```
