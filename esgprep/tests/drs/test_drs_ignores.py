"""
Test ignore functionality in DrsProcessor.
"""

from esgprep.drs.make import DrsProcessor
from esgprep.tests.drs.test_utils import PROJECT_ID, VERSION_STR, create_files_different_variables
from esgprep.tests.drs.post_test_folder import Post_Test_Folder


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
