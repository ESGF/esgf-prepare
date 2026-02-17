"""
Unit tests for DRS latest command functionality.

Tests the esgdrs latest command which creates and manages 'latest' symlinks
pointing to the most recent version directories in DRS structures.
"""

import re
from argparse import Namespace
from pathlib import Path

from esgprep.esgdrs import run
from tests.fixtures.generators import (
    create_files_different_variables,
    clean_directory,
)


def get_default_make_args(incoming_dir, drs_root) -> Namespace:
    """Get default arguments for the make command."""
    return Namespace(
        cmd="make",
        log=None,
        debug=False,
        action="upgrade",
        directory=[str(incoming_dir)],
        project="cmip6",
        ignore_dir=re.compile("^.*/(files|\\.[\\w]*).*$"),
        include_file=["^.*\\.nc$"],
        exclude_file=["^\\..*$"],
        color=False,
        no_color=False,
        max_processes=1,
        root=str(drs_root),
        version="19810101",
        set_value=None,
        set_key=None,
        rescan=True,
        commands_file=None,
        overwrite_commands_file=False,
        upgrade_from_latest=False,
        ignore_from_latest=None,
        ignore_from_incoming=None,
        copy=True,
        link=False,
        symlink=False,
        no_checksum=False,
        checksums_from=None,
        quiet=False,
        prog="esgdrs",
    )


def get_default_latest_args(drs_root) -> Namespace:
    """Get default arguments for the latest command."""
    return Namespace(
        cmd="latest",
        log=None,
        debug=False,
        action="upgrade",
        directory=[str(drs_root)],
        project="cmip6",
        ignore_dir=re.compile("^.*/(files|\\.[\\w]*).*$"),
        include_file=["^.*\\.nc$"],
        exclude_file=["^\\..*$"],
        color=False,
        no_color=False,
        max_processes=1,
        rescan=True,
        prog="esgdrs",
    )


def find_latest_symlinks(root_dir: Path) -> list[Path]:
    """Find all 'latest' symlinks in the DRS structure."""
    latest_symlinks = []
    for latest_path in root_dir.rglob("latest"):
        if latest_path.is_symlink():
            latest_symlinks.append(latest_path)
    return latest_symlinks


def find_version_directories(root_dir: Path) -> list[Path]:
    """Find all version directories (vYYYYMMDD pattern) in the DRS structure."""
    version_dirs = []
    for path in root_dir.rglob("v*"):
        if path.is_dir() and re.match(r"^v\d{8}$", path.name):
            version_dirs.append(path)
    return version_dirs


