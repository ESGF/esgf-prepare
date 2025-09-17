"""
Unit tests for multihash functionality.

Tests the multihash implementation used for file checksums
in the esgmapfile component.
"""

import tempfile
import os
import pytest

from esgprep._utils.checksum import multihash_hex, checksum, is_multihash_algo, MULTIHASH_ALGOS


class TestMultihash:
    """Test class for multihash functionality."""

    def test_multihash_algorithms(self):
        """Test that all multihash algorithms work."""
        test_data = b"Hello, world!"

        for algo_name in MULTIHASH_ALGOS.keys():
            result = multihash_hex(test_data, algo_name)
            assert isinstance(result, str)
            assert len(result) > 0
            # Multihash should be hex string
            assert all(c in '0123456789abcdef' for c in result.lower())

    def test_unsupported_algorithm(self):
        """Test that unsupported algorithms raise ValueError."""
        test_data = b"test"

        with pytest.raises(ValueError):
            multihash_hex(test_data, "unsupported-algo")

    def test_is_multihash_algo(self):
        """Test algorithm detection function."""
        # Multihash algorithms
        assert is_multihash_algo('sha2-256') == True
        assert is_multihash_algo('sha2-512') == True
        assert is_multihash_algo('sha3-256') == True
        assert is_multihash_algo('sha1') == True  # sha1 is both standard and multihash

        # Standard-only algorithms (not in multihash)
        assert is_multihash_algo('sha256') == False
        assert is_multihash_algo('md5') == False
        assert is_multihash_algo('blake2b') == False

    def test_file_checksum_multihash(self):
        """Test file checksum computation with multihash."""
        test_data = b"Test file content for multihash"

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            f.write(test_data)
            temp_file_path = f.name

        try:
            # Test regular checksum
            regular_checksum = checksum(temp_file_path, 'sha256')
            assert isinstance(regular_checksum, str)
            assert len(regular_checksum) == 64  # SHA256 hex length

            # Test multihash checksum
            multihash_checksum = checksum(temp_file_path, 'sha2-256')
            assert isinstance(multihash_checksum, str)
            assert len(multihash_checksum) > 64  # Multihash includes varint encoding

            # They should be different (multihash includes varint encoding)
            assert regular_checksum != multihash_checksum

        finally:
            os.unlink(temp_file_path)

    def test_multihash_consistency(self):
        """Test that multihash produces consistent results."""
        test_data = b"Consistency test data"

        # Same data should produce same multihash
        result1 = multihash_hex(test_data, 'sha2-256')
        result2 = multihash_hex(test_data, 'sha2-256')
        assert result1 == result2

        # Different data should produce different multihash
        different_data = b"Different test data"
        result3 = multihash_hex(different_data, 'sha2-256')
        assert result1 != result3

    def test_multihash_different_algorithms(self):
        """Test that different algorithms produce different results."""
        test_data = b"Algorithm comparison test"

        results = {}
        for algo in MULTIHASH_ALGOS.keys():
            results[algo] = multihash_hex(test_data, algo)

        # All results should be different
        unique_results = set(results.values())
        assert len(unique_results) == len(results)

    def test_include_filename_option(self):
        """Test the include_filename option works with multihash."""
        test_data = b"Filename test content"

        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.test') as f:
            f.write(test_data)
            temp_file_path = f.name

        try:
            # Without filename
            checksum_without = checksum(temp_file_path, 'sha2-256', include_filename=False)

            # With filename
            checksum_with = checksum(temp_file_path, 'sha2-256', include_filename=True)

            # Should be different
            assert checksum_without != checksum_with

        finally:
            os.unlink(temp_file_path)

    def test_multihash_empty_data(self):
        """Test multihash with empty data."""
        empty_data = b""

        result = multihash_hex(empty_data, 'sha2-256')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_multihash_large_data(self):
        """Test multihash with larger data."""
        # Create 1MB of test data
        large_data = b"x" * (1024 * 1024)

        result = multihash_hex(large_data, 'sha2-256')
        assert isinstance(result, str)
        assert len(result) > 0