use crate::search::perform_search;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};

// ── JSON-RPC types ──────────────────────────────────────────────

#[derive(Deserialize)]
struct JsonRpcRequest {
    #[allow(dead_code)]
    jsonrpc: String,
    id: Option<Value>,
    method: String,
    params: Option<Value>,
}

#[derive(Serialize)]
struct JsonRpcResponse {
    jsonrpc: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    id: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<Value>,
}

// ── MCP Server Entry Point ──────────────────────────────────────

pub async fn run() {
    let stdin = tokio::io::stdin();
    let mut stdout = tokio::io::stdout();
    let mut reader = BufReader::new(stdin);
    let mut line = String::new();

    loop {
        line.clear();
        match reader.read_line(&mut line).await {
            Ok(0) => break, // EOF
            Ok(_) => {}
            Err(_) => break,
        }

        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        let request: JsonRpcRequest = match serde_json::from_str(trimmed) {
            Ok(r) => r,
            Err(e) => {
                eprintln!("[mcp] failed to parse request: {}", e);
                continue;
            }
        };

        if let Some(response) = handle_request(request).await {
            let json = serde_json::to_string(&response).unwrap();
            let _ = stdout.write_all(json.as_bytes()).await;
            let _ = stdout.write_all(b"\n").await;
            let _ = stdout.flush().await;
        }
    }
}

// ── Request Dispatcher ──────────────────────────────────────────

async fn handle_request(req: JsonRpcRequest) -> Option<JsonRpcResponse> {
    // Notifications (no id) → no response
    if req.id.is_none() {
        return None;
    }
    let id = req.id;

    let result = match req.method.as_str() {
        "initialize" => handle_initialize(),
        "ping" => Ok(json!({})),
        "tools/list" => handle_tools_list(),
        "tools/call" => handle_tools_call(req.params).await,
        other => Err(json!({
            "code": -32601,
            "message": format!("Method not found: {}", other)
        })),
    };

    Some(match result {
        Ok(r) => JsonRpcResponse {
            jsonrpc: "2.0".to_string(),
            id,
            result: Some(r),
            error: None,
        },
        Err(e) => JsonRpcResponse {
            jsonrpc: "2.0".to_string(),
            id,
            result: None,
            error: Some(e),
        },
    })
}

// ── MCP Method Handlers ─────────────────────────────────────────

fn handle_initialize() -> Result<Value, Value> {
    Ok(json!({
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "sosearch",
            "version": env!("CARGO_PKG_VERSION")
        }
    }))
}

fn handle_tools_list() -> Result<Value, Value> {
    Ok(json!({
        "tools": [
            {
                "name": "web_search",
                "description": "Search the web using multiple search engines (DuckDuckGo, Brave, Yahoo) concurrently and return aggregated results.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query string"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    }))
}

async fn handle_tools_call(params: Option<Value>) -> Result<Value, Value> {
    let params = params.ok_or_else(|| json!({
        "code": -32602,
        "message": "Missing params"
    }))?;

    let tool_name = params["name"]
        .as_str()
        .ok_or_else(|| json!({"code": -32602, "message": "Missing tool name"}))?;

    match tool_name {
        "web_search" => {
            let query = params["arguments"]["query"]
                .as_str()
                .ok_or_else(|| json!({"code": -32602, "message": "Missing 'query' argument"}))?;

            let results = perform_search(query).await;
            let text = serde_json::to_string_pretty(&results).unwrap_or_default();

            Ok(json!({
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }))
        }
        _ => Err(json!({
            "code": -32602,
            "message": format!("Unknown tool: {}", tool_name)
        })),
    }
}
