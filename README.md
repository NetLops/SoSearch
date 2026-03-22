# SoSearch API

A lightning-fast pseudo Web Search Engine API written in **Rust** — also works as an **MCP server** for AI agents.
This project emulates popular APIs like *SerpAPI* or *Tavily* without needing official and expensive API keys, by multiplexing requests to popular engines directly and scraping the results concurrently.

## Philosophy

- **Performance**: Powered by `tokio` for async concurrent I/O.
- **Bot Bypass**: Leverages `rquest` with TLS impersonation (e.g., simulating a Chrome 124 browser footprint at the TLS/HTTP2 layer) to minimize blocking vs standard HTTP clients (the Rust equivalent of `curl_cffi`).
- **Standardized**: Normalizes `DuckDuckGo`, `Yahoo`, and `Brave` HTML results into a standardized `SearchResult` JSON array.

## Core Stack
- [Axum](https://github.com/tokio-rs/axum)
- [Tokio](https://tokio.rs/)
- [rquest](https://github.com/0x676e67/rquest)
- [scraper](https://github.com/causal-agent/scraper)

## 🔍 Supported Search Engines

*   **DuckDuckGo** (Primary standard search)
*   **Yahoo** (Powered by Bing)
*   **Brave Search** (Independent index)

## 📁 Project Structure

```
src/
├── main.rs              # Entry point: HTTP server or MCP mode (--mcp)
├── search.rs            # Shared concurrent search logic
├── mcp.rs               # MCP stdio server (JSON-RPC 2.0)
├── models.rs            # SearchResultItem, SearchResponse structs
└── engines/
    ├── mod.rs            # SearchEngine enum + trait dispatch
    ├── duckduckgo.rs     # DuckDuckGo scraper
    ├── yahoo.rs          # Yahoo scraper (Bing-powered)
    └── brave.rs          # Brave Search scraper
```

## 🤖 Agent Skills & MCP Support

This project includes built-in AI agent support for both **Gemini CLI** and other tools that follow the `.agents/` convention.

### Available Skills

| Skill | Description |
|---|---|
| `sosearch-engine-dev` | Full workflow for adding/debugging search engine scrapers: fetch HTML → test selectors offline → decode URLs → integrate |
| `sosearch-api-ops` | Operations guide: build, run, test, deploy (local + Docker), troubleshoot |

### MCP Servers

Configured in `.gemini/settings.json`:

| Server | Package | Purpose |
|---|---|---|
| `filesystem` | `@modelcontextprotocol/server-filesystem` | Scoped file access to project directory |

### Usage with Gemini CLI

```bash
cd /path/to/SoSearch
gemini
# Skills are auto-discovered. Ask: "How do I add a new search engine?"
```

## 🔌 MCP Server Mode

Run SoSearch as an MCP server for AI agents (Claude, Gemini, Cursor, etc.):

```bash
./SoSearch --mcp
```

### Configuration

**Claude Desktop** (`claude_desktop_config.json`):
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

**Gemini CLI** (`.gemini/settings.json`):
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

This exposes a `web_search` tool that AI agents can call to search the web.

## 🚀 Quick Start

Refer to `QUICK_START.md` for running instructions.

## 📄 License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — 非商业用途可自由使用、修改和分发。

## 🏠 Community

首发于 [LINUX DO 社区](https://linux.do)，欢迎 Star ⭐ 和 PR！
