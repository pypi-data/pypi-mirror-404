"""Git MCP Server - Main entry point.

FastMCP server that provides git operation tools to Claude Code via MCP protocol.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Import the singleton mcp instance from package level
from . import mcp

# Load environment variables from project root .env file
# This file is at: git-mcp-server/src/git_mcp_server/server.py
# Project root is 3 levels up
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path, override=True)

# Configure logging to stderr (MCP protocol uses stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Validate GITHUB_TOKEN is available
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    logger.error("GITHUB_TOKEN not found in environment!")
    logger.error(f"Searched for .env at: {env_path}")
    logger.error("GitHub API operations will fail without authentication.")
else:
    logger.info(f"GITHUB_TOKEN loaded successfully from {env_path}")

# Import tool modules to register tools
# Tools are registered via @mcp.tool() decorators in each module
try:
    from .tools import branch, commit, remote, status, sync  # noqa: F401

    logger.info("All tool modules loaded successfully")
except ImportError as e:
    logger.error(f"Failed to import tool modules: {e}")
    raise


def main() -> None:
    """Run the MCP server.

    Starts the FastMCP server which listens on stdio for MCP protocol messages.
    Claude Code will communicate with this server to invoke git operations.
    """
    logger.info("Git MCP Server starting...")

    # Verify tools are registered before starting server
    try:
        tools = mcp._tool_manager.list_tools()
        tool_count = len(tools)
        logger.info(f"Registered {tool_count} tools: {', '.join(t.name for t in tools)}")

        if tool_count == 0:
            logger.error("CRITICAL: No tools registered before server start!")
            logger.error("Check that tool modules are importing correctly")
            raise RuntimeError("Tool registration failed - cannot start server")

        logger.info(f"Server ready with {tool_count} tools")
    except Exception as e:
        logger.error(f"Tool verification failed: {e}", exc_info=True)
        raise

    logger.info("Server name: git-manager")
    logger.info("Listening on stdio for MCP protocol messages")

    try:
        # Run the MCP server (blocks until terminated)
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
