"""
Main entry point for running all DRS tests.
"""

if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "esgprep/tests/drs"])
