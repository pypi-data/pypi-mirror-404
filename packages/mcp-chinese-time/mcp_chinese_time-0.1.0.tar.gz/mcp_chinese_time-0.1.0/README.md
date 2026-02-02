# MCP Chinese Time

[![PyPI version](https://badge.fury.io/py/mcp-chinese-time.svg)](https://badge.fury.io/py/mcp-chinese-time)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server for parsing Chinese fuzzy time expressions to standard datetime formats.

## Features

- **Relative Time**: 昨天, 今天, 明天, 三天前, 两周后
- **Time Ranges**: 昨天到今天, 上周一到周五
- **Time of Day**: 上午9点, 下午3点30分, 晚上8点
- **Holidays**: Both solar (国庆节, 劳动节) and lunar (春节, 中秋节, 端午节)
- **Specific Dates**: 2024年1月1日, 1月15号
- **Weekdays**: 周一, 上周三, 下周五
- **Chinese Numbers**: Supports both Arabic (3) and Chinese (三) numerals

## Installation

### Using pip

```bash
pip install mcp-chinese-time
```

### Using uvx (recommended for MCP)

```bash
uvx mcp-chinese-time
```

## Usage

### As an MCP Server

#### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "chinese-time": {
      "command": "uvx",
      "args": ["mcp-chinese-time"]
    }
  }
}
```

#### VS Code Configuration

Add to your VS Code settings or `.vscode/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "chinese-time": {
        "command": "uvx",
        "args": ["mcp-chinese-time"]
      }
    }
  }
}
```

#### With pip installation

```json
{
  "mcpServers": {
    "chinese-time": {
      "command": "mcp-chinese-time"
    }
  }
}
```

### As a Python Library

```python
from mcp_chinese_time import FuzzyTimeParser

parser = FuzzyTimeParser(timezone="Asia/Shanghai")

# Parse relative time
result = parser.parse("昨天")
print(result.value)  # "2024-01-14"

# Parse time range
result = parser.parse("上周一到周五")
print(result.value)  # ["2024-01-08", "2024-01-12"]
print(result.is_range)  # True

# Parse holiday
result = parser.parse("国庆节期间")
print(result.value)  # ["2024-10-01", "2024-10-07"]

# Parse time of day
result = parser.parse("下午3点30分")
print(result.value)  # "2024-01-15 15:30:00"
print(result.is_date_only)  # False

# Parse lunar holiday (requires zhdate)
result = parser.parse("中秋节")
print(result.value)  # "2024-09-17"
```

### Running the Server Directly

```bash
# Using the installed command
mcp-chinese-time

# Or using Python module
python -m mcp_chinese_time
```

## API Reference

### Tool: `parse_time`

Parse fuzzy Chinese time expressions to standard datetime format.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `expression` | string | Yes | - | Fuzzy time expression in Chinese |
| `timezone` | string | No | "Asia/Shanghai" | Timezone for parsing |

**Returns:**

```json
{
  "success": true,
  "parsed": {
    "value": "2024-01-15",
    "is_range": false,
    "is_date_only": true,
    "original_expression": "今天",
    "confidence": 1.0
  },
  "error": null
}
```

For time ranges:

```json
{
  "success": true,
  "parsed": {
    "value": ["2024-10-01", "2024-10-07"],
    "is_range": true,
    "is_date_only": true,
    "original_expression": "国庆节期间",
    "confidence": 0.95
  },
  "error": null
}
```

## Supported Expressions

### Relative Days

| Expression | Description |
|------------|-------------|
| 今天, 今日 | Today |
| 昨天, 昨日 | Yesterday |
| 前天, 前日 | Day before yesterday |
| 大前天 | 3 days ago |
| 明天, 明日 | Tomorrow |
| 后天, 后日 | Day after tomorrow |
| 大后天 | 3 days from now |
| N天前 | N days ago |
| N天后 | N days from now |

### Relative Weeks

| Expression | Description |
|------------|-------------|
| 本周, 这周 | This week |
| 上周, 上一周 | Last week |
| 上上周 | 2 weeks ago |
| 下周, 下一周 | Next week |
| 下下周 | 2 weeks from now |
| N周前 | N weeks ago |
| N周后 | N weeks from now |

### Relative Months

| Expression | Description |
|------------|-------------|
| 本月, 这个月 | This month |
| 上个月, 上月 | Last month |
| 下个月, 下月 | Next month |
| N个月前 | N months ago |
| N个月后 | N months from now |

### Weekdays

| Expression | Description |
|------------|-------------|
| 周一 ~ 周日 | Weekday (this week) |
| 星期一 ~ 星期日 | Weekday (this week) |
| 上周X | Last week's weekday |
| 下周X | Next week's weekday |

### Time of Day

| Expression | Description |
|------------|-------------|
| 上午X点 | X AM |
| 下午X点 | X PM |
| 晚上X点 | X PM (evening) |
| X点Y分 | X:Y |

### Solar Holidays

| Expression | Date |
|------------|------|
| 元旦 | Jan 1 |
| 情人节 | Feb 14 |
| 劳动节, 五一 | May 1-5 |
| 儿童节 | Jun 1 |
| 国庆, 国庆节 | Oct 1-7 |
| 圣诞, 圣诞节 | Dec 25 |
| 清明, 清明节 | Apr 4-5 |

### Lunar Holidays

| Expression | Lunar Date |
|------------|------------|
| 春节, 过年 | 1st month, 1st day |
| 除夕, 年三十 | 12th month, 30th day |
| 元宵, 元宵节 | 1st month, 15th day |
| 端午, 端午节 | 5th month, 5th day |
| 七夕, 七夕节 | 7th month, 7th day |
| 中秋, 中秋节 | 8th month, 15th day |
| 重阳, 重阳节 | 9th month, 9th day |

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/weiyilan/mcp-chinese-time.git
cd mcp-chinese-time

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Lunar calendar conversion powered by [zhdate](https://github.com/CutePandaSh/zhdate)
