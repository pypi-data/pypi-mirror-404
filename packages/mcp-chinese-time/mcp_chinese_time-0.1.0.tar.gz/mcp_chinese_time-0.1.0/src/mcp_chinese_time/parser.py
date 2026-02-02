# -*- coding: utf-8 -*-
"""
Fuzzy Time Parser - Core logic for parsing Chinese time expressions.

This module provides the FuzzyTimeParser class which can convert natural language
time expressions in Chinese to standard datetime formats.

Supported Expressions:
- Relative time: 昨天, 今天, 明天, 三天前, 两周后
- Time ranges: 昨天到今天, 上周一到周五
- Time of day: 上午9点到10点, 下午3点
- Holidays: 国庆节期间, 春节期间 (including lunar calendar holidays)
- Specific dates: 2024年1月1日, 1月15号
"""

import logging
import re
from calendar import monthrange
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ParsedTime(BaseModel):
    """Parsed time result."""

    value: Union[str, List[str]] = Field(
        ...,
        description="Parsed datetime string(s). Single string for point in time, list for range.",
    )
    is_range: bool = Field(default=False, description="Whether the result is a time range")
    is_date_only: bool = Field(
        default=False, description="Whether the result is date only (no time component)"
    )
    original_expression: str = Field(..., description="Original input expression")
    confidence: float = Field(default=1.0, description="Confidence score (0-1) of the parsing")


class ParseTimeOutput(BaseModel):
    """Output model for parse_time tool."""

    success: bool = Field(default=True, description="Operation success")
    parsed: Optional[ParsedTime] = Field(None, description="Parsed time result")
    error: Optional[str] = Field(None, description="Error message if failed")


