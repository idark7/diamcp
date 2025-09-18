## Python MCP Server: Adder

This repo contains a minimal Model Context Protocol (MCP) server implemented in Python that exposes a single tool `add(a, b)` which returns the sum of two numbers.

### Install

Use any Python 3.9+ environment.

```
pip install -r requirements.txt
```

### Run (standalone)

This server speaks MCP over stdio and is intended to be launched by an MCP-compatible client. You can still start it manually to verify it launches:

```
python diaMcpServer.py
```

It will wait for an MCP client handshake over stdio.

### Configure in an MCP client

Add an entry to your MCP client configuration that launches this script. Example for a generic client configuration:

```
{
  "mcpServers": {
    "python-adder": {
      "command": "python",
      "args": ["/absolute/path/to/diaMcpServer.py"]
    }
  }
}
```

Once loaded, the client should discover a tool named `add` with parameters `a` and `b` (floats) and return the numeric sum.
