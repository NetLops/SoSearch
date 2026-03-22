# Quick Start

Follow these steps to build and run the `SoSearch` API layer locally.
This project has been set up with a China-based rust mirror (`rsproxy` inside `.cargo/config.toml`) to ensure fast and reliable builds.

## 0. Download Pre-built Binaries (Recommended)

Pre-built binaries for all major platforms are available on [GitHub Releases](https://github.com/netlops/SoSearch/releases).

| Platform | Architecture | File |
|---|---|---|
| Linux | x86_64 | `SoSearch-linux-amd64.tar.gz` |
| Linux | aarch64 | `SoSearch-linux-arm64.tar.gz` |
| macOS | Intel | `SoSearch-macos-amd64.tar.gz` |
| macOS | Apple Silicon | `SoSearch-macos-arm64.tar.gz` |
| Windows | x86_64 | `SoSearch-windows-amd64.zip` |
| Windows | aarch64 | `SoSearch-windows-arm64.zip` |

**Quick install (Linux/macOS):**

```bash
# Example: download latest for Linux amd64
curl -LO https://github.com/netlops/SoSearch/releases/latest/download/SoSearch-linux-amd64.tar.gz
tar xzf SoSearch-linux-amd64.tar.gz
chmod +x SoSearch
./SoSearch
```

**Windows:**

Download the `.zip` from Releases, extract, then run `SoSearch.exe`.

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

## 7. CI/CD Auto Release

This project uses GitHub Actions to automatically build multi-platform binaries and publish GitHub Releases.

### How to Publish a Release

```bash
# 1. Tag a version
git tag v0.1.0

# 2. Push the tag — CI/CD kicks off automatically
git push origin v0.1.0
```

This triggers the workflow at `.github/workflows/release.yml`, which:

1. **Builds 6 targets in parallel** (Linux/macOS/Windows × amd64/arm64)
2. **Packages** binaries into `.tar.gz` (Unix) or `.zip` (Windows)
3. **Creates a GitHub Release** with auto-generated release notes and all binaries attached

### Supported Targets

| Target | Runner | Build Method |
|---|---|---|
| `x86_64-unknown-linux-gnu` | Ubuntu | Native |
| `aarch64-unknown-linux-gnu` | Ubuntu | `cross` (Docker) |
| `x86_64-apple-darwin` | macOS 13 (Intel) | Native |
| `aarch64-apple-darwin` | macOS latest (M1) | Native |
| `x86_64-pc-windows-msvc` | Windows | Native |
| `aarch64-pc-windows-msvc` | Windows | Cross-compile |

### Pre-release Tags

Tags containing `alpha` or `beta` (e.g., `v0.2.0-beta`) are automatically marked as pre-release.

## 8. MCP Server Mode

SoSearch can run as an **MCP (Model Context Protocol) server**, allowing AI agents to use it as a search tool directly.

```bash
./SoSearch --mcp
```

### Configure in Your AI Tool

**Claude Desktop** — add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "sosearch": {
      "command": "/path/to/SoSearch",
      "args": ["--mcp"]
    }
  }
}
```

**Gemini CLI / Cursor / Windsurf** — add to `.gemini/settings.json` or equivalent:
```json
{
  "mcpServers": {
    "sosearch": {
      "command": "/path/to/SoSearch",
      "args": ["--mcp"]
    }
  }
}
```

### Test MCP Handshake

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | ./SoSearch --mcp
```

Expected response:
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"sosearch","version":"0.1.0"}}}
```

### Available Tools

| Tool | Description | Arguments |
|---|---|---|
| `web_search` | Concurrent multi-engine web search | `query` (string) |
