# -*- coding: utf-8 -*-

"""
.. module:: esgprep._utils.checksum.py
   :platform: Unix
   :synopsis: Checksumming utilities.

.. moduleauthor:: Guillaume Levavasseur <glipsl@ipsl.fr>

"""

import hashlib
import os
import re

from esgprep._exceptions import InvalidChecksumType, ChecksumFail
from esgprep._utils.print import *

# Multihash support - implement varint encoding directly to avoid dependency

def _varint_encode(n: int) -> bytes:
    """
    Encode an integer as varint (variable-length integer encoding).
    
    Args:
        n: The integer to encode
        
    Returns:
        The varint-encoded bytes
    """
    result = bytearray()
    while n >= 0x80:
        result.append((n & 0x7F) | 0x80)
        n >>= 7
    result.append(n & 0x7F)
    return bytes(result)


# Map des algorithmes supportés pour multihash
MULTIHASH_ALGOS = {
    "sha1":       (0x11, "sha1"),
    "sha2-256":   (0x12, "sha256"),
    "sha2-512":   (0x13, "sha512"),
    "sha3-512":   (0x14, "sha3_512"),
    "sha3-256":   (0x16, "sha3_256"),
}


def multihash(data: bytes, algo: str) -> bytes:
    """
    Generate a multihash for the given data using the specified algorithm.
    
    Args:
        data: The data to hash
        algo: The multihash algorithm name (e.g., "sha2-256")
        
    Returns:
        The multihash as bytes (code + length + digest)
        
    Raises:
        ValueError: If the algorithm is not supported
    """
    if algo not in MULTIHASH_ALGOS:
        raise ValueError(f"Unsupported multihash algorithm: {algo}")

    code, hashlib_name = MULTIHASH_ALGOS[algo]
    h = hashlib.new(hashlib_name)
    h.update(data)
    digest = h.digest()

    code_bytes = _varint_encode(code)
    length_bytes = _varint_encode(len(digest))
    return code_bytes + length_bytes + digest


def multihash_hex(data: bytes, algo: str) -> str:
    """
    Generate a multihash for the given data and return it as a hex string.
    
    Args:
        data: The data to hash
        algo: The multihash algorithm name (e.g., "sha2-256")
        
    Returns:
        The multihash as a hexadecimal string
    """
    return multihash(data, algo).hex()


def _varint_decode(data: bytes, offset: int = 0) -> tuple[int, int]:
    """
    Decode a varint from bytes.
    
    Args:
        data: The bytes to decode from
        offset: Starting position in the bytes
        
    Returns:
        A tuple of (decoded_value, new_offset)
    """
    result = 0
    shift = 0
    pos = offset
    
    while pos < len(data):
        byte = data[pos]
        result |= (byte & 0x7F) << shift
        pos += 1
        if (byte & 0x80) == 0:
            break
        shift += 7
    
    return result, pos


def detect_multihash_algo(hash_hex: str) -> str:
    """
    Detect the multihash algorithm from a multihash hex string.
    
    Args:
        hash_hex: The multihash as a hexadecimal string
        
    Returns:
        The algorithm name (e.g., "sha2-256") or None if not a valid multihash
    """
    try:
        # Convert hex to bytes
        hash_bytes = bytes.fromhex(hash_hex)
        
        # Decode the algorithm code (first varint)
        code, offset = _varint_decode(hash_bytes, 0)
        
        # Find the algorithm by code
        for algo_name, (algo_code, _) in MULTIHASH_ALGOS.items():
            if algo_code == code:
                return algo_name
        
        return None
        
    except (ValueError, IndexError):
        return None


def is_multihash_algo(checksum_type: str) -> bool:
    """
    Check if a checksum type is a multihash algorithm.
    
    Args:
        checksum_type: The checksum type to check
        
    Returns:
        True if it's a multihash algorithm, False otherwise
    """
    return checksum_type in MULTIHASH_ALGOS


