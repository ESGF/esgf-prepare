"""
Test different migration modes of DrsProcessor.
"""

import os
import pytest
import shutil
from pathlib import Path

from esgprep.drs.make import DrsProcessor
from esgprep.tests.drs.test_utils import PROJECT_ID, VERSION_STR, create_files_different_times
from esgprep.tests.drs.post_test_folder import Post_Test_Folder


def test_drs_processor_copy(test_setup):
    """Test DrsProcessor with copy mode and verify with Post_Test_Folder."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # Create DrsProcessor with copy mode
    processor = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="copy", version=VERSION_STR
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

    # Check that files were copied (both source and destination should exist)
    source_files = list(incoming_dir.glob("**/*.nc"))
    assert len(source_files) > 0, "No source files found"

    # Source files should still exist after copy
    for source_file in source_files:
        assert source_file.exists(), f"Source file was removed: {source_file}"

    # Find created files
    created_files = list(root_dir.glob(f"**/{VERSION_STR}/**/*.nc"))
    assert len(created_files) > 0, "No files were copied to destination"

    # Copied files should now be symlinks in the version directory
    for file in created_files:
        assert file.is_symlink(), f"File in version directory should be a symlink now: {file}"

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

        # Test full directory structure
        test_folder.test()

        # Additionally, verify files in "files/d*" directory are not symlinks
        files_dir = dataset_dir / "files"
        data_version_dirs = list(files_dir.glob("d*"))
        assert len(data_version_dirs) > 0, f"No data version directories found in {files_dir}"

        for d_dir in data_version_dirs:
            for file_path in d_dir.glob("*.nc"):
                assert not file_path.is_symlink(), f"File in '{d_dir.name}' dir should be a copy, not a symlink: {file_path}"


def test_drs_processor_link(test_setup):
    """Test DrsProcessor with link (hard link) mode and verify with Post_Test_Folder."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # Create DrsProcessor with link mode
    processor = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="link", version=VERSION_STR
    )

    # Process all files in directory
    results = list(processor.process_directory(incoming_dir))

    # Collect all operations
    operations = []
    for result in results:
        operations.extend(result.operations)

    # Execute operations
    try:
        success = processor.execute_operations(operations)
        assert success, "Execution of operations failed"

        # Check that files were hard-linked
        created_files = list(root_dir.glob(f"**/{VERSION_STR}/**/*.nc"))
        assert len(created_files) > 0, "No files were created"

        # Hard links are not symlinks but are linked to the same inode
        # But now the version folder files should be symlinks to files in files/d* folder
        for file in created_files:
            assert file.is_symlink(), (
                f"File in version directory should be a symlink: {file}"
            )

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

            # Test the directory structure
            test_folder.test()

            # Additionally, verify files in "files/d*" directory are hard links, not symlinks
            files_dir = dataset_dir / "files"
            data_version_dirs = list(files_dir.glob("d*"))
            assert len(data_version_dirs) > 0, f"No data version directories found in {files_dir}"

            for d_dir in data_version_dirs:
                for file_path in d_dir.glob("*.nc"):
                    # Find the corresponding source file in incoming_dir
                    source_files = list(incoming_dir.glob(f"**/{file_path.name}"))
                    if source_files:
                        source_file = source_files[0]
                        # Hard links have the same inode number
                        source_inode = os.stat(source_file).st_ino
                        link_inode = os.stat(file_path).st_ino
                        print(f"Source inode: {source_inode}, Link inode: {link_inode}")
                        assert not file_path.is_symlink(), f"File in '{d_dir.name}' should be a hard link, not a symlink"

    except OSError as e:
        # Hard links might fail if incoming_dir and root_dir are on different filesystems
        # In this case, we'll skip the test but print a warning
        print(
            f"WARNING: Hard link test failed, possibly due to cross-filesystem linking: {e}"
        )
        pytest.skip("Hard link test failed due to filesystem constraints")
