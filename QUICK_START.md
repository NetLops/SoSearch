# Quick Start

Follow these steps to build and run the `SoSearch` API layer locally.
This project has been set up with a China-based rust mirror (`rsproxy` inside `.cargo/config.toml`) to ensure fast and reliable builds.

## 1. Prerequisites
- [Rust & Cargo](https://rustup.rs/) configured on your environment.
- Port `10080` available locally (or set a custom `PORT` env var).

## 2. Running Locally

Start the Axum server:

```bash
cargo run --release
```

To run it in the background:
```bash
PORT=10080 cargo run --release > server.log 2>&1 &
```

## 3. Running with Docker

```bash
# Build and start (port 11380)
make docker-compose-up

# Stop
make docker-compose-down
```

## 4. Usage Example

Ensure your proxy or local connection is stable, then request a search using `curl`:

```bash
curl -s "http://localhost:10080/search?q=rust+lang" | python3 -m json.tool
```

### Example Output

```json
{
  "query": "rust lang",
  "results": [
    {
      "title": "Rust Programming Language",
      "url": "https://rust-lang.org/",
      "snippet": "Rust is a fast, reliable, and productive programming language...",
      "engine": "duckduckgo"
    }
  ]
}
```

## 5. Using with AI Agents

This project includes built-in agent skills for **Gemini CLI** and compatible tools.

### Gemini CLI

```bash
cd /path/to/SoSearch
gemini
```

Skills are auto-discovered. Try asking:
- *"How do I add a new search engine?"* → uses `sosearch-engine-dev` skill
- *"How do I deploy with Docker?"* → uses `sosearch-api-ops` skill

### Skill Locations

| Path | Tool Compatibility |
|---|---|
| `.gemini/skills/` | Gemini CLI |
| `.agents/skills/` | Generic AI agents (Cursor, Windsurf, etc.) |

Both directories contain the same skills:
- **sosearch-engine-dev** — Scraper development workflow
- **sosearch-api-ops** — API operations & deployment

## 6. Makefile Reference

```
make build              # cargo build --release
make run                # PORT=11380 cargo run --release
make docker-build       # docker build
make docker-compose-up  # docker compose up -d --build
make docker-compose-down # docker compose down
make clean              # cargo clean
```

> **Note**: For heavy scraping requirements against Google and Yandex, consider proxy usage or running a Headless browser backend. The `rquest` crate's TLS impersonation takes you quite far but can still be flagged after bulk usage from datacenter IPs.
