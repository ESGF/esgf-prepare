"""
Pytest fixtures specific to test data generation and validation.
"""

import pytest
from pathlib import Path

from .generators import (
    create_files_different_variables,
    create_files_different_times,
    create_files_different_models,
    create_files_different_versions,
    create_files_different_members,
)


@pytest.fixture
def netcdf_generator():
    """Provide access to NetCDF file generation functions."""
    return {
        "different_variables": create_files_different_variables,
        "different_times": create_files_different_times,
        "different_models": create_files_different_models,
        "different_versions": create_files_different_versions,
        "different_members": create_files_different_members,
    }


@pytest.fixture
def sample_netcdf_files(tmp_dir, netcdf_generator):
    """Create a set of sample NetCDF files for testing."""
    incoming_dir = tmp_dir / "sample_incoming"
    incoming_dir.mkdir(parents=True)

    # Create files with different variables
    files = netcdf_generator["different_variables"](
        incoming_dir, count=3, time_range=(1, 10)
    )

    return {
        "directory": incoming_dir,
        "files": files,
        "count": len(files)
    }