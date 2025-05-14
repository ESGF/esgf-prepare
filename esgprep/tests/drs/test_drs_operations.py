"""
Test execution of DRS operations.
"""

import os
from pathlib import Path

from esgprep.drs.make import DrsProcessor
from esgprep.tests.drs.test_utils import PROJECT_ID, VERSION_STR, create_files_different_variables
from esgprep.tests.drs.post_test_folder import Post_Test_Folder


def test_drs_processor_execute_operations(test_setup):
    """Test DrsProcessor execution of operations using post_test_folder assertions."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # Create DrsProcessor
    processor = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="symlink", version=VERSION_STR
    )

    # Process all files in directory
    results = list(processor.process_directory(incoming_dir))

    # Collect all operations
    operations = []
    for result in results:
        operations.extend(result.operations)

    # Execute operations
    success = processor.execute_operations(operations)
    assert success, "Execution of operations failed"

    # Check that files were created in root_dir
    project_dir = root_dir / PROJECT_ID.upper()
    assert project_dir.exists(), f"Project directory not created: {project_dir}"

    # Find all created files
    created_files = list(root_dir.glob(f"**/{VERSION_STR}/**/*.nc"))
    print(f"Found {len(created_files)} created files:")
    for file in created_files[:5]:  # Print first 5 for debug
        print(f"  {file}")

    assert len(created_files) > 0, "No files were created"

    # Use Post_Test_Folder to verify directory structure
    # Find dataset folders (those containing version folders)
    dataset_dirs = []
    for path in root_dir.glob(f"**/{VERSION_STR[1:]}"):
        if path.is_dir() and path.name.isdigit():
            # The parent directory is a dataset directory
            dataset_dirs.append(path.parent)

    # Test each dataset directory structure
    for dataset_dir in dataset_dirs:
        print(f"Testing dataset directory structure: {dataset_dir}")
        test_folder = Post_Test_Folder(dataset_dir)
        test_folder.test()  # This will assert the correct structure


def test_drs_processor_upgrade_symlink(test_setup):
    """Test DrsProcessor with symlink mode and verify with Post_Test_Folder."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # Create DrsProcessor with symlink mode
    processor = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="symlink", version=VERSION_STR
    )

    # Process all files in directory
    results = list(processor.process_directory(incoming_dir))

    # Collect all operations
    operations = []
    for result in results:
        operations.extend(result.operations)

    # Execute operations
    success = processor.execute_operations(operations)
    assert success, "Execution of operations failed"

    # Check that symlinks were created
    symlinks = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.is_symlink():
                symlinks.append(file_path)

    print(f"Found {len(symlinks)} symlinks:")
    for symlink in symlinks[:5]:  # Print first 5 for debug
        print(f"  {symlink} -> {symlink.resolve()}")

    assert len(symlinks) > 0, "No symlinks were created"

    # Use Post_Test_Folder to verify directory structure
    # Find dataset folders (those containing version folders)
    dataset_dirs = []
    for path in root_dir.glob(f"**/{VERSION_STR[1:]}"):
        if path.is_dir() and path.name.isdigit():
            # The parent directory is a dataset directory
            dataset_dirs.append(path.parent)

    # Test each dataset directory structure
    for dataset_dir in dataset_dirs:
        print(f"Testing dataset directory structure: {dataset_dir}")
        test_folder = Post_Test_Folder(dataset_dir)

        # Verify specific symlink-related assertions
        assert test_folder.exists(), "Dataset directory does not exist"
        assert test_folder.contains_at_least_the_3_folders(), "Missing required folders"
        assert test_folder.is_there_symlink_between_v_and_d(), "Symlink from version to files is missing"
        assert test_folder.is_there_symlink_between_latest_and_latest_version(), "Latest symlink is incorrect"
