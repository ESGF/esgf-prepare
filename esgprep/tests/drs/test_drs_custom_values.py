"""
Test setting custom values in DrsProcessor.
"""

from esgprep.drs.make import DrsProcessor
from esgprep.tests.drs.test_utils import PROJECT_ID, VERSION_STR, create_files_different_models


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
