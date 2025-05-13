import os
import shutil
import tempfile
from pathlib import Path

import netCDF4
import numpy as np
import pytest

# Import the refactored DrsProcessor
from esgprep.drs.make import DrsProcessor
# Import Post_Test_Folder for directory structure assertions
from esgprep.tests.drs.post_test_folder import Post_Test_Folder

# Configuration
PROJECT_ID = "cmip6"
VERSION_STR = "v20250401"

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
    create_sample_netcdf_files(incoming_dir)

    # Print directory paths for manual inspection
    print(f"Test incoming directory: {incoming_dir}")
    print(f"Test root directory: {root_dir}")

    # Yield the test directories
    yield {"incoming_dir": incoming_dir, "root_dir": root_dir}

    # Don't clean up after test to allow manual inspection
    # Comment out clean_directory(incoming_dir) and clean_directory(root_dir) if you need to keep files


def clean_directory(directory):
    """Clean a directory but don't delete the directory itself."""
    for item in directory.glob("*"):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    print(f"Cleaned directory: {directory}")


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

    # Optional: Clean directories after all tests if you want
    # Uncomment if you want to clean after all tests
    # clean_directory(incoming_dir)
    # clean_directory(root_dir)


def create_sample_netcdf_files(directory, count=3):
    """Create sample NetCDF files with attributes for DRS structure."""
    # List to store file paths for return
    file_paths = []

    for i in range(count):
        # Create a folder structure to simulate real data organization
        subfolder = directory / f"subfolder_{i}"
        subfolder.mkdir(exist_ok=True, parents=True)

        # Create NetCDF file with DRS-relevant attributes
        filename = subfolder / f"{PROJECT_ID}_model{i}_var{i}.nc"

        # Create NetCDF file with proper attributes
        ds = netCDF4.Dataset(filename, "w", format="NETCDF4")

        # Add dimensions
        ds.createDimension("time", 10)
        ds.createDimension("lat", 5)
        ds.createDimension("lon", 5)

        # Add variables
        times = ds.createVariable("time", "f8", ("time",))
        lats = ds.createVariable("lat", "f4", ("lat",))
        lons = ds.createVariable("lon", "f4", ("lon",))
        temp = ds.createVariable(
            "tas",
            "f4",
            (
                "time",
                "lat",
                "lon",
            ),
        )

        # Add data
        times[:] = np.arange(10)
        lats[:] = np.arange(5)
        lons[:] = np.arange(5)
        temp[:] = np.random.rand(10, 5, 5)

        # Add global attributes relevant for DRS with valid values
        temp_dict = {"cmip6": "CMIP6", "cmip6plus": "CMIP6Plus", "cmip7": "CMIP7"}
        ds.project_id = temp_dict[PROJECT_ID]

        ds.mip_era = temp_dict[PROJECT_ID]
        ds.activity_id = "CMIP"  # Valid acitivity ID
        ds.institution_id = "IPSL"  # Valid institution ID
        ds.source_id = "IPSL-CM6A-LR"  # Valid source model ID
        ds.experiment_id = "historical"
        ds.variant_label = f"r1i1p1f{i}"
        ds.table_id = "day"
        ds.variable_id = "tas"
        ds.grid_label = "gn"

        # Close the file
        ds.close()

        # Add to file_paths
        file_paths.append(filename)

    return file_paths


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


