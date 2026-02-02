"""Git MCP Server Package.

Provides MCP tools for local git operations via FastMCP server.
"""

from mcp.server.fastmcp import FastMCP

__version__ = "0.1.5"

# Create single global MCP server instance
# This MUST be at package level to avoid double-instantiation when module is run as __main__
mcp = FastMCP("git-manager")

__all__ = ["mcp", "__version__"]
