# -*- coding: utf-8 -*-
"""
Entry point for running the MCP server directly.

Usage:
    python -m mcp_chinese_time
"""

from .server import mcp

if __name__ == "__main__":
    mcp.run()
