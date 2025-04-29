"""
Unit tests for the MapfileProcessor class.

This module tests the functionality of the MapfileProcessor class
with persistent test directories for manual inspection.
"""

import os
import pytest
import tempfile
from pathlib import Path
import shutil
import netCDF4
import numpy as np
from datetime import datetime

from esgprep.mapfile.processor import MapfileProcessor
from esgprep.mapfile.models import FileInput, Mapfile, MapfileEntry, MapfileResult

# Get the repo root directory
REPO_ROOT = Path(__file__).parent.parent.absolute()
print(f"Using repository root: {REPO_ROOT}")

# Create a persistent test directory
TEST_ROOT = REPO_ROOT / "test_data"
print(f"Test data will be stored in: {TEST_ROOT}")

# Project ID for tests
PROJECT_ID = "cmip6"

@pytest.fixture(scope="module", autouse=True)
def setup_and_cleanup():
    """Setup test environment and clean up after all tests."""
    # Create source and output directories
    source_dir = TEST_ROOT / "source"
    output_dir = TEST_ROOT / "mapfiles"
    
    # Clean before test
    print("Cleaning up existing test directories...")
    if source_dir.exists():
        shutil.rmtree(source_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    # Create fresh directories
    source_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Source directory: {source_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create temporary netCDF files for testing
    files = create_test_files(source_dir)
    print(f"Created {len(files)} test files:")
    for file in files[:3]:  # Just show first few
        print(f"  - {file}")
    
    # Yield control back to tests
    yield
    
    # DO NOT clean up after tests to allow manual inspection
    print("\nTest data preserved for manual inspection:")
    print(f"  Source files: {source_dir}")
    print(f"  Output mapfiles: {output_dir}")

@pytest.fixture
def source_dir():
    """Return the source directory for test files."""
    return TEST_ROOT / "source"

@pytest.fixture
def output_dir():
    """Return the output directory for mapfiles."""
    return TEST_ROOT / "mapfiles"

def create_test_files(directory, count=3):
    """Create test netCDF files with appropriate attributes."""
    files = []
    
    # Create different dataset structures
    for i in range(count):
        # Create directory structure that mimics a real DRS path
        dataset_dir = directory / PROJECT_ID.upper() / "CMIP" / "TEST-INSTITUTION" / "TEST-MODEL" / f"test-experiment-{i}" / f"r1i1p1f{i}" / "day" / f"var{i}" / "gn" / "v20250401"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Create netCDF file with a more realistic name
        file_path = dataset_dir / f"var{i}_day_TEST-MODEL_test-experiment-{i}_r1i1p1f{i}_gn_20250101-20251231.nc"
        
        # Create a test netCDF file
        ds = netCDF4.Dataset(file_path, 'w', format='NETCDF4')
        
        # Add dimensions
        ds.createDimension('time', 10)
        ds.createDimension('lat', 5)
        ds.createDimension('lon', 5)
        
        # Add variables
        times = ds.createVariable('time', 'f8', ('time',))
        lats = ds.createVariable('lat', 'f4', ('lat',))
        lons = ds.createVariable('lon', 'f4', ('lon',))
        temp = ds.createVariable('tas', 'f4', ('time', 'lat', 'lon',))
        
        # Fill with data
        times[:] = np.arange(10)
        lats[:] = np.arange(5)
        lons[:] = np.arange(5)
        temp[:] = np.random.rand(10, 5, 5)
        
        # Add global attributes
        ds.project_id = PROJECT_ID.upper()
        ds.mip_era = PROJECT_ID.upper()
        ds.activity_id = "CMIP"
        ds.institution_id = "TEST-INSTITUTION"
        ds.source_id = "TEST-MODEL"
        ds.experiment_id = f"test-experiment-{i}"
        ds.variant_label = f"r1i1p1f{i}"
        ds.table_id = "day"
        ds.variable_id = f"var{i}"
        ds.grid_label = "gn"
        
        # Close the file
        ds.close()
        
        files.append(file_path)
    
    return files

def test_mapfile_processor_initialization(output_dir):
    """Test that the MapfileProcessor initializes correctly."""
    processor = MapfileProcessor(
        outdir=output_dir,
        project=PROJECT_ID,
        mapfile_name="{dataset_id}.v{version}.map"
    )
    
    assert processor.outdir == output_dir
    assert processor.project == PROJECT_ID
    assert processor.mapfile_name == "{dataset_id}.v{version}.map"
    assert processor.no_checksum is False
    assert processor.checksum_type == "sha256"
    
def test_file_input_model(source_dir):
    """Test the FileInput model and dataset_id generation."""
    # Find a test file
    test_files = list(source_dir.glob("**/*.nc"))
    assert len(test_files) > 0, "No test files found"
    test_file = test_files[0]
    
    # Create processor to get a FileInput
    processor = MapfileProcessor(
        outdir=TEST_ROOT / "mapfiles",
        project=PROJECT_ID,
        no_checksum=True  # Skip checksums for faster tests
    )
    
    # Create FileInput
    input_file = processor.create_file_input(test_file)
    
    # Check basic properties
    assert input_file.source_path == test_file
    assert input_file.file_size == test_file.stat().st_size
    assert input_file.project == PROJECT_ID
    assert len(input_file.attributes) > 0, "No attributes extracted"
    
    # Check dataset_id generation
    dataset_id = input_file.dataset_id
    print(f"\nGenerated dataset_id: {dataset_id}")
    assert dataset_id, "No dataset_id generated"
    
    # Check that it contains expected parts
    assert PROJECT_ID.upper() in dataset_id or PROJECT_ID.lower() in dataset_id, \
        f"Dataset ID should contain project: {dataset_id}"
    
    # Print facets for debugging
    print("Extracted facets:")
    for key, value in input_file.drs_facets.items():
        print(f"  - {key}: {value}")
    
    # Check if esgvoc DRS generator was used
    if input_file._drs_generator:
        print("Using esgvoc DRS generator for dataset_id generation")
    else:
        print("Using fallback dataset_id generation")
    
    # Test with custom facets
    custom_facets = {
        "activity_id": "TEST-ACTIVITY",
        "experiment_id": "TEST-EXPERIMENT"
    }
    input_file.drs_facets.update(custom_facets)
    
    # Get updated dataset_id
    updated_dataset_id = input_file.dataset_id
    print(f"Updated dataset_id with custom facets: {updated_dataset_id}")
    
    # Check that custom facets are included
    for value in custom_facets.values():
        assert value in updated_dataset_id, f"Custom facet {value} should be in dataset_id"

def test_process_file(source_dir, output_dir):
    """Test processing a single file."""
    # Find a test file
    test_files = list(source_dir.glob("**/*.nc"))
    assert len(test_files) > 0, "No test files found"
    
    # Create processor
    processor = MapfileProcessor(
        outdir=output_dir,
        project=PROJECT_ID,
        no_checksum=True  # Skip checksums for faster tests
    )
    
    # Process file
    result = processor.process_file(test_files[0])
    
    # Check result
    assert result.success, f"Processing failed: {result.error_message}"
    assert result.input_file is not None, "No input_file in result"
    assert result.input_file.dataset_id != ""
    assert result.mapfile_path is not None
    assert result.input_file.file_size == test_files[0].stat().st_size
    
    # Print result for inspection
    print(f"\nProcessed file: {test_files[0]}")
    print(f"  Dataset ID: {result.input_file.dataset_id}")
    print(f"  Mapfile: {result.mapfile_path}")
    
    # Access through properties
    assert result.dataset_id == result.input_file.dataset_id
    assert result.file_size == result.input_file.file_size
    assert result.source_path == result.input_file.source_path

def test_dataset_id_generation(source_dir, output_dir):
    """Test different methods of dataset ID generation."""
    # Find a test file
    test_files = list(source_dir.glob("**/*.nc"))
    assert len(test_files) > 0, "No test files found"
    test_file = test_files[0]
    
    print(f"\nTesting dataset ID generation for {test_file.name}")
    
    # 1. Test with esgvoc integration
    try:
        print("1. Testing with esgvoc integration (if available)")
        import esgvoc.api as ev
        from esgvoc.apps.drs.generator import DrsGenerator
        
        # Create FileInput manually
        input_file = FileInput(
            source_path=test_file,
            filename=test_file.name,
            file_size=test_file.stat().st_size,
            project=PROJECT_ID,
            attributes={
                "mip_era": PROJECT_ID.upper(),
                "activity_id": "CMIP",
                "institution_id": "TEST-INSTITUTION",
                "source_id": "TEST-MODEL",
                "experiment_id": "test-experiment",
                "variant_label": "r1i1p1f1",
                "table_id": "day",
                "variable_id": "tas",
                "grid_label": "gn"
            }
        )
        
        # Make sure generator is initialized
        assert input_file._drs_generator is not None, "DRS generator not initialized"
        
        # Get dataset ID
        dataset_id = input_file.dataset_id
        print(f"Generated dataset ID with esgvoc: {dataset_id}")
        
        # Should contain all facets
        assert "TEST-INSTITUTION" in dataset_id
        assert "TEST-MODEL" in dataset_id
        assert "test-experiment" in dataset_id
        
    except ImportError:
        print("esgvoc not available, skipping esgvoc integration test")
    
    # 2. Test with fallback approach (manual generation)
    print("2. Testing fallback approach")
    processor = MapfileProcessor(
        outdir=output_dir,
        project=PROJECT_ID,
        no_checksum=True
    )
    
    # Force fallback by temporarily disabling esgvoc integration
    original_input_file = processor.create_file_input(test_file)
    original_input_file._drs_generator = None
    original_input_file._project_config = None
    
    # Generate dataset ID with fallback method
    fallback_dataset_id = original_input_file.dataset_id
    print(f"Generated dataset ID with fallback: {fallback_dataset_id}")
    
    # Should still work and contain project
    assert PROJECT_ID.upper() in fallback_dataset_id or PROJECT_ID.lower() in fallback_dataset_id
    
    # 3. Compare with traditional extraction method
    print("3. Testing traditional extraction method")
    traditional_dataset_info = processor._extract_dataset_info(test_file)
    assert traditional_dataset_info is not None
    
    traditional_dataset_id = traditional_dataset_info[0]
    print(f"Generated dataset ID with traditional method: {traditional_dataset_id}")
    
    # Should still work
    assert traditional_dataset_id

def test_write_mapfiles(source_dir, output_dir):
    """Test writing mapfiles to disk."""
    # Create processor with no checksums for faster tests
    processor = MapfileProcessor(
        outdir=output_dir,
        project=PROJECT_ID,
        no_checksum=True
    )
    
    # Process directory
    print(f"\nSearching for files in {source_dir}...")
    all_files = list(source_dir.glob("**/*.nc"))
    print(f"Found {len(all_files)} NetCDF files")
    
    # Process the files
    results = list(processor.process_directory(source_dir))
    print(f"Processed {len(results)} files with {sum(1 for r in results if r.success)} successes")
    
    # Write mapfiles
    count = processor.write_mapfiles()
    print(f"Wrote {count} mapfiles to {output_dir}")
    
    # Check results
    assert count > 0, "No mapfiles were written"
    
    # Check that files were actually written
    mapfiles = list(output_dir.glob("*.map"))
    assert len(mapfiles) > 0, "No mapfiles found in output directory"
    
    # Print mapfile information for inspection
    print("\nGenerated mapfiles:")
    for mapfile_path in mapfiles:
        with open(mapfile_path) as f:
            lines = f.readlines()
            print(f"  - {mapfile_path.name}: {len(lines)} entries")
            # Print first few lines for inspection
            if len(lines) > 0:
                print(f"    First entry: {lines[0].strip()}")
            
            # Check content
            assert len(lines) > 0, f"Mapfile {mapfile_path} is empty"

def test_with_checksum(source_dir, output_dir):
    """Test processing with checksum calculation."""
    # Use a separate output directory for this test to avoid confusion
    checksum_dir = output_dir / "with_checksum"
    checksum_dir.mkdir(exist_ok=True)
    print(f"\nTesting checksums, output to {checksum_dir}")
    
    # Only test one file to keep test time reasonable
    test_files = list(source_dir.glob("**/*.nc"))
    test_file = test_files[0]
    print(f"Computing checksum for {test_file}")
    
    # Create processor with checksums enabled
    processor = MapfileProcessor(
        outdir=checksum_dir,
        project=PROJECT_ID,
        no_checksum=False,
        checksum_type="sha256"
    )
    
    # Process file
    result = processor.process_file(test_file)
    
    # Check result
    assert result.success, f"Processing failed: {result.error_message}"
    
    # Write mapfiles
    processor.write_mapfiles()
    
    # Read back the mapfile to check checksums
    mapfiles = list(checksum_dir.glob("*.map"))
    assert len(mapfiles) > 0, "No mapfiles generated with checksums"
    
    mapfile_path = mapfiles[0]
    print(f"Checking mapfile: {mapfile_path}")
    
    with open(mapfile_path) as f:
        content = f.read()
        print(f"Mapfile content (first 200 chars): {content[:200]}...")
        
    # Verify checksum is present
    assert "checksum=" in content, "No checksum found in mapfile"
    assert "checksum_type=SHA256" in content, "No checksum type found in mapfile"
    
    print("Checksum test passed successfully")

def test_all_versions_flag(source_dir, output_dir):
    """Test processing with all_versions flag."""
    # Use a separate output directory
    all_versions_dir = output_dir / "all_versions"
    all_versions_dir.mkdir(exist_ok=True)
    print(f"\nTesting all_versions flag, output to {all_versions_dir}")
    
    # Create processor with all_versions=True
    processor = MapfileProcessor(
        outdir=all_versions_dir,
        project=PROJECT_ID,
        no_checksum=True,
        all_versions=True
    )
    
    # Process directory
    results = list(processor.process_directory(source_dir))
    processor.write_mapfiles()
    
    # Check that appropriate mapfiles were generated
    mapfiles = list(all_versions_dir.glob("*.map"))
    assert len(mapfiles) > 0, "No mapfiles generated with all_versions flag"
    
    print(f"Generated {len(mapfiles)} mapfiles with all_versions flag")
    for mapfile in mapfiles:
        print(f"  - {mapfile.name}")

def test_custom_tech_notes(source_dir, output_dir):
    """Test inclusion of technical notes in mapfiles."""
    # Use a separate output directory
    tech_notes_dir = output_dir / "tech_notes"
    tech_notes_dir.mkdir(exist_ok=True)
    print(f"\nTesting tech notes, output to {tech_notes_dir}")
    
    # Create processor with tech notes
    processor = MapfileProcessor(
        outdir=tech_notes_dir,
        project=PROJECT_ID,
        no_checksum=True,
        tech_notes_url="https://example.com/tech-notes",
        tech_notes_title="Technical Notes for Testing"
    )
    
    # Process one file
    test_files = list(source_dir.glob("**/*.nc"))
    result = processor.process_file(test_files[0])
    processor.write_mapfiles()
    
    # Check that tech notes were included
    mapfiles = list(tech_notes_dir.glob("*.map"))
    assert len(mapfiles) > 0, "No mapfiles generated with tech notes"
    
    with open(mapfiles[0]) as f:
        content = f.read()
        print(f"Mapfile content with tech notes: {content[:200]}...")
    
    assert "dataset_tech_notes=https://example.com/tech-notes" in content
    assert "dataset_tech_notes_title=Technical Notes for Testing" in content
    
    print("Tech notes test passed successfully")

if __name__ == "__main__":
    # Create log directory if it doesn't exist
    log_dir = REPO_ROOT / "test_data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("Running MapfileProcessor tests")
    print("=" * 80)
    print(f"Test data directory: {TEST_ROOT}")
    print(f"Log directory: {log_dir}")
    print("=" * 80)
    
    # Run all tests
    pytest.main(["-xvs", __file__])
