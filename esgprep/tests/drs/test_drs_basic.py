"""
Test basic DrsProcessor functionality.
"""

import pytest
from pathlib import Path

from esgprep.drs.make import DrsProcessor
from esgprep.tests.drs.test_utils import PROJECT_ID, VERSION_STR, clean_directory, create_files_different_models
from esgprep.tests.drs.post_test_folder import Post_Test_Folder


def test_check_drs_processor_availability():
    """Test if DrsProcessor class is available and can be instantiated."""
    try:
        processor = DrsProcessor(root_dir=Path("/tmp"))
        assert processor is not None, "DrsProcessor should be instantiated"
    except Exception as e:
        pytest.fail(f"Failed to instantiate DrsProcessor: {str(e)}")


def test_basic_drs_processor_list(test_setup):
    """Test basic DrsProcessor functionality for listing files."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # Create DrsProcessor
    processor = DrsProcessor(root_dir=root_dir, mode="symlink", version=VERSION_STR)

    # Find NetCDF files
    nc_files = list(incoming_dir.glob("**/*.nc"))
    assert len(nc_files) > 0, "No NetCDF files found in test directory"

    # Process each file
    results = []
    for file_path in nc_files:
        result = processor.process_file(file_path)
        results.append(result)
        print(result)

    # Check results
    assert all(r.success for r in results), "Not all files were processed successfully"

    # Check that datasets were created
    assert len(processor.datasets) > 0, "No datasets were created"

    # Print dataset information for debug
    for dataset_id, dataset in processor.datasets.items():
        print(f"Dataset: {dataset_id}")
        print(f"  Versions: {[v.version_id for v in dataset.versions]}")
        for version in dataset.versions:
            print(f"  Files in {version.version_id}: {len(version.files)}")


def test_drs_processor_tree(test_setup):
    """Test DrsProcessor functionality for generating the DRS tree."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # Create DrsProcessor
    processor = DrsProcessor(root_dir=root_dir, mode="symlink", version=VERSION_STR)

    # Process all files in directory
    results = list(processor.process_directory(incoming_dir))

    # Check results
    assert all(r.success for r in results), "Not all files were processed successfully"

    # Collect all operations
    operations = []
    for result in results:
        operations.extend(result.operations)

    # Print operations for debug
    print(f"Total operations: {len(operations)}")
    for i, op in enumerate(operations[:5]):  # Print first 5 for debug
        print(
            f"Operation {i + 1}: {op.operation_type} from {op.source} to {op.destination}"
        )

    # Check that operations include creating directories and adding files
    assert any(
        op.destination and "cmip6" in str(op.destination).lower() for op in operations
    ), "No operations create CMIP6 directory structure"
