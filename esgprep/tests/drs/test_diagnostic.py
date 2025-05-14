"""
Diagnostic test for understanding DrsProcessor upgrade_from_latest behavior.
"""

import os
import tempfile
import shutil
from pathlib import Path

import pytest

from esgprep.drs.make import DrsProcessor
from esgprep.tests.drs.test_utils import (
    PROJECT_ID, clean_directory, _create_base_netcdf_file,
    VALID_MODELS, VALID_VARIABLES
)


def test_diagnostic_upgrade_from_latest(test_setup):
    """
    Diagnostic test to understand the exact behavior of upgrade_from_latest.
    This test creates files with clear names that include their time range and
    prints detailed information about the directory structure.
    """
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # First version
    first_version = "v20250401"
    second_version = "v20250402"

    # Create temporary directories for storing files between test stages
    temp_dir_v1 = Path(tempfile.mkdtemp(prefix="esgdrs_diag_v1_"))
    temp_dir_v2 = Path(tempfile.mkdtemp(prefix="esgdrs_diag_v2_"))

    # Use valid model and variables
    model_id = VALID_MODELS[0]  # Use first valid model
    time_ranges = [(1, 10), (10, 20), (20, 30)]

    # Create first version files with descriptive names
    print("\n=== Creating first version files ===")
    first_version_files = []
    variable_id = VALID_VARIABLES[0]  # Use same variable (tas) for all files
    for i, time_range in enumerate(time_ranges):
        subfolder = temp_dir_v1 / f"subfolder_{i}"
        subfolder.mkdir(exist_ok=True, parents=True)

        # Use same variable but different time ranges in the filename for easier identification
        filename = subfolder / f"{PROJECT_ID}_{model_id}_{variable_id}_time{time_range[0]}-{time_range[1]}.nc"
        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range, version=1
        )
        first_version_files.append(file_path)
        print(f"  Created file: {file_path.name} with time range {time_range[0]}-{time_range[1]}")

    # Copy the first version files to the incoming directory
    clean_directory(incoming_dir)
    print("\n=== Copying first version files to incoming directory ===")
    for i, file_path in enumerate(first_version_files):
        subfolder = incoming_dir / f"subfolder_{i}"
        subfolder.mkdir(exist_ok=True, parents=True)
        dest_path = subfolder / file_path.name
        shutil.copy2(file_path, dest_path)
        print(f"  Copied to: {dest_path}")

    # Create DrsProcessor for first version
    processor1 = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="copy", version=first_version
    )

    # Process files in directory for first version
    print("\n=== Processing first version files ===")
    results1 = list(processor1.process_directory(incoming_dir))
    print(f"  Processed {len(results1)} files")

    # Check that all files were processed successfully with valid DRS paths
    for result in results1:
        assert result.success, f"DRS generation failed for {result.input_file.source_path} with error: {result.error_message}"
        assert result.input_file.drs_path is not None, f"DRS path not generated for {result.input_file.source_path}"
        print(f"  Successfully generated DRS path: {result.input_file.drs_path.relative_to(root_dir)}")

    # Execute operations for first version
    operations1 = []
    for result in results1:
        operations1.extend(result.operations)
    processor1.execute_operations(operations1)

    # Create second version files with descriptive names
    print("\n=== Creating second version files ===")
    second_version_files = []
    # Use same variable for all files in version 2 as well
    for i, time_range in enumerate(time_ranges):
        subfolder = temp_dir_v2 / f"subfolder_{i}"
        subfolder.mkdir(exist_ok=True, parents=True)

        # Use same variable but different time ranges in the filename for easier identification
        filename = subfolder / f"{PROJECT_ID}_{model_id}_{variable_id}_time{time_range[0]}-{time_range[1]}_v2.nc"
        file_path = _create_base_netcdf_file(
            filename, model_id, variable_id, time_range, version=2
        )
        second_version_files.append(file_path)
        print(f"  Created file: {file_path.name} with time range {time_range[0]}-{time_range[1]}")

    # For upgrade_from_latest, only include the modified middle file
    clean_directory(incoming_dir)
    print("\n=== Preparing second version with only the modified file ===")

    # Create the subfolder for just the second file (index 1)
    subdir = incoming_dir / "subfolder_1"
    subdir.mkdir(exist_ok=True, parents=True)

    # Only copy the second file (index 1) from version 2 - only this one changed
    dest_path = subdir / second_version_files[1].name
    shutil.copy2(second_version_files[1], dest_path)
    print(f"  Copied modified file to: {dest_path}")

    # Create DrsProcessor for second version with upgrade_from_latest=True
    processor2 = DrsProcessor(
        root_dir=root_dir,
        project=PROJECT_ID,
        mode="copy",
        version=second_version,
        upgrade_from_latest=True,  # Use upgrade_from_latest mode
    )

    # Process the files in directory for second version
    print("\n=== Processing second version with upgrade_from_latest ===")
    results2 = list(processor2.process_directory(incoming_dir))
    print(f"  Processed {len(results2)} files in second version")

    # Check that all files were processed successfully with valid DRS paths
    for result in results2:
        assert result.success, f"DRS generation failed for {result.input_file.source_path} with error: {result.error_message}"
        assert result.input_file.drs_path is not None, f"DRS path not generated for {result.input_file.source_path}"
        print(f"  Successfully generated DRS path: {result.input_file.drs_path.relative_to(root_dir)}")

    # Execute operations for second version
    operations2 = []
    for result in results2:
        operations2.extend(result.operations)
    processor2.execute_operations(operations2)

    # Print the directory structure using os.walk
    print("\n=== Resulting directory structure ===")
    for root, dirs, files in os.walk(root_dir):
        level = root.replace(str(root_dir), '').count(os.sep)
        indent = ' ' * 4 * level
        root_name = os.path.basename(root)
        print(f"{indent}{root_name}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            file_path = Path(root) / f
            if file_path.is_symlink():
                target = Path(os.readlink(file_path))
                if not target.is_absolute():
                    # Calculate a relative path that's easier to read
                    target = Path(os.path.normpath(os.path.join(os.path.dirname(file_path), target)))
                print(f"{sub_indent}{f} -> {target.relative_to(root_dir)}")
            else:
                print(f"{sub_indent}{f}")

    # Find all vXXXXXXXX directories
    print("\n=== Version directories ===")
    version_dirs = {}
    for path in root_dir.glob("**"):
        if path.is_dir() and (path.name.startswith("v") and len(path.name) >= 9 and path.name[1:].isdigit()):
            # Group by parent directory
            parent = path.parent
            if parent not in version_dirs:
                version_dirs[parent] = []
            version_dirs[parent].append(path)

    # Count files in each version directory
    for parent, dirs in version_dirs.items():
        print(f"  Parent: {parent.relative_to(root_dir)}")
        for dir_path in sorted(dirs):
            files = list(dir_path.glob("*.nc"))
            print(f"    {dir_path.name}: {len(files)} files")
            for file_path in files:
                if file_path.is_symlink():
                    target = file_path.resolve().relative_to(root_dir)
                    print(f"      {file_path.name} -> {target}")
                else:
                    print(f"      {file_path.name}")

    # Find all dXXXXXXXX directories
    print("\n=== Data directories under files/ ===")
    data_dirs = {}
    for path in root_dir.glob("**/files"):
        if path.is_dir():
            parent = path.parent
            if parent not in data_dirs:
                data_dirs[parent] = []
            # Get d* directories
            for d_dir in path.glob("d*"):
                if d_dir.is_dir() and d_dir.name.startswith("d") and len(d_dir.name) >= 9 and d_dir.name[1:].isdigit():
                    data_dirs[parent].append(d_dir)

    # Count files in each data directory
    for parent, dirs in data_dirs.items():
        print(f"  Parent: {parent.relative_to(root_dir)}")
        for dir_path in sorted(dirs):
            files = list(dir_path.glob("*.nc"))
            print(f"    {dir_path.name}: {len(files)} files")
            for file_path in files:
                print(f"      {file_path.name}")

    # Find all latest directories
    print("\n=== Latest directories ===")
    for path in root_dir.glob("**/latest"):
        if path.is_dir():
            if path.is_symlink():
                target = path.resolve().relative_to(root_dir)
                print(f"  {path.parent.relative_to(root_dir)}/latest -> {target}")
            else:
                print(f"  {path.parent.relative_to(root_dir)}/latest (not a symlink)")

            # List files in latest dir
            latest_files = list(path.glob("*.nc"))
            for file_path in latest_files:
                if file_path.is_symlink():
                    target = file_path.resolve().relative_to(root_dir)
                    print(f"    {file_path.name} -> {target}")
                else:
                    print(f"    {file_path.name}")

    # Count total files by version
    print("\n=== Total file counts ===")
    first_version_files = list(root_dir.glob(f"**/{first_version}/**/*.nc"))
    second_version_files = list(root_dir.glob(f"**/{second_version}/**/*.nc"))

    print(f"  Files in {first_version}: {len(first_version_files)}")
    print(f"  Files in {second_version}: {len(second_version_files)}")

    # Check if all expected files are in the second version
    second_version_filenames = [f.name for f in second_version_files]
    print(f"\n  Files in {second_version}:")
    for name in second_version_filenames:
        print(f"    {name}")

    # Important: Now we examine what's intended by the upgrade_from_latest option
    print("\n=== Analysis of upgrade_from_latest behavior ===")
    print("Based on the documentation:")
    print("  Method (a) - Default: All files must be provided, unchanged files are optimized")
    print("  Method (b) - With --upgrade-from-latest: Only modified files need to be provided")

    print("\nObservation: With upgrade_from_latest enabled, we only provided the second file")
    print(f"             but expected all files to appear in {second_version}.")
    print("\nPossible explanations:")
    print("1. The test expectation is incorrect: upgrade_from_latest is meant to only update")
    print("   the files that are provided, not create symlinks for all files from latest.")
    print("2. There's a bug in the implementation: upgrade_from_latest should create symlinks")
    print("   for all files from the latest version, not just the ones provided.")

    # Cleanup
    shutil.rmtree(temp_dir_v1, ignore_errors=True)
    shutil.rmtree(temp_dir_v2, ignore_errors=True)
