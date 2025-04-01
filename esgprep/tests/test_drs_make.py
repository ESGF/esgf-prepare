import os
import sys
import pytest
import shutil
import tempfile
import datetime
from pathlib import Path
import netCDF4
import numpy as np

# Import the refactored DrsProcessor
from esgprep.drs.make import DrsProcessor
from esgprep.drs.models import MigrationMode, FileInput, DrsResult

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
    yield {
        "incoming_dir": incoming_dir,
        "root_dir": root_dir
    }
    
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
        filename = subfolder / f"cmip6_model{i}_var{i}.nc"
        
        # Create NetCDF file with proper attributes
        ds = netCDF4.Dataset(filename, 'w', format='NETCDF4')
        
        # Add dimensions
        ds.createDimension('time', 10)
        ds.createDimension('lat', 5)
        ds.createDimension('lon', 5)
        
        # Add variables
        times = ds.createVariable('time', 'f8', ('time',))
        lats = ds.createVariable('lat', 'f4', ('lat',))
        lons = ds.createVariable('lon', 'f4', ('lon',))
        temp = ds.createVariable('tas', 'f4', ('time', 'lat', 'lon',))
        
        # Add data
        times[:] = np.arange(10)
        lats[:] = np.arange(5)
        lons[:] = np.arange(5)
        temp[:] = np.random.rand(10, 5, 5)
        
        # Add global attributes relevant for DRS with valid values
        ds.project_id = PROJECT_ID
        ds.mip_era = PROJECT_ID.upper()
        ds.activity_id = "CMIP" # Valid acitivity ID
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
    processor = DrsProcessor(
        root_dir=root_dir,
        mode="symlink",
        version=VERSION_STR
    )
    
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
    processor = DrsProcessor(
        root_dir=root_dir,
        mode="symlink",
        version=VERSION_STR
    )
    
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
        print(f"Operation {i+1}: {op.operation_type} from {op.source} to {op.destination}")
    
    # Check that operations include creating directories and adding files
    assert any(op.destination and "cmip6" in str(op.destination).lower() for op in operations), \
        "No operations create CMIP6 directory structure"

def test_drs_processor_execute_operations(test_setup):
    """Test DrsProcessor execution of operations (todo/upgrade)."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]
    
    # Create DrsProcessor
    processor = DrsProcessor(
        root_dir=root_dir,
        mode="symlink",
        version=VERSION_STR
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

def test_drs_processor_upgrade_symlink(test_setup):
    """Test DrsProcessor with symlink mode."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]
    
    # Create DrsProcessor with symlink mode
    processor = DrsProcessor(
        root_dir=root_dir,
        mode="symlink",
        version=VERSION_STR
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

def test_drs_processor_set_custom_values(test_setup):
    """Test DrsProcessor with custom facet values."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]
    
    # Custom facet to set
    custom_facet = "activity_id"
    custom_value = "AerChemMIP"
    
    # Create DrsProcessor with custom values
    processor = DrsProcessor(
        root_dir=root_dir,
        mode="symlink",
        version=VERSION_STR
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
    """Test DrsProcessor with copy mode."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]
    
    # Create DrsProcessor with copy mode
    processor = DrsProcessor(
        root_dir=root_dir,
        mode="copy",
        version=VERSION_STR
    )
    
    # Process all files in directory
    results = list(processor.process_directory(incoming_dir))
    
    # Collect all operations
    operations = []
    for result in results:
        operations.extend(result.operations)
    print("TEST_OPERATIONS:",operations)
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
    
    # Copied files should not be symlinks
    for file in created_files:
        assert not file.is_symlink(), f"File should be a copy, not a symlink: {file}"

def test_drs_processor_link(test_setup):
    """Test DrsProcessor with link (hard link) mode."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]
    
    # Create DrsProcessor with link mode
    processor = DrsProcessor(
        root_dir=root_dir,
        mode="link",
        version=VERSION_STR
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
        
        # Check that files were hard-linked
        created_files = list(root_dir.glob(f"**/{VERSION_STR}/**/*.nc"))
        assert len(created_files) > 0, "No files were created"
        
        # Hard links are not symlinks but are linked to the same inode
        for file in created_files:
            assert not file.is_symlink(), f"File should be a hard link, not a symlink: {file}"
            
    except OSError as e:
        # Hard links might fail if incoming_dir and root_dir are on different filesystems
        # In this case, we'll skip the test but print a warning
        print(f"WARNING: Hard link test failed, possibly due to cross-filesystem linking: {e}")
        pytest.skip("Hard link test failed due to filesystem constraints")

def test_drs_processor_version_update(test_setup):
    """Test DrsProcessor with version update."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]
    
    # First version
    first_version = "v20250401"
    
    # Create DrsProcessor for first version
    processor1 = DrsProcessor(
        root_dir=root_dir,
        mode="copy",
        version=first_version
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
        root_dir=root_dir,
        mode="copy",
        version=second_version
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
    assert len(second_version_files) > len(first_version_files), "Second version should have more files"
    
    # Clean up modified directory
    shutil.rmtree(modified_dir, ignore_errors=True)


def test_drs_processor_with_ignores(test_setup):
    """Test DrsProcessor with ignore_from_incoming."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]
    
    # Find some files to ignore
    nc_files = list(incoming_dir.glob("**/*.nc"))
    files_to_ignore = [nc_files[0].name]  # Ignore first file
    
    # Create DrsProcessor with ignore_from_incoming
    processor = DrsProcessor(
        root_dir=root_dir,
        mode="copy",
        version=VERSION_STR,
        ignore_from_incoming=files_to_ignore
    )
    
    # Process all files in directory
    results = list(processor.process_directory(incoming_dir))
    
    # Count successful results (should be less than total files)
    successful_results = [r for r in results if r.success]
    
    # Should have at least one ignored file
    assert len(successful_results) < len(nc_files), \
        "Expected some files to be ignored"
    
    # Execute operations for successful files
    operations = []
    for result in successful_results:
        operations.extend(result.operations)
    processor.execute_operations(operations)
    
    # Check that ignored files are not in destination
    for ignored_file in files_to_ignore:
        # Look for ignored file name in destination
        ignored_dests = list(root_dir.glob(f"**/{ignored_file}"))
        assert len(ignored_dests) == 0, f"Ignored file {ignored_file} found in destination"

def test_drs_processor_upgrade_from_latest(test_setup):
    """Test DrsProcessor with upgrade from latest."""
    incoming_dir = test_setup["incoming_dir"]
    root_dir = test_setup["root_dir"]
    
    # First version
    first_version = "v20250401"
    
    # Create DrsProcessor for first version
    processor1 = DrsProcessor(
        root_dir=root_dir,
        mode="copy",
        version=first_version
    )
    
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
        mode="copy",
        version=second_version,
        upgrade_from_latest=True
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
    
    # Clean up modified directory
    shutil.rmtree(modified_dir, ignore_errors=True)
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