def checksum(ffp, checksum_type, include_filename=False, human_readable=True):
    """
    Computes a file checksum. Supports both standard hashlib algorithms and multihash algorithms.

    """
    try:
        # Get file size for progress indication
        file_size = os.path.getsize(ffp)
        show_progress = file_size > 1000 * 1024 * 1024  # Show progress for files > 1GB
        
        if show_progress:
            from esgprep._utils.print import Print
            Print.info(f"Computing {checksum_type} checksum for large file: {os.path.basename(ffp)} ({file_size / (1024*1024):.1f} MB)")
        
        # Check if this is a multihash algorithm
        if is_multihash_algo(checksum_type):
            # Handle multihash algorithms
            if show_progress:
                # For large files, read in chunks and show progress
                hash_data = bytearray()
                bytes_read = 0
                chunk_size = 64 * 1024  # 64KB chunks
                
                with open(ffp, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        hash_data.extend(chunk)
                        bytes_read += len(chunk)
                        
                        # Show progress every 1GB
                        if bytes_read % (1024 * 1024 * 1024) == 0:
                            progress_pct = int((bytes_read / file_size) * 100)
                            Print.info(f"  Progress: {progress_pct}%")
                
                if show_progress:
                    Print.info(f"  Converting data to bytes for hash calculation...")
                data = bytes(hash_data)
            else:
                # Read file data normally for smaller files
                with open(ffp, 'rb') as f:
                    data = f.read()
            
            # Include filename into the data if requested
            if include_filename:
                data += os.path.basename(ffp).encode()
            
            # Generate multihash
            if show_progress:
                Print.info(f"  Generating {checksum_type} multihash (this may take a while for large files)...")
            
            if human_readable:
                result = multihash_hex(data, checksum_type)
            else:
                result = multihash(data, checksum_type)
                
            if show_progress:
                Print.info(f"  Checksum completed: {result[:32]}...")
            
            return result
        
        else:
            # Handle standard hashlib algorithms
            # Get checksum client.
            hash_algo = getattr(hashlib, checksum_type)()

            # Checksumming file.
            with open(ffp, 'rb') as f:
                blocksize = os.stat(ffp).st_blksize
                bytes_read = 0
                
                for block in iter(lambda: f.read(blocksize), b''):
                    hash_algo.update(block)
                    bytes_read += len(block)
                    
                    # Show progress for large files every 1GB
                    if show_progress and bytes_read % (1024 * 1024 * 1024) == 0:
                        progress_pct = int((bytes_read / file_size) * 100)
                        Print.info(f"  Progress: {progress_pct}%")

            # Include filename into the checksum.
            if include_filename:
                hash_algo.update(os.path.basename(ffp).encode())

            if show_progress:
                Print.info(f"  Checksum completed")

            # Return human readable checksum.
            if human_readable:
                return hash_algo.hexdigest()
            else:
                return hash_algo.digest()

    # Catch checksum type error.
    except AttributeError:
        raise InvalidChecksumType(checksum_type)

    # Catch manual stop error.
    except KeyboardInterrupt:
        raise

    # Catch any other error.
    except Exception:
        raise ChecksumFail(ffp, checksum_type)


def get_checksum_pattern(checksum_type):
    """
    Builds a regular expression describing a checksum pattern.

    """
    # Handle multihash algorithms
    if is_multihash_algo(checksum_type):
        # Multihash patterns are variable length hex strings
        # They start with varint-encoded code and length, followed by the digest
        # For hex representation, this is quite variable, so we use a more flexible pattern
        return re.compile(r'^[0-9a-f]+$')
    
    else:
        # Handle standard hashlib algorithms
        # Get checksum client.
        hash_algo = getattr(hashlib, checksum_type)()

        # Get checksum length.
        checksum_length = len(hash_algo.hexdigest())

        # Return corresponding regex.
        return re.compile(f'^[0-9a-f]{{{checksum_length}}}$')


def get_checksum(ffp, checksum_type='sha256', checksums=None):
    """
    Global method to get file checksum:
    1. By computing the checksum directly.
    2. Through a list of checksums in a dictionary way {file: checksum}.

    """
    # Verify checksum dictionary.
    if checksums:

        # Verify file in dictionary keys.
        if ffp in checksums:

            # Verify checksum pattern.
            if re.match(get_checksum_pattern(checksum_type), checksums[ffp]):
                # Return pre-computed checksum.
                return checksums[ffp]

    # Return computed checksum.
    return checksum(ffp, checksum_type)
