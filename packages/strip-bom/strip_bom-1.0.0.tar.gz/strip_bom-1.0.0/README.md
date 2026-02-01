# Strip BOM


[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/ysskrishna/strip-bom/blob/main/LICENSE)
![Tests](https://github.com/ysskrishna/strip-bom/actions/workflows/test.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/strip-bom)](https://pypi.org/project/strip-bom/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/strip-bom?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/strip-bom)

Strip UTF-8 byte order mark (BOM) from strings, bytes, streams, and files. Inspired by the popular [strip-bom](https://github.com/sindresorhus/strip-bom) npm package.

## Features

- **Multiple input types**: Strip BOM from strings, bytes, bytearrays, streams, and files
- **Smart validation**: Validates UTF-8 encoding before processing buffers
- **Memory efficient**: Handles large files and streams without loading everything into memory
- **Zero dependencies**: Lightweight with no external dependencies
- **Type safe**: Full type hints for excellent IDE support
- **Robust**: Graceful error handling and Unicode support (emojis, CJK characters, etc.)

## Why Strip BOM?

The [UTF-8 Byte Order Mark (BOM)](https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8) can cause issues when:

- ❌ Processing files from different sources (some have BOM, others don't)
- ❌ Comparing strings that should be identical but differ only by BOM
- ❌ Working with APIs that don't expect BOM characters
- ❌ Parsing JSON, CSV, or other structured data formats

> **Note**: The [Unicode Standard](https://www.unicode.org/faq/utf_bom#bom5) permits BOM in UTF-8 but doesn't require or recommend it, since byte order is irrelevant for UTF-8.


## Installation

```bash
pip install strip-bom
```

## Usage Examples

### Strings

```python
from strip_bom import strip_bom

text_with_bom = '\ufeffunicorn'
clean_text = strip_bom(text_with_bom)
print(clean_text)  # 'unicorn'

# Text without BOM remains unchanged
normal_text = 'Hello World'
print(strip_bom(normal_text))  # 'Hello World'
```

### Bytes and Buffers

```python
from strip_bom import strip_bom_buffer

bytes_with_bom = b'\xef\xbb\xbfunicorn'
clean_bytes = strip_bom_buffer(bytes_with_bom)
print(clean_bytes)  # b'unicorn'

# Invalid UTF-8 is left unchanged (safety first!)
invalid_utf8 = b'\xef\xbb\xbf\xff\xfe'
result = strip_bom_buffer(invalid_utf8)
print(result == invalid_utf8)  # True (no changes made)
```

### Streams (Memory Efficient)

```python
from strip_bom import strip_bom_stream
import io

# Process large streams without loading everything into memory
stream = io.BytesIO(b'\xef\xbb\xbfLarge file content here...')

# Process in chunks
for chunk in strip_bom_stream(stream, chunk_size=8192):
    # Process each chunk as needed
    print(chunk)

# Or get all content at once
stream.seek(0)
content = b''.join(strip_bom_stream(stream))
```

### Files

```python
from strip_bom import strip_bom_file

# Text mode (reads as UTF-8)
content = strip_bom_file('data.txt', mode='r')
print(f"File content: {content}")

# Binary mode
binary_content = strip_bom_file('data.txt', mode='rb')
print(f"Binary content: {binary_content}")
```

## API Reference

### `strip_bom(text: str) -> str`
Remove BOM from Unicode string.

### `strip_bom_buffer(buffer: Union[bytes, bytearray]) -> bytes`
Remove BOM from bytes/bytearray if valid UTF-8.

### `strip_bom_stream(stream: BinaryIO, chunk_size: int = 8192) -> Iterator[bytes]`
Remove BOM from binary stream, yielding chunks.

### `strip_bom_file(file_path: str, mode: str = 'r') -> Union[str, bytes]`
Remove BOM from file content. Mode can be `'r'`/`'rt'` for text or `'rb'` for binary.


## Learn More

- [W3C: The byte-order mark (BOM) in HTML](https://www.w3.org/International/questions/qa-byte-order-mark)
- [Unicode FAQ: UTF-8, UTF-16, UTF-32 & BOM](https://www.unicode.org/faq/utf_bom#bom5)
- [Wikipedia: Byte Order Mark](https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8)

## Acknowledgments

Inspired by [Sindre Sorhus](https://github.com/sindresorhus)'s [strip-bom](https://github.com/sindresorhus/strip-bom) npm package.

## Changelog

See [CHANGELOG.md](https://github.com/ysskrishna/strip-bom/blob/main/CHANGELOG.md) for a detailed list of changes and version history.

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/ysskrishna/strip-bom/blob/main/CONTRIBUTING.md) for details.

## Support

If you find this library helpful:

- ⭐ Star the repository
- 🐛 Report issues
- 🔀 Submit pull requests
- 💝 [Sponsor on GitHub](https://github.com/sponsors/ysskrishna)

## License

MIT © [Y. Siva Sai Krishna](https://github.com/ysskrishna) - see [LICENSE](https://github.com/ysskrishna/strip-bom/blob/main/LICENSE) file for details.

---

<p align="left">
  <a href="https://github.com/ysskrishna">Author's GitHub</a> •
  <a href="https://linkedin.com/in/ysskrishna">Author's LinkedIn</a> •
  <a href="https://github.com/ysskrishna/strip-bom/issues">Report Issues</a> •
  <a href="https://pypi.org/project/strip-bom/">Package on PyPI</a>
</p>