"""
Global pytest configuration and fixtures for the esgf-prepare test suite.
"""

import tempfile
import shutil
from pathlib import Path
import pytest

from tests.fixtures.generators import clean_directory


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test outputs."""
    tmp_path = Path(tempfile.mkdtemp(prefix="esgf_test_"))
    yield tmp_path
    # Cleanup
    if tmp_path.exists():
        shutil.rmtree(tmp_path)


@pytest.fixture
def test_data_dir():
    """Provide the path to test data fixtures."""
    return Path(__file__).parent / "fixtures" / "sample_data"


@pytest.fixture
def real_data_dir():
    """Provide the path to real test data."""
    return Path(__file__).parent / "fixtures" / "real_data"


@pytest.fixture
def clean_tmp_dir(tmp_dir):
    """Provide a clean temporary directory that gets cleaned after each test."""
    clean_directory(tmp_dir)
    yield tmp_dir
    clean_directory(tmp_dir)


@pytest.fixture
def drs_test_structure(tmp_dir):
    """Create a basic DRS directory structure for testing."""
    drs_root = tmp_dir / "drs_root"
    incoming = tmp_dir / "incoming"

    # Create directories
    drs_root.mkdir(parents=True)
    incoming.mkdir(parents=True)

    return {
        "root": drs_root,
        "incoming": incoming,
        "tmp_dir": tmp_dir
    }


@pytest.fixture(scope="session")
def project_root():
    """Provide the project root directory."""
    return Path(__file__).parent.parent


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "skip_this: marks tests to be skipped"
    )