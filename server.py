"""
server.py - the CGPA Guider's MCP server.

FastMCP turns each plain Python function from tools.py into an MCP tool:
its name, type hints and docstring become the description that any MCP
client (our LangChain agent, or anyone else's agent in any language)
gets back from `tools/list`, and the function runs on `tools/call`.

Test it on its own (no agent, no LLM, no API key):
    fastmcp list server.py
    fastmcp call server.py get_credit_hours semesters='[5,6]'     # -> 37.0

Run it as a network server:
    python server.py            # serves http://127.0.0.1:8000/mcp
"""

import os

from fastmcp import FastMCP

from tools import ALL_TOOLS

mcp = FastMCP("cgpa")

# Share every tool, the same way the starter shared get_credit_hours:
#     mcp.tool(get_credit_hours)
for fn in ALL_TOOLS:
    mcp.tool(fn)


if __name__ == "__main__":
    # Locally: 127.0.0.1:8000. On a host such as Render, the platform sets
    # PORT and we must listen on 0.0.0.0 so outside traffic can reach us.
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)
