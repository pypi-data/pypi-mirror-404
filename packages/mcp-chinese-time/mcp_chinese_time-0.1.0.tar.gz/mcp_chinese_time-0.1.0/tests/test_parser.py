# -*- coding: utf-8 -*-
"""
Unit tests for FuzzyTimeParser.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from mcp_chinese_time.parser import FuzzyTimeParser


class TestFuzzyTimeParser:
    """Test cases for FuzzyTimeParser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance with fixed time."""
        parser = FuzzyTimeParser(timezone="Asia/Shanghai")
        return parser

    @pytest.fixture
    def fixed_now(self):
        """Fixed datetime for consistent testing."""
        return datetime(2024, 1, 15, 10, 30, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    def set_fixed_time(self, parser, fixed_now):
        """Helper to set fixed time on parser."""
        # Override the now property by setting _now directly and preventing reset
        original_reset = parser.reset_now
        parser._now = fixed_now
        parser.reset_now = lambda: None  # Prevent reset
        return original_reset

    def test_parse_today(self, parser, fixed_now):
        """Test parsing '今天'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("今天")
        assert result.value == "2024-01-15"
        assert result.is_date_only is True
        assert result.confidence == 1.0

    def test_parse_yesterday(self, parser, fixed_now):
        """Test parsing '昨天'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("昨天")
        assert result.value == "2024-01-14"
        assert result.is_date_only is True

    def test_parse_tomorrow(self, parser, fixed_now):
        """Test parsing '明天'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("明天")
        assert result.value == "2024-01-16"
        assert result.is_date_only is True

    def test_parse_day_before_yesterday(self, parser, fixed_now):
        """Test parsing '前天'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("前天")
        assert result.value == "2024-01-13"

    def test_parse_day_after_tomorrow(self, parser, fixed_now):
        """Test parsing '后天'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("后天")
        assert result.value == "2024-01-17"

    def test_parse_n_days_ago(self, parser, fixed_now):
        """Test parsing 'N天前'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("三天前")
        assert result.value == "2024-01-12"

        result = parser.parse("5天前")
        assert result.value == "2024-01-10"

    def test_parse_n_days_later(self, parser, fixed_now):
        """Test parsing 'N天后'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("三天后")
        assert result.value == "2024-01-18"

        result = parser.parse("7天后")
        assert result.value == "2024-01-22"

    def test_parse_this_week(self, parser, fixed_now):
        """Test parsing '本周' (week containing Jan 15, 2024 - Monday is Jan 15)."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("本周")
        assert result.is_range is True
        assert result.value == ["2024-01-15", "2024-01-21"]

    def test_parse_last_week(self, parser, fixed_now):
        """Test parsing '上周'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("上周")
        assert result.is_range is True
        assert result.value == ["2024-01-08", "2024-01-14"]

    def test_parse_next_week(self, parser, fixed_now):
        """Test parsing '下周'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("下周")
        assert result.is_range is True
        assert result.value == ["2024-01-22", "2024-01-28"]

    def test_parse_n_weeks_ago(self, parser, fixed_now):
        """Test parsing 'N周前'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("两周前")
        assert result.is_range is True
        assert result.value == ["2024-01-01", "2024-01-07"]

    def test_parse_this_month(self, parser, fixed_now):
        """Test parsing '本月'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("本月")
        assert result.is_range is True
        assert result.value == ["2024-01-01", "2024-01-31"]

    def test_parse_last_month(self, parser, fixed_now):
        """Test parsing '上个月'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("上个月")
        assert result.is_range is True
        assert result.value == ["2023-12-01", "2023-12-31"]

    def test_parse_next_month(self, parser, fixed_now):
        """Test parsing '下个月'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("下个月")
        assert result.is_range is True
        assert result.value == ["2024-02-01", "2024-02-29"]  # 2024 is a leap year

    def test_parse_specific_date_full(self, parser):
        """Test parsing '2024年1月1日'."""
        result = parser.parse("2024年1月1日")
        assert result.value == "2024-01-01"
        assert result.is_date_only is True
        assert result.confidence == 1.0

    def test_parse_specific_date_month_day(self, parser, fixed_now):
        """Test parsing '1月20日'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("1月20日")
        assert result.value == "2024-01-20"

    def test_parse_specific_date_day_only(self, parser, fixed_now):
        """Test parsing '20号'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("20号")
        assert result.value == "2024-01-20"

    def test_parse_time_of_day_morning(self, parser, fixed_now):
        """Test parsing '上午9点'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("上午9点")
        assert result.value == "2024-01-15 09:00:00"
        assert result.is_date_only is False

    def test_parse_time_of_day_afternoon(self, parser, fixed_now):
        """Test parsing '下午3点30分'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("下午3点30分")
        assert result.value == "2024-01-15 15:30:00"
        assert result.is_date_only is False

    def test_parse_time_of_day_evening(self, parser, fixed_now):
        """Test parsing '晚上8点'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("晚上8点")
        assert result.value == "2024-01-15 20:00:00"

    def test_parse_weekday_this_week(self, parser, fixed_now):
        """Test parsing '周三' (this week)."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("周三")
        # Jan 15 is Monday, so Wednesday is Jan 17
        assert result.value == "2024-01-17"

    def test_parse_weekday_last_week(self, parser, fixed_now):
        """Test parsing '上周三'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("上周三")
        assert result.value == "2024-01-10"

    def test_parse_weekday_next_week(self, parser, fixed_now):
        """Test parsing '下周五'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("下周五")
        assert result.value == "2024-01-26"

    def test_parse_range_yesterday_to_today(self, parser, fixed_now):
        """Test parsing '昨天到今天'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("昨天到今天")
        assert result.is_range is True
        assert result.value == ["2024-01-14", "2024-01-15"]

    def test_parse_range_with_至(self, parser, fixed_now):
        """Test parsing '昨天至今天'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("昨天至今天")
        assert result.is_range is True
        assert result.value == ["2024-01-14", "2024-01-15"]

    def test_parse_range_weekday(self, parser, fixed_now):
        """Test parsing '上周一到周五'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("上周一到周五")
        assert result.is_range is True
        assert result.value == ["2024-01-08", "2024-01-19"]

    def test_parse_solar_holiday_national_day(self, parser, fixed_now):
        """Test parsing '国庆节'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("国庆节")
        assert result.is_range is True
        assert result.value == ["2024-10-01", "2024-10-07"]

    def test_parse_solar_holiday_labor_day(self, parser, fixed_now):
        """Test parsing '劳动节'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("劳动节")
        assert result.is_range is True
        assert result.value == ["2024-05-01", "2024-05-05"]

    def test_parse_solar_holiday_new_year(self, parser, fixed_now):
        """Test parsing '元旦'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("元旦")
        assert result.value == "2024-01-01"
        assert result.is_range is False

    def test_parse_holiday_with_period(self, parser, fixed_now):
        """Test parsing '国庆节期间'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("国庆节期间")
        assert result.is_range is True
        assert result.value == ["2024-10-01", "2024-10-07"]

    def test_parse_qingming(self, parser, fixed_now):
        """Test parsing '清明节'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("清明节")
        # 2024 is a leap year, so Qingming is April 4
        assert result.value == "2024-04-04"

    def test_parse_unknown_expression(self, parser, fixed_now):
        """Test parsing unknown expression returns fallback."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("随便什么")
        assert result.value == "2024-01-15"  # Falls back to today
        assert result.confidence == 0.3

    def test_chinese_number_conversion(self, parser):
        """Test Chinese number conversion."""
        assert parser._cn_to_num("一") == 1
        assert parser._cn_to_num("二") == 2
        assert parser._cn_to_num("两") == 2
        assert parser._cn_to_num("十") == 10
        assert parser._cn_to_num("十五") == 15
        assert parser._cn_to_num("二十") == 20
        assert parser._cn_to_num("二十三") == 23
        assert parser._cn_to_num("5") == 5
        assert parser._cn_to_num("15") == 15

    def test_timezone_support(self):
        """Test different timezone support."""
        parser_shanghai = FuzzyTimeParser(timezone="Asia/Shanghai")
        parser_utc = FuzzyTimeParser(timezone="UTC")

        # Both should work without errors
        result_shanghai = parser_shanghai.parse("今天")
        result_utc = parser_utc.parse("今天")

        assert result_shanghai.is_date_only is True
        assert result_utc.is_date_only is True


class TestLunarHolidays:
    """Test cases for lunar calendar holidays."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return FuzzyTimeParser(timezone="Asia/Shanghai")

    @pytest.fixture
    def fixed_now(self):
        """Fixed datetime for consistent testing."""
        return datetime(2024, 1, 15, 10, 30, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    def set_fixed_time(self, parser, fixed_now):
        """Helper to set fixed time on parser."""
        parser._now = fixed_now
        parser.reset_now = lambda: None

    def test_parse_spring_festival(self, parser, fixed_now):
        """Test parsing '春节' (Chinese New Year 2024 is Feb 10)."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("春节")
        # Spring Festival 2024: Feb 10
        assert result.is_range is True
        # The exact dates depend on zhdate conversion
        assert len(result.value) == 2

    def test_parse_mid_autumn(self, parser, fixed_now):
        """Test parsing '中秋节'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("中秋节")
        # Mid-Autumn Festival 2024 is Sept 17
        assert result.confidence == 0.95

    def test_parse_dragon_boat(self, parser, fixed_now):
        """Test parsing '端午节'."""
        self.set_fixed_time(parser, fixed_now)
        result = parser.parse("端午节")
        assert result.is_range is True
        assert result.confidence == 0.95
