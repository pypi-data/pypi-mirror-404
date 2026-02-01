from typing import Union, BinaryIO, Iterator

# UTF-8 BOM bytes: 0xEF 0xBB 0xBF
UTF8_BOM = b'\xef\xbb\xbf'
# UTF-8 BOM character: U+FEFF
UTF8_BOM_CHAR = '\ufeff'


def strip_bom(string: str) -> str:
    """
    Strip UTF-8 byte order mark (BOM) from a string.
    
    Args:
        string: Input string that may contain a BOM
        
    Returns:
        String with BOM removed if present, otherwise the original string
        
    Raises:
        TypeError: If input is not a string
        
    Example:
        >>> strip_bom('\ufeffunicorn')
        'unicorn'
    """
    if not isinstance(string, str):
        raise TypeError(f'Expected a string, got {type(string).__name__}')
    
    # Catches EFBBBF (UTF-8 BOM) because when a UTF-8 string with BOM
    # is read, the BOM is represented as the character U+FEFF
    if string and string[0] == UTF8_BOM_CHAR:
        return string[1:]
    
    return string


def _is_utf8(byte_array: bytes) -> bool:
    """
    Check if a byte array is valid UTF-8 encoded.
    
    Args:
        byte_array: Bytes to check
        
    Returns:
        True if the bytes are valid UTF-8, False otherwise
    """
    try:
        byte_array.decode('utf-8', errors='strict')
        return True
    except UnicodeDecodeError:
        return False


def strip_bom_buffer(byte_array: Union[bytes, bytearray]) -> bytes:
    """
    Strip UTF-8 byte order mark (BOM) from a byte array.
    
    Only strips the BOM if the buffer is actually valid UTF-8 encoded.
    
    Args:
        byte_array: Input bytes that may contain a UTF-8 BOM (0xEF 0xBB 0xBF)
        
    Returns:
        Bytes with BOM removed if present and valid UTF-8, otherwise the original bytes
        
    Raises:
        TypeError: If input is not bytes or bytearray
        
    Example:
        >>> strip_bom_buffer(b'\\xef\\xbb\\xbfunicorn')
        b'unicorn'
    """
    if not isinstance(byte_array, (bytes, bytearray)):
        raise TypeError(f'Expected bytes or bytearray, got {type(byte_array).__name__}')
    
    # Convert bytearray to bytes for consistency
    if isinstance(byte_array, bytearray):
        byte_array = bytes(byte_array)
    
    # Check for UTF-8 BOM: 0xEF 0xBB 0xBF
    if len(byte_array) >= len(UTF8_BOM) and byte_array[:len(UTF8_BOM)] == UTF8_BOM:
        # Only strip if the buffer is actually valid UTF-8
        if _is_utf8(byte_array):
            return byte_array[len(UTF8_BOM):]
    
    return byte_array


def strip_bom_stream(file_like: BinaryIO, chunk_size: int = 8192) -> Iterator[bytes]:
    """
    Strip UTF-8 byte order mark (BOM) from a stream/file-like object.
    
    Reads the first chunk using chunk_size (at least 3 bytes to check for BOM),
    checks for BOM, strips it if present and the data is valid UTF-8,
    then yields all remaining data in chunks of chunk_size.
    
    Args:
        file_like: File-like object opened in binary mode
        chunk_size: Size of chunks to read (default: 8192). The first chunk will
                   be at least this size (or 3 bytes, whichever is larger).
        
    Yields:
        Bytes chunks with BOM removed from the first chunk
        
    Raises:
        TypeError: If input is not a file-like object
        
    Example:
        >>> with open('file.txt', 'rb') as f:
        ...     for chunk in strip_bom_stream(f):
        ...         print(chunk)
    """
    if not hasattr(file_like, 'read'):
        raise TypeError(f'Expected a file-like object, got {type(file_like).__name__}')
    
    # Generator function that processes the stream
    def _strip_bom_stream_generator():
        # Read first chunk (at least enough bytes to check for BOM, use chunk_size for consistency)
        min_read_size = max(len(UTF8_BOM), chunk_size)
        first_chunk = file_like.read(min_read_size)
        
        if not first_chunk:
            return
        
        # Process first chunk with strip_bom_buffer to handle BOM removal
        processed_first = strip_bom_buffer(first_chunk)
        
        # Yield processed first chunk (BOM removed if it was present)
        if processed_first:
            yield processed_first
        
        # Yield the rest of the file in chunks
        while True:
            chunk = file_like.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    return _strip_bom_stream_generator()


def strip_bom_file(file_path: str, mode: str = 'r') -> Union[str, bytes]:
    """
    Convenience function to read a file and strip BOM.
    
    Args:
        file_path: Path to the file
        mode: File mode ('r' or 'rt' for text, 'rb' for binary)
        
    Returns:
        File contents with BOM removed (string if mode='r' or 'rt', bytes if mode='rb')
        
    Raises:
        ValueError: If mode is not 'r', 'rt', or 'rb'
        FileNotFoundError: If the file does not exist
        
    Example:
        >>> content = strip_bom_file('file.txt', 'r')
        >>> print(content)
        'unicorn'
    """
    if mode in ('r', 'rt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return strip_bom(content)
    elif mode == 'rb':
        with open(file_path, 'rb') as f:
            content = f.read()
            return strip_bom_buffer(content)
    else:
        raise ValueError(f"Mode must be 'r', 'rt', or 'rb', got '{mode}'")
