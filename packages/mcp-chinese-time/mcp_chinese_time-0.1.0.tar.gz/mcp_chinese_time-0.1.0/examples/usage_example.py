# -*- coding: utf-8 -*-
"""
Usage examples for mcp-chinese-time.

This script demonstrates how to use the FuzzyTimeParser directly in Python.
"""

from mcp_chinese_time import FuzzyTimeParser


def main():
    """Run usage examples."""
    parser = FuzzyTimeParser(timezone="Asia/Shanghai")

    print("=" * 60)
    print("MCP Chinese Time - Usage Examples")
    print("=" * 60)

    # Example 1: Relative days
    print("\n1. Relative Days:")
    for expr in ["今天", "昨天", "明天", "三天前", "五天后"]:
        result = parser.parse(expr)
        print(f"   {expr} -> {result.value}")

    # Example 2: Relative weeks
    print("\n2. Relative Weeks:")
    for expr in ["本周", "上周", "下周", "两周前"]:
        result = parser.parse(expr)
        print(f"   {expr} -> {result.value}")

    # Example 3: Relative months
    print("\n3. Relative Months:")
    for expr in ["本月", "上个月", "下个月"]:
        result = parser.parse(expr)
        print(f"   {expr} -> {result.value}")

    # Example 4: Weekdays
    print("\n4. Weekdays:")
    for expr in ["周一", "周三", "上周五", "下周一"]:
        result = parser.parse(expr)
        print(f"   {expr} -> {result.value}")

    # Example 5: Time of day
    print("\n5. Time of Day:")
    for expr in ["上午9点", "下午3点30分", "晚上8点"]:
        result = parser.parse(expr)
        print(f"   {expr} -> {result.value}")

    # Example 6: Specific dates
    print("\n6. Specific Dates:")
    for expr in ["2024年1月15日", "3月20日", "25号"]:
        result = parser.parse(expr)
        print(f"   {expr} -> {result.value}")

    # Example 7: Time ranges
    print("\n7. Time Ranges:")
    for expr in ["昨天到今天", "上周一到周五", "1月1日到1月15日"]:
        result = parser.parse(expr)
        print(f"   {expr} -> {result.value}")

    # Example 8: Solar holidays
    print("\n8. Solar Holidays:")
    for expr in ["元旦", "劳动节", "国庆节期间"]:
        result = parser.parse(expr)
        print(f"   {expr} -> {result.value}")

    # Example 9: Lunar holidays (requires zhdate)
    print("\n9. Lunar Holidays:")
    try:
        for expr in ["春节", "中秋节", "端午节"]:
            result = parser.parse(expr)
            print(f"   {expr} -> {result.value}")
    except Exception as e:
        print(f"   (Lunar conversion failed: {e})")

    # Example 10: Confidence scores
    print("\n10. Confidence Scores:")
    for expr in ["今天", "国庆节", "随便什么"]:
        result = parser.parse(expr)
        print(f"   {expr} -> confidence: {result.confidence}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
