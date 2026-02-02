# -*- coding: utf-8 -*-
"""
MCP Server - FastMCP server definition for Chinese time parsing.

This module defines the MCP server and its tools using FastMCP 2.x.
"""

from fastmcp import FastMCP

from .parser import FuzzyTimeParser, ParseTimeOutput

mcp = FastMCP(
    name="mcp-chinese-time",
    instructions="中文模糊时间表达式解析 MCP 服务器 (Chinese Fuzzy Time Expression Parser)",
)


async def _parse_time_handler(expression: str, timezone: str = "Asia/Shanghai") -> dict:
    """
    Core handler for parsing fuzzy time expressions.

    This is separated from the MCP tool decorator to allow direct testing.
    """
    try:
        parser = FuzzyTimeParser(timezone=timezone)
        result = parser.parse(expression)

        output = ParseTimeOutput(success=True, parsed=result)
        return output.model_dump()
    except Exception as e:
        output = ParseTimeOutput(success=False, error=str(e))
        return output.model_dump()


@mcp.tool
async def parse_time(expression: str, timezone: str = "Asia/Shanghai") -> dict:
    """
    解析模糊时间表达式为标准日期时间格式。

    Parse fuzzy Chinese time expressions to standard datetime format.

    Supported expressions:
    - Relative time: 昨天, 今天, 明天, 三天前, 两周后
    - Time ranges: 昨天到今天, 上周一到周五
    - Time of day: 上午9点, 下午3点30分
    - Holidays: 国庆节期间, 春节, 中秋节 (including lunar calendar)
    - Specific dates: 2024年1月1日, 1月15号

    Args:
        expression: Fuzzy time expression in Chinese
                   (e.g., "昨天", "三周前", "国庆节期间", "上午9点")
        timezone: Timezone for parsing (default: Asia/Shanghai)
                 Supports standard timezone names like "UTC", "America/New_York"

    Returns:
        Dictionary containing:
        - success: bool - Whether parsing succeeded
        - parsed: dict or None - Parsed result with:
            - value: str or list - Parsed datetime(s)
            - is_range: bool - Whether result is a time range
            - is_date_only: bool - Whether result has no time component
            - original_expression: str - Original input
            - confidence: float - Confidence score (0-1)
        - error: str or None - Error message if failed

    Examples:
        >>> await parse_time("昨天")
        {"success": true, "parsed": {"value": "2024-01-14", ...}}

        >>> await parse_time("国庆节期间")
        {"success": true, "parsed": {"value": ["2024-10-01", "2024-10-07"], ...}}
    """
    return await _parse_time_handler(expression, timezone)
