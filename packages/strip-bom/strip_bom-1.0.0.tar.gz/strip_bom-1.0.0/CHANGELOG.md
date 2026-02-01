# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0]

### Added
- Initial release of strip-bom Python package
- `strip_bom()` function to strip UTF-8 BOM from strings
- `strip_bom_buffer()` function to strip UTF-8 BOM from bytes/bytearray (only if valid UTF-8)
- `strip_bom_stream()` function to strip UTF-8 BOM from streams/file-like objects
- `strip_bom_file()` convenience function to read files and strip BOM
- UTF-8 validation before stripping BOM from buffers (prevents stripping BOM from invalid UTF-8)
- Support for both text and binary file modes
- Type hints for better IDE support and type checking
- Zero dependencies for minimal overhead
- Comprehensive test suite with unit tests covering all functions and edge cases
- Python 3.8+ compatibility

### Features
- Fast and reliable BOM stripping for strings, bytes, streams, and files
- Validates UTF-8 encoding before stripping BOM from buffers
- Handles large files and streams efficiently
- Graceful error handling for invalid inputs
- Supports Unicode characters including emojis and CJK characters

[1.0.0]: https://github.com/ysskrishna/strip-bom/releases/tag/v1.0.0
