"""
Test DrsProcessor version updates.
"""

import tempfile
import shutil
from pathlib import Path

from esgprep.drs.make import DrsProcessor
from esgprep.tests.drs.test_utils import PROJECT_ID, clean_directory, create_version_specific_files, VALID_MODELS
from esgprep.tests.drs.post_test_folder import Post_Test_Folder


def test_drs_processor_version_update(test_setup):
    """Test DrsProcessor with version update and verify with Post_Test_Folder."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # First version
    first_version = "v20250401"
    second_version = "v20250402"

    # Create temporary directories for storing files between test stages
    version_dirs = {
        "v1": Path(tempfile.mkdtemp(prefix="esgdrs_test_v1_")),
        "v2": Path(tempfile.mkdtemp(prefix="esgdrs_test_v2_"))
    }

    # Create files for both versions using the specialized function with valid model
    first_version_files, second_version_files = create_version_specific_files(
        incoming_dir, version_dirs, model_id=VALID_MODELS[0]
    )

    # Copy the first version files to the incoming directory
    clean_directory(incoming_dir)
    for i, file_path in enumerate(first_version_files):
        subfolder = incoming_dir / f"subfolder_{i}"
        subfolder.mkdir(exist_ok=True, parents=True)
        shutil.copy2(file_path, subfolder / file_path.name)

    # Create DrsProcessor for first version
    processor1 = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="copy", version=first_version
    )

    # Process all files in directory for first version
    results1 = list(processor1.process_directory(incoming_dir))

    # Check that all files were processed successfully with valid DRS paths
    for result in results1:
        assert result.success, f"DRS generation failed for {result.input_file.source_path} with error: {result.error_message}"
        assert result.input_file.drs_path is not None, f"DRS path not generated for {result.input_file.source_path}"

    # Execute operations for first version
    operations1 = []
    for result in results1:
        operations1.extend(result.operations)
    processor1.execute_operations(operations1)

    # Now prepare the incoming directory with a mix of files from both versions:
    # 1. First file from version 1 (unchanged)
    # 2. Second file from version 2 (changed)
    # 3. Third file from version 1 (unchanged)
    clean_directory(incoming_dir)

    # Create subdirectories for each file
    for i in range(3):
        subdir = incoming_dir / f"subfolder_{i}"
        subdir.mkdir(exist_ok=True, parents=True)

    # Copy files with appropriate version data
    # Copy first file (index 0) from version 1
    shutil.copy2(
        first_version_files[0],
        incoming_dir / f"subfolder_0" / first_version_files[0].name
    )

    # Copy second file (index 1) from version 2
    shutil.copy2(
        second_version_files[1],
        incoming_dir / f"subfolder_1" / second_version_files[1].name
    )

    # Copy third file (index 2) from version 1
    shutil.copy2(
        first_version_files[2],
        incoming_dir / f"subfolder_2" / first_version_files[2].name
    )

    # Create DrsProcessor for second version
    processor2 = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="copy", version=second_version
    )

    # Process all files in directory for second version
    results2 = list(processor2.process_directory(incoming_dir))

    # Check that all files for second version were processed successfully with valid DRS paths
    for result in results2:
        assert result.success, f"DRS generation failed for {result.input_file.source_path} with error: {result.error_message}"
        assert result.input_file.drs_path is not None, f"DRS path not generated for {result.input_file.source_path}"

    # Execute operations for second version
    operations2 = []
    for result in results2:
        operations2.extend(result.operations)
    processor2.execute_operations(operations2)

    # Check that both versions exist
    first_version_files_result = list(root_dir.glob(f"**/{first_version}/**/*.nc"))
    second_version_files_result = list(root_dir.glob(f"**/{second_version}/**/*.nc"))

    assert len(first_version_files_result) > 0, "First version files not found"
    assert len(second_version_files_result) > 0, "Second version files not found"
    assert len(second_version_files_result) == len(first_version_files_result), (
        "Second version should have the same number of files"
    )

    # Use Post_Test_Folder to verify directory structure after update
    # Find dataset folders (those containing version folders)
    dataset_dirs = []
    for path in root_dir.glob(f"**/{second_version[1:]}"):
        if path.is_dir() and path.name.isdigit():
            # The parent directory is a dataset directory
            dataset_dirs.append(path.parent)

    # Test each dataset directory structure
    for dataset_dir in dataset_dirs:
        print(f"Testing dataset directory structure after version update: {dataset_dir}")
        test_folder = Post_Test_Folder(dataset_dir)

        # Test the directory structure using Post_Test_Folder
        test_folder.test()

        # Verify specifically that both versions exist in the folder
        version_dirs_result = list(dataset_dir.glob("v*"))
        version_names = [d.name for d in version_dirs_result]
        print(f"Found version directories: {version_names}")
        assert first_version in version_names, f"First version {first_version} not found in {version_names}"
        assert second_version in version_names, f"Second version {second_version} not found in {version_names}"

    # Clean up temporary directories
    shutil.rmtree(version_dirs["v1"], ignore_errors=True)
    shutil.rmtree(version_dirs["v2"], ignore_errors=True)
