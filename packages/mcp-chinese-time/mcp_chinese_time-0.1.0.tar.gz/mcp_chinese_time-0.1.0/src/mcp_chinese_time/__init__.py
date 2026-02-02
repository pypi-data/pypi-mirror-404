# -*- coding: utf-8 -*-
"""
MCP Chinese Time - A Model Context Protocol server for parsing Chinese fuzzy time expressions.

This package provides an MCP server that can parse natural language time expressions
in Chinese to standard datetime formats.

Example usage:
    # As MCP server
    python -m mcp_chinese_time

    # Or use the parser directly
    from mcp_chinese_time import FuzzyTimeParser

    parser = FuzzyTimeParser()
    result = parser.parse("昨天")
    print(result.value)  # "2024-01-14"
"""

from .parser import FuzzyTimeParser, ParsedTime, ParseTimeOutput
from .server import mcp

__version__ = "0.1.0"
__all__ = [
    "FuzzyTimeParser",
    "ParsedTime",
    "ParseTimeOutput",
    "mcp",
    "main",
]


def main():
    """Entry point for the MCP server."""
    mcp.run()
