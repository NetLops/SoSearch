# SoSearch Project Instructions

## Overview
SoSearch is a high-performance meta search engine API written in **Rust**. It concurrently queries DuckDuckGo, Yahoo, and Brave Search, scrapes HTML results, and returns a unified JSON response.

## Tech Stack
- **Framework**: Axum (async HTTP server)
- **Runtime**: Tokio (async I/O)
- **HTTP Client**: rquest (TLS impersonation — Chrome fingerprint)
- **HTML Parsing**: scraper (CSS selector-based)
- **Serialization**: serde / serde_json

## Project Structure
```
src/
├── main.rs              # Axum server, /search endpoint, concurrent engine dispatch
├── models.rs            # SearchResultItem, SearchResponse structs
└── engines/
    ├── mod.rs            # SearchEngine enum + trait dispatch
    ├── duckduckgo.rs     # DuckDuckGo scraper
    ├── yahoo.rs          # Yahoo scraper (Bing-powered)
    └── brave.rs          # Brave Search scraper
examples/
├── fetch_html.rs        # Download raw HTML for offline debugging
└── test_parser.rs       # Offline CSS selector iteration
.gemini/skills/          # Gemini CLI agent skills
.agents/skills/          # Generic agent skills (same content, dual discovery)
```

## Conventions
- Use `rquest::Client` with Chrome User-Agent for all HTTP requests
- All engine scrapers follow the same pattern: build URL → fetch HTML → parse with CSS selectors → return `Vec<SearchResultItem>`
- Errors are logged but never crash the server; failed engines return empty results
- Port defaults to `10080`, override via `PORT` env var; Docker uses `11380`
- **Chinese mirrors**: Use `rsproxy` for Cargo (already configured in `.cargo/config.toml`)

## Available Skills
- **sosearch-engine-dev**: Workflow for adding/debugging search engine scrapers
- **sosearch-api-ops**: Running, testing, and deploying the API

## Rules
- **Never kill other projects' processes.** Check `lsof -i :PORT` before binding.
- **Avoid interactive commands.** Use `yes |` for confirmations, background long-running processes.
