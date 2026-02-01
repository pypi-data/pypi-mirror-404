import pytest

from strip_bom import strip_bom


class TestStripBom:
    """Tests for strip_bom() function."""

    def test_strip_bom_from_string_with_bom(self):
        """Test stripping BOM from string that has BOM."""
        text_with_bom = '\ufeffunicorn'
        result = strip_bom(text_with_bom)
        assert result == 'unicorn'
        assert result != text_with_bom

    def test_strip_bom_from_string_without_bom(self):
        """Test string without BOM remains unchanged."""
        text_no_bom = 'unicorn'
        result = strip_bom(text_no_bom)
        assert result == 'unicorn'
        assert result is text_no_bom  # Should return same object

    def test_strip_bom_from_empty_string(self):
        """Test empty string handling."""
        result = strip_bom('')
        assert result == ''

    def test_strip_bom_from_string_with_only_bom(self):
        """Test string containing only BOM."""
        result = strip_bom('\ufeff')
        assert result == ''

    def test_strip_bom_raises_type_error_for_non_string(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError, match='Expected a string'):
            strip_bom(b'bytes')
        
        with pytest.raises(TypeError, match='Expected a string'):
            strip_bom(123)
        
        with pytest.raises(TypeError, match='Expected a string'):
            strip_bom(None)
