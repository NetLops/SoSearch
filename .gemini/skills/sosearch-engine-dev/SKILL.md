---
name: sosearch-engine-dev
description: Workflow for adding or debugging search engine scrapers in the SoSearch project. Covers fetching raw HTML, iterating CSS selectors offline, URL decoding, and integration into production engine modules.
---

# SoSearch Engine Development Skill

> Use this skill when asked to add a new search engine, fix broken selectors, or debug scraper output.

## The Golden Rule

> **Never write CSS selectors by guessing. Always: fetch → inspect → test offline → integrate.**

## Step 1: Fetch Raw HTML

Create or update `examples/fetch_html.rs` to download the target engine's results page:

```rust
// examples/fetch_html.rs
let client = rquest::Client::builder()
    .user_agent("Mozilla/5.0 ... Chrome/124.0.0.0 ...")
    .build()?;

let url = "https://engine.com/search?q=rust+lang";
let html = client.get(url).send().await?.text().await?;
std::fs::write("engine_out.html", &html)?;
println!("Fetched {} bytes", html.len());
```

Run: `cargo run --example fetch_html`

### Quick Diagnosis

| Symptom | Cause | Action |
|---|---|---|
| HTML < 5KB | CAPTCHA/JS challenge | Try different UA or switch engine |
| HTML > 50KB, no results parsed | Wrong selectors | Go to Step 2 |
| 403 Forbidden | Bot detection | Use `rquest` impersonation |
| Connection error | Geo-block/DNS | Use proxy or VPN |

## Step 2: Offline Selector Testing

Create or update `examples/test_parser.rs`:

```rust
// examples/test_parser.rs
let html = std::fs::read_to_string("engine_out.html").unwrap();
let doc = scraper::Html::parse_document(&html);

let container = scraper::Selector::parse(".result-container").unwrap();
let title_sel = scraper::Selector::parse("h3").unwrap();
let link_sel = scraper::Selector::parse("a[href]").unwrap();
let snippet_sel = scraper::Selector::parse(".description").unwrap();

for el in doc.select(&container).take(5) {
    let title = el.select(&title_sel).next()
        .map(|t| t.text().collect::<String>()).unwrap_or_default();
    let url = el.select(&link_sel).next()
        .and_then(|a| a.value().attr("href")).unwrap_or("");
    let snippet = el.select(&snippet_sel).next()
        .map(|s| s.text().collect::<String>()).unwrap_or_default();
    println!("Title: {title}\nURL: {url}\nSnippet: {snippet}\n");
}
```

Run: `cargo run --example test_parser`

### Selector Reference

| Engine | Container | Title | URL | Snippet |
|---|---|---|---|---|
| DuckDuckGo | `.result` | `.result__a` | `.result__a[href]` | `.result__snippet` |
| Yahoo | `.algo` | `h3` | `.compTitle a` | `.compText` |
| Brave | `.snippet` | `.title` | `a` | `.snippet-description` |

## Step 3: URL Decoding

Many engines wrap URLs in redirects. Decode before returning:

- **Yahoo**: Extract between `RU=` and `/RK=`, then `urlencoding::decode()`
- **DuckDuckGo**: Extract after `uddg=`, split on `&`, decode
- **Brave**: Usually clean URLs, just filter out internal links starting with `/`

## Step 4: Integration

Copy verified selectors into `src/engines/<engine>.rs` following the standard pattern:

```rust
pub struct NewEngine;

impl NewEngine {
    pub fn name(&self) -> &'static str { "NewEngine" }

    pub async fn search(&self, query: &str, client: &rquest::Client)
        -> Result<Vec<crate::models::SearchResultItem>, Box<dyn std::error::Error + Send + Sync>>
    {
        let url = format!("https://engine.com/search?q={}", urlencoding::encode(query));
        let html = client.get(&url).send().await?.text().await?;
        let doc = scraper::Html::parse_document(&html);
        // ... paste verified selectors ...
        Ok(results)
    }
}
```

Then register it in `src/engines/mod.rs` (add to the `SearchEngine` enum and dispatch).

## Step 5: E2E Verification

```bash
PORT=10080 cargo run --release > /tmp/sosearch.log 2>&1 &
sleep 3
curl -s "http://localhost:10080/search?q=test" | python3 -m json.tool
```

Check that the new engine appears in results with valid titles, URLs, and snippets.
