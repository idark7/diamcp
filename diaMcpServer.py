# Module uses future annotations for forward references and speed
from __future__ import annotations

# Import sys for writing diagnostic messages to stderr
import sys
# Import FastMCP to create the Diabetes Interface Adapter server
from mcp.server.fastmcp import FastMCP
import requests

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
        url = f"https://0d4e.ns.gluroo.com/api/v1/entries.json?count={count}"
        headers = {
            "Accept": "application/json",
            "api-secret": "48d43ce867489ec33269f08bcc777c0ffaf57eca"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        parsed = [{"sgv": entry.get("sgv"), "dateString": entry.get("dateString")} for entry in data]
        return str(parsed)
    except Exception as e:
        return f"Error fetching entries: {e}"


# Only run the server when this file is executed directly
if __name__ == "__main__":
    # Emit a startup line to stderr so host logs show server liveness
    sys.stderr.write("[Dia] starting; waiting for DIA handshake on stdio\n")
    # Ensure the message is flushed immediately
    sys.stderr.flush()
    # Start the DIA server using stdio transport (compatible with DIA clients)
    dia.run(transport="stdio")
