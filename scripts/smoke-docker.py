"""Validate the built container without depending on public search engines."""

import json
import os
import subprocess
import time
import urllib.error
import urllib.request


port = os.environ.get("PORT", "11380")
url = f"http://127.0.0.1:{port}/search"
deadline = time.monotonic() + 30
while True:
    try:
        with urllib.request.urlopen(url, timeout=2):
            raise AssertionError("HTTP must reject a missing query")
    except urllib.error.HTTPError as error:
        assert error.code == 400, f"Unexpected HTTP status: {error.code}"
        break
    except (urllib.error.URLError, TimeoutError):
        if time.monotonic() >= deadline:
            raise
        time.sleep(1)
print("HTTP: service started and rejects missing query with 400")

requests = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 3, "method": "ping"},
]
process = subprocess.run(
    ["docker", "compose", "run", "--rm", "--no-deps", "-T", "sosearch", "./SoSearch", "--mcp"],
    input="".join(json.dumps(request) + "\n" for request in requests),
    capture_output=True,
    text=True,
    timeout=30,
    check=True,
)
responses = [json.loads(line) for line in process.stdout.splitlines()]
assert len(responses) == 3, process.stdout
assert [response["id"] for response in responses] == [1, 2, 3]
assert all(response["jsonrpc"] == "2.0" for response in responses)
assert responses[0]["result"]["serverInfo"]["name"] == "sosearch"
assert responses[0]["result"]["capabilities"] == {"tools": {}}
tool = responses[1]["result"]["tools"][0]
assert tool["name"] == "web_search"
assert tool["inputSchema"]["required"] == ["query"]
assert responses[2]["result"] == {}
print("MCP: initialize, tool discovery and ping passed")
