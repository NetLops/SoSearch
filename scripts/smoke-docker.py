"""Check HTTP/MCP behavior; optionally require real, nonempty search results."""

import argparse
import collections
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


# These requests always target the local service, even on hosts with a proxy.
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def http_error(url, expected, method="GET"):
    try:
        with HTTP.open(urllib.request.Request(url, method=method), timeout=2):
            raise AssertionError(f"Expected HTTP {expected}, received success")
    except urllib.error.HTTPError as error:
        require(error.code == expected, f"Expected HTTP {expected}, received {error.code}")
    return {"status": expected}


def wait_for_http(base_url):
    deadline = time.monotonic() + 30
    while True:
        try:
            return http_error(base_url + "/search", 400)
        except (urllib.error.URLError, TimeoutError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)


def rpc_call(command, requests, timeout=30, malformed_prefix=False):
    payload = "not-json\n" if malformed_prefix else ""
    payload += "".join(json.dumps(request, ensure_ascii=False) + "\n" for request in requests)
    process = subprocess.run(
        command, input=payload, capture_output=True, text=True, timeout=timeout, check=True
    )
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    expected_ids = [request["id"] for request in requests if "id" in request]
    require([response.get("id") for response in responses] == expected_ids, process.stdout)
    require(all(response.get("jsonrpc") == "2.0" for response in responses), process.stdout)
    return responses


def check_protocol(command):
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "ping"},
        {"jsonrpc": "2.0", "id": 4, "method": "unknown"},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call"},
        {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "unknown"}},
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "web_search", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "web_search", "arguments": {"query": 42}}},
    ]
    responses = rpc_call(command, requests, malformed_prefix=True)
    require(responses[0]["result"]["serverInfo"]["name"] == "sosearch", "Wrong server name")
    require(responses[0]["result"]["capabilities"] == {"tools": {}}, "Wrong capabilities")
    tool = responses[1]["result"]["tools"][0]
    require(tool["name"] == "web_search", "Missing search tool")
    require(tool["inputSchema"]["required"] == ["query"], "Wrong input schema")
    require(responses[2]["result"] == {}, "Ping failed")
    for response, code in zip(responses[3:], [-32601, -32602, -32602, -32602, -32602]):
        require(response["error"]["code"] == code, f"Wrong RPC error: {response}")
    return {"responses": 8, "notification_silent": True, "recovers_from_invalid_json": True}


def validate_results(results, live):
    require(isinstance(results, list), "Search results must be an array")
    if live:
        require(len(results) > 0, "No search results: inspect upstream errors and container logs")
    else:
        require(results == [], "Offline proxy must yield an empty result list")
    for item in results:
        require(isinstance(item, dict), "Result must be an object")
        require(all(isinstance(item.get(key), str) for key in ["title", "url", "snippet", "engine"]), "Invalid result fields")
        require(bool(item["title"].strip()), "Empty result title")
        url = urllib.parse.urlsplit(item["url"])
        require(url.scheme in {"http", "https"} and bool(url.netloc), f"Invalid result URL: {item['url']}")
        require(item["engine"].lower() in {"duckduckgo", "brave", "yahoo"}, "Unknown engine")
    return {
        "result_count": len(results),
        "engines": dict(collections.Counter(item["engine"] for item in results)),
        "sample_urls": [item["url"] for item in results[:3]],
    }


def check_http_search(base_url, query, live):
    url = base_url + "/search?" + urllib.parse.urlencode({"q": query})
    with HTTP.open(url, timeout=60) as response:
        require(response.status == 200, "Search request failed")
        require(response.headers.get_content_type() == "application/json", "Expected JSON")
        payload = json.load(response)
    require(payload["query"] == query, "Query changed during URL decoding")
    return validate_results(payload["results"], live)


def check_mcp_search(command, query, live):
    responses = rpc_call(command, [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "web_search", "arguments": {"query": query}}},
    ], timeout=75)
    content = responses[1]["result"]["content"]
    require(len(content) == 1 and content[0]["type"] == "text", "Wrong MCP search content")
    return validate_results(json.loads(content[0]["text"]), live)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--offline-search", action="store_true", help="Expect empty searches with the CI proxy override")
    mode.add_argument("--live-search", action="store_true", help="Require valid, nonempty HTTP and MCP search results")
    parser.add_argument("--query", default="rust programming language")
    parser.add_argument("--report", default="artifacts/availability.json")
    parser.add_argument("--binary", help="Use a local binary for MCP instead of Docker Compose")
    args = parser.parse_args()
    base_url = f"http://127.0.0.1:{os.environ.get('PORT', '11380')}"
    command = [str(Path(args.binary).resolve()), "--mcp"] if args.binary else [
        "docker", "compose", "run", "--rm", "--no-deps", "-T", "sosearch", "./SoSearch", "--mcp"
    ]
    checks = []

    def run(name, operation):
        started = time.monotonic()
        check = {"name": name}
        try:
            check.update(status="passed", details=operation())
        except Exception as error:
            check.update(status="failed", error=f"{type(error).__name__}: {error}")
            if isinstance(error, subprocess.CalledProcessError):
                check["stderr"] = error.stderr
        check["duration_seconds"] = round(time.monotonic() - started, 3)
        checks.append(check)
        print(json.dumps(check, ensure_ascii=False), flush=True)

    run("http_missing_query", lambda: wait_for_http(base_url))
    run("http_unknown_route", lambda: http_error(base_url + "/not-found", 404))
    run("http_unsupported_method", lambda: http_error(base_url + "/search?q=test", 405, "POST"))
    run("mcp_protocol_and_errors", lambda: check_protocol(command))
    if args.offline_search or args.live_search:
        query = args.query if args.live_search else "Rust + 中文 & query=100%"
        run("http_search", lambda: check_http_search(base_url, query, args.live_search))
        run("mcp_web_search", lambda: check_mcp_search(command, query, args.live_search))
    report = {
        "mode": "live" if args.live_search else "offline" if args.offline_search else "protocol",
        "commit": os.environ.get("GITHUB_SHA"),
        "checks": checks,
        "passed": sum(check["status"] == "passed" for check in checks),
        "failed": sum(check["status"] == "failed" for check in checks),
    }
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(f"### {report['mode']} availability\n\n| Check | Status |\n| --- | --- |\n")
            for check in checks:
                summary.write(f"| {check['name']} | {check['status']} |\n")
            summary.write(f"\nPassed: {report['passed']}; failed: {report['failed']}.\n")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
