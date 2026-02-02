# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-15

### Added

- Initial release
- `parse_time` MCP tool for parsing Chinese fuzzy time expressions
- Support for relative time expressions (昨天, 今天, 明天, N天前/后)
- Support for relative week expressions (本周, 上周, 下周, N周前/后)
- Support for relative month expressions (本月, 上个月, 下个月, N个月前/后)
- Support for time of day expressions (上午9点, 下午3点30分)
- Support for specific date expressions (2024年1月1日, 1月15号)
- Support for weekday expressions (周一, 上周三, 下周五)
- Support for time range expressions (昨天到今天, 上周一到周五)
- Support for solar holidays (国庆节, 劳动节, 元旦, etc.)
- Support for lunar holidays with zhdate conversion (春节, 中秋节, 端午节, etc.)
- Chinese number support (一, 二, 三, etc.)
- Configurable timezone support
- FastMCP 2.x based MCP server
- Comprehensive test suite
- Full documentation with usage examples
