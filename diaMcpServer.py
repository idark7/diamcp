# Module uses future annotations for forward references and speed
from __future__ import annotations

# Import sys for writing diagnostic messages to stderr
import sys
import json
import time
# Import FastMCP to create the Diabetes Interface Adapter server
from mcp.server.fastmcp import FastMCP
import requests

# Gluroo API configuration shared across tools
GLUROO_BASE_URL = "https://0d4e.ns.gluroo.com/api/v1"
GLUCOSE_ENTRIES_URL = f"{GLUROO_BASE_URL}/entries.json"
GLUROO_JSON_HEADERS = {
    "Accept": "application/json",
    "api-secret": "48d43ce867489ec33269f08bcc777c0ffaf57eca",
}

# Create a FastMCP server instance with a name
dia = FastMCP("Dia")


# Register the following function as a DIA tool
@dia.tool()
def getentries(count: int = 1) -> str:
    """Fetch entries from the Gluroo API.

    Parameters
    - count: Number of entries to fetch (default 1)

    The API secret is managed internally for now.
    """
    try:
        url = f"{GLUCOSE_ENTRIES_URL}?count={count}"
        response = requests.get(url, headers=GLUROO_JSON_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        parsed = [{"sgv": entry.get("sgv"), "dateString": entry.get("dateString")} for entry in data]
        return str(parsed)
    except Exception as e:
        return f"Error fetching entries: {e}"


@dia.tool()
def streamentries(
    max_events: int = 5,
    timeout: float = 30.0,
    poll_interval: float = 5.0,
    entries_url: str | None = None,
    per_request: int | None = None,
) -> str:
    """Poll the Gluroo REST API for recent glucose readings.

    Parameters
    - max_events: Maximum number of unique readings to return (<= 0 means unlimited until timeout).
    - timeout: Total number of seconds to poll before giving up.
    - poll_interval: Delay between REST calls while waiting for new readings.
    - entries_url: Optional override for the Gluroo entries endpoint.
    - per_request: Optional override for `count` passed to the REST endpoint.
    """

    limit = max_events if max_events > 0 else None
    if limit is None:
        # reasonable default to avoid massive downloads when unlimited
        per_request = per_request or 25
    else:
        per_request = per_request or max(limit * 2, 1)

    events: list[dict] = []
    seen_ids: set[str] = set()
    url = entries_url or GLUCOSE_ENTRIES_URL
    deadline = time.monotonic() + max(timeout, 0)

    try:
        while time.monotonic() < deadline and (limit is None or len(events) < limit):
            response = requests.get(
                f"{url}?count={per_request}",
                headers=GLUROO_JSON_HEADERS,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                return f"Unexpected response payload: {data!r}"

            new_found = False
            for entry in data:
                entry_id = entry.get("_id")
                if entry_id is None or entry_id in seen_ids:
                    continue
                seen_ids.add(entry_id)
                events.append({
                    "sgv": entry.get("sgv"),
                    "dateString": entry.get("dateString"),
                    "raw": entry,
                })
                new_found = True
                if limit is not None and len(events) >= limit:
                    break

            if limit is not None and len(events) >= limit:
                break

            if not new_found:
                time.sleep(max(poll_interval, 0))
            else:
                # brief pause to avoid hammering the endpoint when data is flowing fast
                time.sleep(max(min(poll_interval, 1.0), 0))
    except Exception as e:
        return f"Error streaming entries via REST polling: {e}"

    return json.dumps(events)


# Only run the server when this file is executed directly
if __name__ == "__main__":
    # Emit a startup line to stderr so host logs show server liveness
    sys.stderr.write("[Dia] starting; waiting for DIA handshake on stdio\n")
    # Ensure the message is flushed immediately
    sys.stderr.flush()
    # Start the DIA server using stdio transport (compatible with DIA clients)
    dia.run(transport="stdio")
