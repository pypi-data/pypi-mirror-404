import io
import pytest

from strip_bom import strip_bom_stream


class TestStripBomStream:
    """Tests for strip_bom_stream() function."""

    def test_strip_bom_from_stream_with_bom(self):
        """Test stripping BOM from BytesIO stream with BOM."""
        stream = io.BytesIO(b'\xef\xbb\xbfunicorn')
        chunks = list(strip_bom_stream(stream))
        result = b''.join(chunks)
        assert result == b'unicorn'

    def test_strip_bom_from_stream_without_bom(self):
        """Test stream without BOM remains unchanged."""
        stream = io.BytesIO(b'unicorn')
        chunks = list(strip_bom_stream(stream))
        result = b''.join(chunks)
        assert result == b'unicorn'

    def test_strip_bom_from_empty_stream(self):
        """Test empty stream handling."""
        stream = io.BytesIO(b'')
        chunks = list(strip_bom_stream(stream))
        assert chunks == []

    def test_strip_bom_from_stream_with_only_bom(self):
        """Test stream containing only BOM."""
        stream = io.BytesIO(b'\xef\xbb\xbf')
        chunks = list(strip_bom_stream(stream))
        result = b''.join(chunks)
        assert result == b''

    def test_strip_bom_stream_with_minimal_chunk_size(self):
        """Test stream with chunk_size=1 (byte-by-byte reading)."""
        content = b'\xef\xbb\xbfHello'
        stream = io.BytesIO(content)
        result = b''.join(strip_bom_stream(stream, chunk_size=1))
        assert result == b'Hello'

    def test_strip_bom_raises_type_error_for_non_file_like(self):
        """Test that non-file-like input raises TypeError."""
        with pytest.raises(TypeError, match='Expected a file-like object'):
            strip_bom_stream('not a stream')
        
        with pytest.raises(TypeError, match='Expected a file-like object'):
            strip_bom_stream(123)
        
        with pytest.raises(TypeError, match='Expected a file-like object'):
            strip_bom_stream(None)

    def test_strip_bom_stream_with_closed_stream(self):
        """Test behavior when stream is already closed."""
        stream = io.BytesIO(b'\xef\xbb\xbfHello')
        stream.close()
        with pytest.raises(ValueError):
            list(strip_bom_stream(stream))

    def test_strip_bom_stream_early_termination(self):
        """Test that generator can be safely terminated early."""
        content = b'\xef\xbb\xbf' + b'x' * 10000
        stream = io.BytesIO(content)
        gen = strip_bom_stream(stream)
        first_chunk = next(gen)
        gen.close()  # Should not raise