class TestDRSLatest:
    """Test class for DRS latest command functionality."""

    def test_latest_single_variable_single_version(self, drs_test_structure):
        """Test latest command with a single variable and single version."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Step 1: Create test data and DRS structure
        create_files_different_variables(incoming_dir, count=1)
        make_args = get_default_make_args(incoming_dir, drs_root)
        run(make_args)

        # Step 2: Verify DRS structure was created with latest symlinks
        initial_symlinks = find_latest_symlinks(drs_root)
        assert len(initial_symlinks) > 0, "No latest symlinks created by make command"

        # Step 3: Remove latest symlinks
        for symlink in initial_symlinks:
            symlink.unlink()
            assert not symlink.exists(), f"Failed to remove symlink: {symlink}"

        # Step 4: Verify symlinks are gone
        remaining_symlinks = find_latest_symlinks(drs_root)
        assert len(remaining_symlinks) == 0, "Some symlinks were not removed"

        # Step 5: Run latest command to recreate symlinks
        latest_args = get_default_latest_args(drs_root)
        run(latest_args)

        # Step 6: Verify symlinks were recreated correctly
        recreated_symlinks = find_latest_symlinks(drs_root)
        assert len(recreated_symlinks) == len(initial_symlinks), (
            f"Expected {len(initial_symlinks)} symlinks, got {len(recreated_symlinks)}"
        )

        # Step 7: Validate each symlink
        for symlink in recreated_symlinks:
            assert symlink.exists(), f"Symlink does not exist: {symlink}"
            assert symlink.is_symlink(), f"Path is not a symlink: {symlink}"

    def test_latest_multiple_variables_multiple_versions(self, drs_test_structure):
        """Test latest command with multiple variables and versions."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Step 1: Create test data with different variables
        create_files_different_variables(incoming_dir, count=3)

        # Step 2: Run make command for first version
        make_args = get_default_make_args(incoming_dir, drs_root)
        make_args.version = "19810101"
        run(make_args)

        # Step 3: Create more test data for a second version
        clean_directory(incoming_dir)
        create_files_different_variables(incoming_dir, count=3)

        # Step 4: Run make command for second version
        make_args.version = "19810102"
        make_args.rescan = True
        run(make_args)

        # Step 5: Verify multiple versions exist
        version_dirs = find_version_directories(drs_root)
        assert len(version_dirs) >= 2, (
            f"Expected at least 2 version directories, got {len(version_dirs)}"
        )

        # Step 6: Remove all latest symlinks
        initial_symlinks = find_latest_symlinks(drs_root)
        for symlink in initial_symlinks:
            symlink.unlink()

        # Step 7: Run latest command
        latest_args = get_default_latest_args(drs_root)
        run(latest_args)

        # Step 8: Verify all symlinks recreated correctly
        recreated_symlinks = find_latest_symlinks(drs_root)
        assert len(recreated_symlinks) >= len(initial_symlinks)

        # Step 9: Verify symlinks point to the latest version (v19810102)
        for symlink in recreated_symlinks:
            assert symlink.exists() and symlink.is_symlink()
            target = symlink.readlink()
            assert target == Path("v19810102"), (
                f"Expected symlink to point to v19810102, got {target}"
            )

    def test_latest_no_existing_structure(self, drs_test_structure):
        """Test latest command when no DRS structure exists."""
        drs_root = drs_test_structure["root"]

        # Ensure clean state
        clean_directory(drs_root)

        # Run latest command on empty directory
        latest_args = get_default_latest_args(drs_root)
        run(latest_args)

        # Should not create anything and not error
        symlinks = find_latest_symlinks(drs_root)
        assert len(symlinks) == 0, "No symlinks should be created for empty structure"

    def test_latest_broken_symlinks(self, drs_test_structure):
        """Test latest command when some latest symlinks are broken."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Step 1: Create DRS structure
        create_files_different_variables(incoming_dir, count=2)
        make_args = get_default_make_args(incoming_dir, drs_root)
        run(make_args)

        # Step 2: Get symlink locations
        symlinks = find_latest_symlinks(drs_root)
        assert len(symlinks) > 0, "Need symlinks for this test"

        # Step 3: Break some symlinks by pointing to non-existent targets
        for symlink in symlinks[:1]:  # Break first symlink only
            symlink.unlink()
            symlink.symlink_to("nonexistent_version")
            assert symlink.is_symlink(), "Should be a symlink"
            assert not symlink.exists(), "Should be a broken symlink"

        # Step 4: Run latest command - should fix broken symlinks
        latest_args = get_default_latest_args(drs_root)
        run(latest_args)

        # Step 5: Verify all symlinks are now correct
        final_symlinks = find_latest_symlinks(drs_root)
        for symlink in final_symlinks:
            assert symlink.exists(), f"Symlink should exist: {symlink}"
            assert symlink.is_symlink(), f"Should be a symlink: {symlink}"

    def test_latest_mixed_versions_per_dataset(self, drs_test_structure):
        """Test latest command when different datasets have different latest versions."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Step 1: Create initial data
        create_files_different_variables(incoming_dir, count=2)

        # Step 2: Create first version for both datasets
        make_args = get_default_make_args(incoming_dir, drs_root)
        make_args.version = "19810101"
        run(make_args)

        # Step 3: Create second version data for only one variable/dataset
        clean_directory(incoming_dir)
        create_files_different_variables(incoming_dir, count=1)  # Only first variable

        # Step 4: Create second version
        make_args.version = "19810102"
        make_args.rescan = True
        run(make_args)

        # Step 5: Remove symlinks and recreate
        for symlink in find_latest_symlinks(drs_root):
            symlink.unlink()

        latest_args = get_default_latest_args(drs_root)
        run(latest_args)

        # Step 6: Verify correct recreation
        final_symlinks = find_latest_symlinks(drs_root)
        assert len(final_symlinks) >= 2, "Should have symlinks for multiple datasets"

        # At least one should point to the newer version
        targets = [symlink.readlink() for symlink in final_symlinks]
        assert Path("v19810102") in targets, (
            "Should have at least one symlink pointing to v19810102"
        )
