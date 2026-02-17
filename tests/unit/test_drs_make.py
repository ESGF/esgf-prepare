"""
Unit tests for DRS make functionality.

Tests the core functionality of creating DRS directory structures
from incoming NetCDF files using the esgdrs make command.
"""

import re
from argparse import Namespace
import pytest

from esgprep.esgdrs import run
from tests.fixtures.generators import (
    create_files_different_variables,
    create_files_different_times,
    create_files_different_members,
    create_files_different_models,
)
from tests.fixtures.validators import DRSValidator
# TODO : fix all


def get_default_make_args(incoming_dir, drs_root) -> Namespace:
    """Get default arguments for the DRS make command."""
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
        version="v19810101",
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


class TestDRSMake:
    """Test class for DRS make functionality."""

    def test_make_different_variables(self, drs_test_structure):
        """Test DRS creation from files with different variables."""
        incoming_dir = drs_test_structure["incoming"] / "incoming1"
        drs_root = drs_test_structure["root"]

        # Create test files with different variables
        create_files_different_variables(incoming_dir, count=3)

        # Run DRS make
        args = get_default_make_args(incoming_dir, drs_root)
        run(args)

        # Validate DRS structure was created
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "hur"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_make_different_times(self, drs_test_structure):
        """Test DRS creation with files containing different time ranges."""
        incoming_dir = drs_test_structure["incoming"] / "incoming2"
        drs_root = drs_test_structure["root"]

        # Create test files with different time ranges
        create_files_different_times(incoming_dir, count=3)

        # Run DRS make with a different version
        args = get_default_make_args(incoming_dir, drs_root)
        args.version = "v19810102"
        run(args)

        # Validate DRS structure
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_make_different_members(self, drs_test_structure):
        """Test DRS creation with different member IDs."""
        incoming_dir = drs_test_structure["incoming"] / "incoming3"
        drs_root = drs_test_structure["root"]

        # Create test files with different members
        create_files_different_members(incoming_dir, count=3)

        # Run DRS make
        args = get_default_make_args(incoming_dir, drs_root)
        args.version = "v19810103"
        run(args)

        # Validate DRS structure for one of the members
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r2i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_make_different_models(self, drs_test_structure):
        """Test DRS creation with different source models."""
        incoming_dir = drs_test_structure["incoming"] / "incoming4"
        drs_root = drs_test_structure["root"]

        # Create test files with different models
        create_files_different_models(incoming_dir, count=3)

        # Run DRS make
        args = get_default_make_args(incoming_dir, drs_root)
        args.version = "v19810104"
        run(args)

        # Validate DRS structure for one of the models (NESM3)
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "NESM3"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

    def test_make_upgrade_from_latest(self, drs_test_structure):
        """Test DRS make with upgrade_from_latest functionality."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # First, create initial DRS structure
        incoming1 = incoming_dir / "incoming1"
        create_files_different_times(incoming1, count=3)

        args = get_default_make_args(incoming1, drs_root)
        args.version = "v19810101"
        run(args)

        # Now create additional files for upgrade
        incoming2 = incoming_dir / "incoming2"
        create_files_different_times(incoming2, count=3, variable_id="tas")

        # Run upgrade from latest
        args = get_default_make_args(incoming2, drs_root)
        args.version = "v19810102"
        args.upgrade_from_latest = True
        run(args)

        # Validate the upgraded structure
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=True, verbose=False)

    def test_make_empty_directory(self, drs_test_structure):
        """Test DRS make behavior with empty input directory."""
        incoming_dir = drs_test_structure["incoming"] / "empty"
        incoming_dir.mkdir()
        drs_root = drs_test_structure["root"]

        # Run DRS make on empty directory
        args = get_default_make_args(incoming_dir, drs_root)
        run(args)

        # Should not create any DRS structure
        cmip6_dir = drs_root / "CMIP6"
        assert not cmip6_dir.exists() or len(list(cmip6_dir.rglob("*"))) == 0

    def test_make_with_different_copy_modes(self, drs_test_structure):
        """Test DRS make with different file copy modes (copy, link, symlink)."""
        incoming_dir = drs_test_structure["incoming"] / "copy_test"
        drs_root = drs_test_structure["root"]

        # Create test files
        create_files_different_variables(incoming_dir, count=2)

        # Test with symlink mode
        args = get_default_make_args(incoming_dir, drs_root)
        args.copy = False
        args.symlink = True
        run(args)

        # Verify symlinks were created in version directory
        expected_drs_path = (
            drs_root
            / "CMIP6"
            / "CMIP"
            / "IPSL"
            / "IPSL-CM6A-LR"
            / "historical"
            / "r1i1p1f1"
            / "day"
            / "tas"
            / "gn"
        )

        validator = DRSValidator(expected_drs_path)
        assert validator.validate_all(upgrade_from_latest=False, verbose=False)

        # Check that files in version directory are symlinks
        version_dir = expected_drs_path / "v19810101"
        version_files = list(version_dir.glob("*.nc"))
        assert len(version_files) > 0
        for f in version_files:
            assert f.is_symlink(), f"File {f} should be a symlink"

    def test_make_project_mismatch_error(self, drs_test_structure, capfd):
        """Test that DRS make provides clear error message when project mismatches file attributes."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Create test files with CMIP6 attributes
        create_files_different_variables(incoming_dir, count=1)

        # Try to process with wrong project (cmip7 instead of cmip6)
        args = get_default_make_args(incoming_dir, drs_root)
        args.project = "cmip7"  # Wrong project

        # Should raise a SystemExit exception due to errors
        with pytest.raises(SystemExit) as exc_info:
            run(args)

        # The error message is captured in stdout, so we need to check that the process failed
        assert exc_info.value.code == 1  # Should exit with error code 1

        # Capture the output and verify error message content
        captured = capfd.readouterr()
        output = captured.out + captured.err

        # Verify the error message contains expected information
        assert "Project mismatch" in output
        assert "CLI specified 'cmip7'" in output
        assert "file contains 'cmip6'" in output
        assert "Please use '--project cmip6'" in output
        assert "esgvoc status" in output

    def test_make_project_match_succeeds(self, drs_test_structure):
        """Test that DRS make succeeds when project matches file attributes."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Create test files with CMIP6 attributes
        create_files_different_variables(incoming_dir, count=1)

        # Process with correct project (cmip6)
        args = get_default_make_args(incoming_dir, drs_root)
        args.project = "cmip6"  # Correct project

        # Should succeed without raising exception
        run(args)

        # Verify DRS structure was created
        cmip6_dir = drs_root / "CMIP6"
        assert cmip6_dir.exists()

        # Check that some files were processed
        nc_files = list(cmip6_dir.rglob("*.nc"))
        assert len(nc_files) > 0
