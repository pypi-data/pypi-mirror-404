import tempfile
import pytest
from pathlib import Path

from strip_bom import strip_bom_file


class TestStripBomFile:
    """Tests for strip_bom_file() function."""

    def test_strip_bom_file_text_mode_with_bom(self):
        """Test reading file in text mode with BOM."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write('\ufeffunicorn')
            temp_path = f.name
        
        try:
            result = strip_bom_file(temp_path, 'r')
            assert result == 'unicorn'
        finally:
            Path(temp_path).unlink()

    def test_strip_bom_file_text_mode_without_bom(self):
        """Test reading file in text mode without BOM."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write('unicorn')
            temp_path = f.name
        
        try:
            result = strip_bom_file(temp_path, 'r')
            assert result == 'unicorn'
        finally:
            Path(temp_path).unlink()

    def test_strip_bom_file_binary_mode_with_bom(self):
        """Test reading file in binary mode with BOM."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'\xef\xbb\xbfunicorn')
            temp_path = f.name
        
        try:
            result = strip_bom_file(temp_path, 'rb')
            assert result == b'unicorn'
        finally:
            Path(temp_path).unlink()

    def test_strip_bom_file_binary_mode_without_bom(self):
        """Test reading file in binary mode without BOM."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(b'unicorn')
            temp_path = f.name
        
        try:
            result = strip_bom_file(temp_path, 'rb')
            assert result == b'unicorn'
        finally:
            Path(temp_path).unlink()

    def test_strip_bom_file_with_rt_mode(self):
        """Test reading file with 'rt' mode (same as 'r')."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write('\ufeffunicorn')
            temp_path = f.name
        
        try:
            result = strip_bom_file(temp_path, 'rt')
            assert result == 'unicorn'
        finally:
            Path(temp_path).unlink()

    def test_strip_bom_file_raises_value_error_for_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write('test')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Mode must be 'r', 'rt', or 'rb'"):
                strip_bom_file(temp_path, 'w')
            
            with pytest.raises(ValueError, match="Mode must be 'r', 'rt', or 'rb'"):
                strip_bom_file(temp_path, 'x')
        finally:
            Path(temp_path).unlink()

    def test_strip_bom_file_with_empty_file(self):
        """Test reading empty file."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            temp_path = f.name
        
        try:
            result = strip_bom_file(temp_path, 'r')
            assert result == ''
        finally:
            Path(temp_path).unlink()

    def test_strip_bom_file_with_utf8_fixture(self):
        """Test with UTF-8 fixture file containing BOM.
        
        Fixture file is located at tests/fixtures/fixture-utf8.
        """
        fixtures_dir = Path(__file__).parent / 'fixtures'
        utf8_fixture = fixtures_dir / 'fixture-utf8'
        
        # Test UTF-8 fixture: BOM should be stripped
        result_utf8 = strip_bom_file(str(utf8_fixture), 'rb')
        assert result_utf8 == b'Unicorn\n'

    def test_strip_bom_file_with_directory_path(self):
        """Test error handling when path is a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(IsADirectoryError):
                strip_bom_file(tmpdir)