class FuzzyTimeParser:
    """
    Parser for fuzzy time expressions in Chinese.

    Converts natural language time expressions to standard datetime format.

    Example:
        parser = FuzzyTimeParser(timezone="Asia/Shanghai")
        result = parser.parse("昨天")
        print(result.value)  # "2024-01-14"

        result = parser.parse("上周一到周五")
        print(result.value)  # ["2024-01-08", "2024-01-12"]
    """

    # Chinese number mapping
    CN_NUMBERS = {
        "零": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "十一": 11,
        "十二": 12,
        "半": 0.5,
    }

    # Day of week mapping
    WEEKDAYS = {
        "一": 0,
        "二": 1,
        "三": 2,
        "四": 3,
        "五": 4,
        "六": 5,
        "日": 6,
        "天": 6,
    }

    # Solar (Gregorian) holidays - fixed dates (month, day, duration_days)
    SOLAR_HOLIDAYS = {
        "元旦": (1, 1, 1),
        "情人节": (2, 14, 1),
        "妇女节": (3, 8, 1),
        "植树节": (3, 12, 1),
        "愚人节": (4, 1, 1),
        "劳动节": (5, 1, 5),
        "五一": (5, 1, 5),
        "儿童节": (6, 1, 1),
        "建党节": (7, 1, 1),
        "建军节": (8, 1, 1),
        "教师节": (9, 10, 1),
        "国庆": (10, 1, 7),
        "国庆节": (10, 1, 7),
        "双十一": (11, 11, 1),
        "平安夜": (12, 24, 1),
        "圣诞": (12, 25, 1),
        "圣诞节": (12, 25, 1),
    }

    # Lunar (Chinese) holidays - need conversion (lunar_month, lunar_day, duration_days)
    LUNAR_HOLIDAYS = {
        "春节": (1, 1, 7),
        "过年": (1, 1, 7),
        "大年初一": (1, 1, 1),
        "除夕": (12, 30, 1),
        "年三十": (12, 30, 1),
        "元宵": (1, 15, 1),
        "元宵节": (1, 15, 1),
        "龙抬头": (2, 2, 1),
        "端午": (5, 5, 3),
        "端午节": (5, 5, 3),
        "七夕": (7, 7, 1),
        "七夕节": (7, 7, 1),
        "中元": (7, 15, 1),
        "中元节": (7, 15, 1),
        "中秋": (8, 15, 1),
        "中秋节": (8, 15, 1),
        "重阳": (9, 9, 1),
        "重阳节": (9, 9, 1),
        "腊八": (12, 8, 1),
        "腊八节": (12, 8, 1),
        "小年": (12, 23, 1),
    }

    # Qingming requires special handling (based on solar term, usually April 4-6)
    QINGMING_HOLIDAYS = {"清明", "清明节"}

    def __init__(self, timezone: str = "Asia/Shanghai"):
        """
        Initialize parser with timezone.

        Args:
            timezone: Timezone string (e.g., "Asia/Shanghai", "UTC")
        """
        self.tz = ZoneInfo(timezone)
        self._now = None

    @property
    def now(self) -> datetime:
        """Get current datetime (cached for consistent parsing within a single parse call)."""
        if self._now is None:
            self._now = datetime.now(self.tz)
        return self._now

    def reset_now(self) -> None:
        """Reset cached now time."""
        self._now = None

    def parse(self, expression: str) -> ParsedTime:
        """
        Parse a fuzzy time expression.

        Args:
            expression: Fuzzy time expression in Chinese

        Returns:
            ParsedTime with parsed result
        """
        self.reset_now()
        expression = expression.strip()

        # Try different parsing strategies
        # Order matters: weekday must come before relative_week to handle "上周三" correctly
        parsers = [
            self._parse_range,
            self._parse_holiday,
            self._parse_relative_day,
            self._parse_weekday,  # Before relative_week to handle "上周三" vs "上周"
            self._parse_relative_week,
            self._parse_relative_month,
            self._parse_time_of_day,
            self._parse_specific_date,
        ]

        for parser in parsers:
            result = parser(expression)
            if result:
                return result

        # Fallback: return today's date with low confidence
        return ParsedTime(
            value=self.now.strftime("%Y-%m-%d"),
            is_range=False,
            is_date_only=True,
            original_expression=expression,
            confidence=0.3,
        )

    def _cn_to_num(self, cn: str) -> int:
        """Convert Chinese number to int."""
        if cn.isdigit():
            return int(cn)

        # Handle compound numbers like "十五"
        if cn in self.CN_NUMBERS:
            return self.CN_NUMBERS[cn]

        # Handle "十X" pattern
        if cn.startswith("十") and len(cn) == 2:
            return 10 + self.CN_NUMBERS.get(cn[1], 0)

        # Handle "X十" pattern
        if len(cn) == 2 and cn.endswith("十"):
            return self.CN_NUMBERS.get(cn[0], 0) * 10

        # Handle "X十Y" pattern
        if "十" in cn and len(cn) == 3:
            parts = cn.split("十")
            return self.CN_NUMBERS.get(parts[0], 0) * 10 + self.CN_NUMBERS.get(parts[1], 0)

        return 1  # Default

    def _format_datetime(self, dt: datetime, date_only: bool = False) -> str:
        """Format datetime to standard string."""
        if date_only:
            return dt.strftime("%Y-%m-%d")
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _parse_range(self, expr: str) -> Optional[ParsedTime]:
        """Parse time range expressions like '昨天到今天'."""
        range_patterns = [
            (r"(.+?)到(.+)", True),
            (r"(.+?)至(.+)", True),
            (r"(.+?)-(.+)", True),
            (r"(.+?)~(.+)", True),
            (r"从(.+?)到(.+)", True),
        ]

        for pattern, _ in range_patterns:
            match = re.match(pattern, expr)
            if match:
                start_expr = match.group(1).strip()
                end_expr = match.group(2).strip()

                start_result = self._parse_single(start_expr)
                end_result = self._parse_single(end_expr)

                if start_result and end_result:
                    return ParsedTime(
                        value=[start_result[0], end_result[0]],
                        is_range=True,
                        is_date_only=start_result[1] and end_result[1],
                        original_expression=expr,
                        confidence=min(start_result[2], end_result[2]),
                    )

        return None

    def _parse_single(self, expr: str) -> Optional[Tuple[str, bool, float]]:
        """Parse a single time expression. Returns (datetime_str, is_date_only, confidence)."""
        parsers = [
            self._parse_holiday,
            self._parse_relative_day,
            self._parse_relative_week,
            self._parse_relative_month,
            self._parse_time_of_day,
            self._parse_specific_date,
            self._parse_weekday,
        ]

        for parser in parsers:
            result = parser(expr)
            if result:
                val = result.value if not isinstance(result.value, list) else result.value[0]
                return (val, result.is_date_only, result.confidence)

        return None

    def _parse_holiday(self, expr: str) -> Optional[ParsedTime]:
        """
        Parse holiday expressions like '国庆节期间'.

        Handles three types of holidays:
        1. Solar (Gregorian) holidays - fixed dates
        2. Lunar (Chinese) holidays - converted from lunar calendar
        3. Qingming - based on solar term (usually April 4-6)
        """
        year = self.now.year

        # 1. Check solar (Gregorian) holidays
        for holiday, (month, day, duration) in self.SOLAR_HOLIDAYS.items():
            if holiday in expr:
                holiday_date = datetime(year, month, day, tzinfo=self.tz)
                return self._create_holiday_result(holiday_date, duration, expr)

        # 2. Check lunar (Chinese) holidays
        for holiday, (lunar_month, lunar_day, duration) in self.LUNAR_HOLIDAYS.items():
            if holiday in expr:
                holiday_date = self._lunar_to_solar(year, lunar_month, lunar_day)
                if holiday_date:
                    return self._create_holiday_result(holiday_date, duration, expr)

        # 3. Check Qingming - special handling based on solar term
        if any(qm in expr for qm in self.QINGMING_HOLIDAYS):
            # Qingming is usually on April 4th or 5th
            qingming_day = 4 if self._is_leap_year(year) else 5
            holiday_date = datetime(year, 4, qingming_day, tzinfo=self.tz)
            duration = 3 if "期间" in expr else 1
            return self._create_holiday_result(holiday_date, duration, expr)

        return None

    def _lunar_to_solar(self, year: int, lunar_month: int, lunar_day: int) -> Optional[datetime]:
        """
        Convert lunar (Chinese) date to solar (Gregorian) date.

        Uses zhdate library for accurate conversion.

        Args:
            year: Target year
            lunar_month: Lunar month (1-12)
            lunar_day: Lunar day (1-30)

        Returns:
            datetime in Gregorian calendar, or None if conversion fails
        """
        try:
            from zhdate import ZhDate

            # Handle special case: 除夕 (lunar 12/30 or 12/29)
            if lunar_month == 12 and lunar_day >= 29:
                try:
                    spring_festival = ZhDate(year, 1, 1)
                    solar_spring = spring_festival.to_datetime()
                    chuxi_date = solar_spring - timedelta(days=1)
                    return datetime(
                        chuxi_date.year, chuxi_date.month, chuxi_date.day, tzinfo=self.tz
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate Chuxi for year {year}: {e}")
                    return None
            else:
                lunar = ZhDate(year, lunar_month, lunar_day)

            # Convert to Gregorian
            solar_date = lunar.to_datetime()
            return datetime(solar_date.year, solar_date.month, solar_date.day, tzinfo=self.tz)

        except ImportError:
            logger.warning("zhdate library not installed, lunar date conversion unavailable")
            return None
        except Exception as e:
            logger.warning(f"Failed to convert lunar date {year}/{lunar_month}/{lunar_day}: {e}")
            return None

    def _create_holiday_result(
        self, holiday_date: datetime, duration: int, expr: str
    ) -> ParsedTime:
        """Create ParsedTime result for a holiday."""
        if duration > 1 or "期间" in expr:
            start = holiday_date
            end = holiday_date + timedelta(days=duration - 1)
            return ParsedTime(
                value=[
                    self._format_datetime(start, True),
                    self._format_datetime(end, True),
                ],
                is_range=True,
                is_date_only=True,
                original_expression=expr,
                confidence=0.95,
            )
        else:
            return ParsedTime(
                value=self._format_datetime(holiday_date, True),
                is_range=False,
                is_date_only=True,
                original_expression=expr,
                confidence=0.95,
            )

    def _is_leap_year(self, year: int) -> bool:
        """Check if a year is a leap year."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def _parse_relative_day(self, expr: str) -> Optional[ParsedTime]:
        """Parse relative day expressions like '昨天', '三天前'."""
        # Direct day references
        day_map = {
            "今天": 0,
            "今日": 0,
            "昨天": -1,
            "昨日": -1,
            "前天": -2,
            "前日": -2,
            "大前天": -3,
            "明天": 1,
            "明日": 1,
            "后天": 2,
            "后日": 2,
            "大后天": 3,
        }

        for key, offset in day_map.items():
            if expr == key or expr.startswith(key):
                target = self.now + timedelta(days=offset)
                return ParsedTime(
                    value=self._format_datetime(target, True),
                    is_range=False,
                    is_date_only=True,
                    original_expression=expr,
                    confidence=1.0,
                )

        # Pattern: X天前/后
        patterns = [
            (r"(\d+|[一二三四五六七八九十]+)天前", -1),
            (r"(\d+|[一二三四五六七八九十]+)天后", 1),
            (r"(\d+|[一二三四五六七八九十]+)日前", -1),
            (r"(\d+|[一二三四五六七八九十]+)日后", 1),
        ]

        for pattern, direction in patterns:
            match = re.match(pattern, expr)
            if match:
                num = self._cn_to_num(match.group(1))
                target = self.now + timedelta(days=num * direction)
                return ParsedTime(
                    value=self._format_datetime(target, True),
                    is_range=False,
                    is_date_only=True,
                    original_expression=expr,
                    confidence=0.95,
                )

        return None

    def _parse_relative_week(self, expr: str) -> Optional[ParsedTime]:
        """Parse relative week expressions like '上周', '三周前'."""
        # Week references
        week_map = {
            "本周": 0,
            "这周": 0,
            "上周": -1,
            "上一周": -1,
            "上上周": -2,
            "下周": 1,
            "下一周": 1,
            "下下周": 2,
        }

        for key, offset in week_map.items():
            if expr == key or expr.startswith(key):
                # Get start of the target week (Monday)
                today = self.now.date()
                start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
                end_of_week = start_of_week + timedelta(days=6)

                return ParsedTime(
                    value=[
                        start_of_week.strftime("%Y-%m-%d"),
                        end_of_week.strftime("%Y-%m-%d"),
                    ],
                    is_range=True,
                    is_date_only=True,
                    original_expression=expr,
                    confidence=0.95,
                )

        # Pattern: X周前/后 (两 is also included for "两周前")
        patterns = [
            (r"(\d+|[一二两三四五六七八九十]+)周前", -1),
            (r"(\d+|[一二两三四五六七八九十]+)周后", 1),
            (r"(\d+|[一二两三四五六七八九十]+)个?星期前", -1),
            (r"(\d+|[一二两三四五六七八九十]+)个?星期后", 1),
        ]

        for pattern, direction in patterns:
            match = re.match(pattern, expr)
            if match:
                num = self._cn_to_num(match.group(1))
                today = self.now.date()
                start_of_week = (
                    today - timedelta(days=today.weekday()) + timedelta(weeks=num * direction)
                )
                end_of_week = start_of_week + timedelta(days=6)

                return ParsedTime(
                    value=[
                        start_of_week.strftime("%Y-%m-%d"),
                        end_of_week.strftime("%Y-%m-%d"),
                    ],
                    is_range=True,
                    is_date_only=True,
                    original_expression=expr,
                    confidence=0.9,
                )

        return None

    def _parse_relative_month(self, expr: str) -> Optional[ParsedTime]:
        """Parse relative month expressions like '上个月', '三个月前'."""
        month_map = {
            "本月": 0,
            "这个月": 0,
            "上个月": -1,
            "上月": -1,
            "下个月": 1,
            "下月": 1,
        }

        for key, offset in month_map.items():
            if expr == key or expr.startswith(key):
                year = self.now.year
                month = self.now.month + offset

                while month < 1:
                    month += 12
                    year -= 1
                while month > 12:
                    month -= 12
                    year += 1

                _, last_day = monthrange(year, month)

                return ParsedTime(
                    value=[
                        f"{year}-{month:02d}-01",
                        f"{year}-{month:02d}-{last_day:02d}",
                    ],
                    is_range=True,
                    is_date_only=True,
                    original_expression=expr,
                    confidence=0.95,
                )

        # Pattern: X个月前/后
        patterns = [
            (r"(\d+|[一二三四五六七八九十]+)个?月前", -1),
            (r"(\d+|[一二三四五六七八九十]+)个?月后", 1),
        ]

        for pattern, direction in patterns:
            match = re.match(pattern, expr)
            if match:
                num = self._cn_to_num(match.group(1))
                offset = num * direction

                year = self.now.year
                month = self.now.month + offset

                while month < 1:
                    month += 12
                    year -= 1
                while month > 12:
                    month -= 12
                    year += 1

                _, last_day = monthrange(year, month)

                return ParsedTime(
                    value=[
                        f"{year}-{month:02d}-01",
                        f"{year}-{month:02d}-{last_day:02d}",
                    ],
                    is_range=True,
                    is_date_only=True,
                    original_expression=expr,
                    confidence=0.85,
                )

        return None

    def _parse_time_of_day(self, expr: str) -> Optional[ParsedTime]:
        """Parse time of day expressions like '上午9点'."""
        # Single time point
        pattern = r"(凌晨|早上|上午|中午|下午|晚上|深夜)?(\d+|[一二三四五六七八九十]+)点(?:(\d+|[一二三四五六七八九十]+)分?)?"
        match = re.search(pattern, expr)

        if match:
            period = match.group(1)
            hour = self._cn_to_num(match.group(2))
            minute = self._cn_to_num(match.group(3)) if match.group(3) else 0

            # Adjust hour based on period
            if period:
                if period in ("下午", "晚上") and hour < 12:
                    hour += 12
                elif period == "凌晨" and hour == 12:
                    hour = 0

            today = self.now.date()
            target = datetime(today.year, today.month, today.day, hour, minute, tzinfo=self.tz)

            return ParsedTime(
                value=self._format_datetime(target, False),
                is_range=False,
                is_date_only=False,
                original_expression=expr,
                confidence=0.9,
            )

        return None

    def _parse_specific_date(self, expr: str) -> Optional[ParsedTime]:
        """Parse specific date expressions like '2024年1月1日'."""
        patterns = [
            # Full date: 2024年1月1日
            (
                r"(\d{4})年(\d{1,2})月(\d{1,2})[日号]?",
                lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3))),
            ),
            # Month and day: 1月1日
            (
                r"(\d{1,2})月(\d{1,2})[日号]?",
                lambda m: (self.now.year, int(m.group(1)), int(m.group(2))),
            ),
            # Day only: 15号
            (r"(\d{1,2})[日号]", lambda m: (self.now.year, self.now.month, int(m.group(1)))),
        ]

        for pattern, extractor in patterns:
            match = re.match(pattern, expr)
            if match:
                try:
                    year, month, day = extractor(match)
                    target = datetime(year, month, day, tzinfo=self.tz)
                    return ParsedTime(
                        value=self._format_datetime(target, True),
                        is_range=False,
                        is_date_only=True,
                        original_expression=expr,
                        confidence=1.0,
                    )
                except ValueError:
                    continue

        return None

    def _parse_weekday(self, expr: str) -> Optional[ParsedTime]:
        """Parse weekday expressions like '周一', '上周三'."""
        # Pattern: (上|下|这)?周/星期X
        pattern = r"(上上?|下下?|这)?(?:周|星期)([一二三四五六日天])"
        match = re.match(pattern, expr)

        if match:
            prefix = match.group(1) or "这"
            weekday_cn = match.group(2)
            weekday = self.WEEKDAYS.get(weekday_cn, 0)

            today = self.now.date()
            current_weekday = today.weekday()

            # Calculate week offset
            week_offset = 0
            if prefix == "上":
                week_offset = -1
            elif prefix == "上上":
                week_offset = -2
            elif prefix == "下":
                week_offset = 1
            elif prefix == "下下":
                week_offset = 2

            # Calculate target date
            days_diff = weekday - current_weekday + (week_offset * 7)
            target = today + timedelta(days=days_diff)

            return ParsedTime(
                value=target.strftime("%Y-%m-%d"),
                is_range=False,
                is_date_only=True,
                original_expression=expr,
                confidence=0.95,
            )

        return None
