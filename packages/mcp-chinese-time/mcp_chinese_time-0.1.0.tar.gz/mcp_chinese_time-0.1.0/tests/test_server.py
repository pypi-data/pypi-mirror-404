# -*- coding: utf-8 -*-
"""
Integration tests for MCP server.
"""

import pytest

from mcp_chinese_time.server import _parse_time_handler


class TestMCPServer:
    """Test cases for MCP server tools."""

    @pytest.mark.asyncio
    async def test_parse_time_success(self):
        """Test parse_time tool with valid expression."""
        result = await _parse_time_handler("昨天")

        assert result["success"] is True
        assert result["parsed"] is not None
        assert result["error"] is None
        assert result["parsed"]["is_date_only"] is True

    @pytest.mark.asyncio
    async def test_parse_time_range(self):
        """Test parse_time tool with range expression."""
        result = await _parse_time_handler("昨天到今天")

        assert result["success"] is True
        assert result["parsed"]["is_range"] is True
        assert len(result["parsed"]["value"]) == 2

    @pytest.mark.asyncio
    async def test_parse_time_holiday(self):
        """Test parse_time tool with holiday expression."""
        result = await _parse_time_handler("国庆节期间")

        assert result["success"] is True
        assert result["parsed"]["is_range"] is True

    @pytest.mark.asyncio
    async def test_parse_time_with_timezone(self):
        """Test parse_time tool with custom timezone."""
        result = await _parse_time_handler("今天", timezone="UTC")

        assert result["success"] is True
        assert result["parsed"] is not None

    @pytest.mark.asyncio
    async def test_parse_time_invalid_timezone(self):
        """Test parse_time tool with invalid timezone."""
        result = await _parse_time_handler("今天", timezone="Invalid/Timezone")

        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_parse_time_specific_time(self):
        """Test parse_time tool with time of day."""
        result = await _parse_time_handler("下午3点30分")

        assert result["success"] is True
        assert result["parsed"]["is_date_only"] is False
        assert "15:30:00" in result["parsed"]["value"]

    @pytest.mark.asyncio
    async def test_parse_time_weekday(self):
        """Test parse_time tool with weekday expression."""
        result = await _parse_time_handler("下周一")

        assert result["success"] is True
        assert result["parsed"]["is_date_only"] is True

    @pytest.mark.asyncio
    async def test_parse_time_relative_weeks(self):
        """Test parse_time tool with relative week expression."""
        result = await _parse_time_handler("两周前")

        assert result["success"] is True
        assert result["parsed"]["is_range"] is True
