use crate::engines::{duckduckgo::DuckDuckGo, brave::Brave, yahoo::Yahoo, SearchEngine};
use crate::models::SearchResultItem;
use futures::stream::{FuturesUnordered, StreamExt};
use rquest::Client;
use tracing::info;

/// Perform a concurrent web search across all engines.
/// Shared by both the HTTP handler and MCP handler.
pub async fn perform_search(query: &str) -> Vec<SearchResultItem> {
    let client = Client::builder()
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        .build()
        .unwrap_or_else(|_| Client::new());

    let engines: Vec<SearchEngine> = vec![
        SearchEngine::DuckDuckGo(DuckDuckGo),
        SearchEngine::Brave(Brave),
        SearchEngine::Yahoo(Yahoo),
    ];

    let mut results = Vec::new();
    let mut tasks = FuturesUnordered::new();

    for engine in engines {
        let q = query.to_string();
        let c = client.clone();
        tasks.push(tokio::spawn(async move {
            let name = engine.name();
            match engine.search(&q, &c).await {
                Ok(items) => {
                    info!("{} returned {} results", name, items.len());
                    items
                }
                Err(e) => {
                    eprintln!("Error searching {}: {}", name, e);
                    vec![]
                }
            }
        }));
    }

    while let Some(res) = tasks.next().await {
        if let Ok(mut items) = res {
            results.append(&mut items);
        }
    }

    results
}