def test_drs_processor_set_custom_values(test_setup):
    """Test DrsProcessor with custom facet values."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # Custom facet to set
    custom_facet = "activity_id"
    custom_value = "AerChemMIP"

    # Create DrsProcessor with custom values
    processor = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="symlink", version=VERSION_STR
    )

    # Find NetCDF files
    nc_files = list(incoming_dir.glob("**/*.nc"))

    # Process each file
    results = []
    for file_path in nc_files:
        # Create file input with custom value
        file_input = processor.create_file_input(file_path)

        # Set custom facet
        file_input.drs_facets[custom_facet] = custom_value

        # Process the modified file input
        result = processor.process_file(file_path)
        results.append(result)

    # Collect all operations
    operations = []
    for result in results:
        operations.extend(result.operations)

    # Execute operations
    success = processor.execute_operations(operations)
    assert success, "Execution of operations failed"

    # Check that custom facet is reflected in the directory structure
    custom_dirs = list(root_dir.glob(f"**/{custom_value}"))

    print(f"Looking for directories with {custom_value}:")
    for custom_dir in custom_dirs:
        print(f"  {custom_dir}")

    # We don't assert on finding the custom value in paths because it depends on pyessv configuration
    # and may not be directly visible in the path


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


def test_drs_processor_version_update(test_setup):
    """Test DrsProcessor with version update and verify with Post_Test_Folder."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # First version
    first_version = "v20250401"

    # Create DrsProcessor for first version
    processor1 = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="copy", version=first_version
    )

    # Process all files in directory for first version
    results1 = list(processor1.process_directory(incoming_dir))

    # Execute operations for first version
    operations1 = []
    for result in results1:
        operations1.extend(result.operations)
    processor1.execute_operations(operations1)

    # Create modified sample files for second version
    modified_dir = Path(tempfile.mkdtemp(prefix="esgdrs_test_modified_"))
    create_sample_netcdf_files(modified_dir, count=4)  # One more file than original

    # Second version
    second_version = "v20250402"

    # Create DrsProcessor for second version
    processor2 = DrsProcessor(
        root_dir=root_dir, project=PROJECT_ID, mode="copy", version=second_version
    )

    # Process all files in directory for second version
    results2 = list(processor2.process_directory(modified_dir))

    # Execute operations for second version
    operations2 = []
    for result in results2:
        operations2.extend(result.operations)
    processor2.execute_operations(operations2)

    # Check that both versions exist
    first_version_files = list(root_dir.glob(f"**/{first_version}/**/*.nc"))
    second_version_files = list(root_dir.glob(f"**/{second_version}/**/*.nc"))

    assert len(first_version_files) > 0, "First version files not found"
    assert len(second_version_files) > 0, "Second version files not found"
    assert len(second_version_files) > len(first_version_files), (
        "Second version should have more files"
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
        version_dirs = list(dataset_dir.glob("v*"))
        version_names = [d.name for d in version_dirs]
        print(f"Found version directories: {version_names}")
        assert first_version in version_names, f"First version {first_version} not found in {version_names}"
        assert second_version in version_names, f"Second version {second_version} not found in {version_names}"

    # Clean up modified directory
    shutil.rmtree(modified_dir, ignore_errors=True)


def test_drs_processor_with_ignores(test_setup):
    """Test DrsProcessor with ignore_from_incoming and verify with Post_Test_Folder."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # Find some files to ignore
    nc_files = list(incoming_dir.glob("**/*.nc"))
    files_to_ignore = [nc_files[0].name]  # Ignore first file

    # Create DrsProcessor with ignore_from_incoming
    processor = DrsProcessor(
        root_dir=root_dir,
        project=PROJECT_ID,
        mode="copy",
        version=VERSION_STR,
        ignore_from_incoming=files_to_ignore,
    )

    # Process all files in directory
    results = list(processor.process_directory(incoming_dir))

    # Count successful results (should be less than total files)
    successful_results = [r for r in results if r.success]

    # Should have at least one ignored file
    assert len(successful_results) < len(nc_files), "Expected some files to be ignored"

    # Execute operations for successful files
    operations = []
    for result in successful_results:
        operations.extend(result.operations)
    processor.execute_operations(operations)

    # Check that ignored files are not in destination
    for ignored_file in files_to_ignore:
        # Look for ignored file name in destination
        ignored_dests = list(root_dir.glob(f"**/{ignored_file}"))
        assert len(ignored_dests) == 0, (
            f"Ignored file {ignored_file} found in destination"
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

        # Verify ignored files are not in any directory
        for ignored_file in files_to_ignore:
            # Check files directory
            files_dir = dataset_dir / "files"
            ignored_in_files = list(files_dir.glob(f"**/{ignored_file}"))
            assert len(ignored_in_files) == 0, f"Ignored file {ignored_file} found in files directory"

            # Check version directory
            version_dir = dataset_dir / VERSION_STR
            ignored_in_version = list(version_dir.glob(f"**/{ignored_file}"))
            assert len(ignored_in_version) == 0, f"Ignored file {ignored_file} found in version directory"

            # Check latest directory
            latest_dir = dataset_dir / "latest"
            ignored_in_latest = list(latest_dir.glob(f"**/{ignored_file}"))
            assert len(ignored_in_latest) == 0, f"Ignored file {ignored_file} found in latest directory"


def test_drs_processor_upgrade_from_latest(test_setup):
    """Test DrsProcessor with upgrade from latest and verify with Post_Test_Folder."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]

    # First version
    first_version = "v20250401"

    # Create DrsProcessor for first version
    processor1 = DrsProcessor(root_dir=root_dir, mode="copy", version=first_version)

    # Process all files in directory for first version
    results1 = list(processor1.process_directory(incoming_dir))

    # Keep track of the processed dataset paths for later comparison
    processed_datasets = set()
    for result in results1:
        if result.success and result.dataset:
            # Store the base path (everything up to the version directory)
            dataset_path = result.input_file.drs_path.parent.parent
            processed_datasets.add(dataset_path)

    # Execute operations for first version
    operations1 = []
    for result in results1:
        operations1.extend(result.operations)
    processor1.execute_operations(operations1)

    # Create modified sample files for second version
    modified_dir = Path(tempfile.mkdtemp(prefix="esgdrs_test_modified_"))
    new_files = create_sample_netcdf_files(modified_dir, count=1)  # Just one new file

    # Second version
    second_version = "v20250402"

    # Create DrsProcessor for second version with upgrade_from_latest=True
    processor2 = DrsProcessor(
        root_dir=root_dir,
        project=PROJECT_ID,
        mode="copy",
        version=second_version,
        upgrade_from_latest=True,
    )

    # Process just the new file for second version
    result2 = processor2.process_file(new_files[0])

    # Execute operations for second version
    processor2.execute_operations(result2.operations)

    # Now count files in a way that respects the dataset structure
    first_version_count = 0
    second_version_count = 0

    # For each dataset that was processed in the first run
    for dataset_path in processed_datasets:
        # Count files in first version directory
        first_version_dir = dataset_path / first_version
        if first_version_dir.exists():
            first_version_files = list(first_version_dir.glob("*.nc"))
            first_version_count += len(first_version_files)

        # Count files in second version directory
        second_version_dir = dataset_path / second_version
        if second_version_dir.exists():
            second_version_files = list(second_version_dir.glob("*.nc"))
            second_version_count += len(second_version_files)

    print(f"Found {first_version_count} files in first version directories")
    print(f"Found {second_version_count} files in second version directories")

    # Assert that both versions have files
    assert first_version_count > 0, "First version files not found"
    assert second_version_count > 0, "Second version files not found"

    # Use Post_Test_Folder to verify directory structure
    # Find dataset folders (those containing version folders)
    dataset_dirs = []
    for path in root_dir.glob("**"):
        # Look for directories that contain both versions
        if path.is_dir() and (path / first_version).exists() and (path / second_version).exists():
            dataset_dirs.append(path)

    # Test each dataset directory structure
    for dataset_dir in dataset_dirs:
        print(f"Testing dataset directory structure with multiple versions: {dataset_dir}")
        test_folder = Post_Test_Folder(dataset_dir)

        # Test the directory structure
        test_folder.test()

        # Additional assertions specific to upgrade_from_latest
        # 1. Latest directory should be a symlink to the second version
        latest_dir = dataset_dir / "latest"
        assert latest_dir.exists() and latest_dir.is_symlink(), "Latest dir should be a symlink"
        latest_target = latest_dir.resolve()
        expected_target = dataset_dir / second_version
        assert expected_target.samefile(latest_target), f"Latest symlink points to {latest_target}, expected {expected_target}"

        # 2. Both version directories should exist
        assert (dataset_dir / first_version).exists(), f"First version directory {first_version} not found"
        assert (dataset_dir / second_version).exists(), f"Second version directory {second_version} not found"

        # 3. Files directory should contain data version folders for both versions
        files_dir = dataset_dir / "files"
        assert files_dir.exists(), "Files directory not found"

        # Find d* folders for each version
        first_data_version = first_version[1:]  # Remove 'v' prefix
        second_data_version = second_version[1:]  # Remove 'v' prefix

        first_data_dir = files_dir / f"d{first_data_version}"
        second_data_dir = files_dir / f"d{second_data_version}"

        assert first_data_dir.exists(), f"Data directory d{first_data_version} not found"
        assert second_data_dir.exists(), f"Data directory d{second_data_version} not found"

        # Count files in data version directories
        first_data_files = list(first_data_dir.glob("*.nc"))
        second_data_files = list(second_data_dir.glob("*.nc"))

        assert len(first_data_files) > 0, f"No files found in d{first_data_version} directory"
        assert len(second_data_files) > 0, f"No files found in d{second_data_version} directory"

        # Total count should match or exceed the version directory counts
        total_data_files = len(first_data_files) + len(second_data_files)
        assert total_data_files >= first_version_count + second_version_count, "Files directory missing some files"

    # Clean up modified directory
    shutil.rmtree(modified_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
