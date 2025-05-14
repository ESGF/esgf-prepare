"""
Pytest fixtures for DRS testing.
"""

import pytest
from pathlib import Path

from esgprep.tests.drs.test_utils import clean_directory, create_files_different_models

# Get the repo root directory
REPO_ROOT = Path(__file__).parent.parent.absolute()
print(f"Using repository root: {REPO_ROOT}")

# Create a logs directory
LOG_DIR = REPO_ROOT / "tests" / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)
print(f"Logs will be saved to: {LOG_DIR}")


@pytest.fixture(scope="function")
def test_setup():
    """Create persistent directories for testing and sample NetCDF files."""
    # Create persistent directories for test
    test_dir = REPO_ROOT / "test_data"
    incoming_dir = test_dir / "incoming"
    root_dir = test_dir / "root"

    # Create directories if they don't exist
    incoming_dir.mkdir(parents=True, exist_ok=True)
    root_dir.mkdir(parents=True, exist_ok=True)

    # Clean directories before test
    clean_directory(incoming_dir)
    clean_directory(root_dir)

    # Create sample NetCDF files with proper attributes for testing
    create_files_different_models(incoming_dir)

    # Print directory paths for manual inspection
    print(f"Test incoming directory: {incoming_dir}")
    print(f"Test root directory: {root_dir}")

    # Yield the test directories
    yield {"incoming_dir": incoming_dir, "root_dir": root_dir}

    # Don't clean up after test to allow manual inspection
    # Comment out clean_directory(incoming_dir) and clean_directory(root_dir) if you need to keep files


@pytest.fixture(scope="session", autouse=True)
def clean_test_directories():
    """Clean test directories at the start of the test session."""
    # Define test directories
    test_dir = REPO_ROOT / "test_data"
    incoming_dir = test_dir / "incoming"
    root_dir = test_dir / "root"

    # Create directories if they don't exist
    test_dir.mkdir(parents=True, exist_ok=True)
    incoming_dir.mkdir(parents=True, exist_ok=True)
    root_dir.mkdir(parents=True, exist_ok=True)

    # Clean log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for log_file in LOG_DIR.glob("*"):
        if log_file.is_file():
            log_file.unlink()
    print(f"Cleaned log directory: {LOG_DIR}")

    # Clean test directories at the beginning
    clean_directory(incoming_dir)
    clean_directory(root_dir)

    # Yield control back to the tests
    yield
