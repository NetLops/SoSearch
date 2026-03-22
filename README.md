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
examples/
├── fetch_html.rs        # Download raw HTML for offline debugging
└── test_parser.rs       # Offline CSS selector iteration
.gemini/                 # Gemini CLI agent config
├── GEMINI.md            # Project-level system prompt
├── settings.json        # MCP server configuration
└── skills/              # Project-level agent skills
    ├── sosearch-engine-dev/  # Scraper development workflow
    └── sosearch-api-ops/     # API operations & deployment
.agents/                 # Generic agent config (compatible with multiple AI tools)
└── skills/              # Same skills, alternative discovery path
    ├── sosearch-engine-dev/
    └── sosearch-api-ops/
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

### Windows Configuration

**Claude Desktop** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "sosearch": {
      "command": "C:\\path\\to\\SoSearch.exe",
      "args": ["--mcp"]
    }
  }
}
```

## 🚀 Quick Start

### Linux / macOS

```bash
# Download pre-built binary or build from source
cargo run --release
curl "http://localhost:10080/search?q=hello+world"
```

### Windows

**使用预编译二进制：**

从 [GitHub Releases](https://github.com/netlops/SoSearch/releases) 下载 `SoSearch-windows-amd64.zip`，解压后：

```powershell
# 启动 HTTP 服务
.\SoSearch.exe

# 另开一个终端测试
Invoke-RestMethod "http://localhost:10080/search?q=hello+world" | ConvertTo-Json

# 或使用 curl
curl.exe "http://localhost:10080/search?q=hello+world"
```

**从源码编译（需要安装 [Rust](https://rustup.rs/)、CMake、NASM、LLVM/Clang）：**

```powershell
# 安装依赖 (使用 Chocolatey)
choco install cmake nasm llvm -y

# 编译运行
cargo run --release
```

**MCP 模式：**

```powershell
.\SoSearch.exe --mcp
```

Refer to `QUICK_START.md` for full instructions.

## 📄 License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — 非商业用途可自由使用、修改和分发。

## 🏠 Community

首发于 [LINUX DO 社区](https://linux.do)，欢迎 Star ⭐ 和 PR！
