"""
Unit tests for mapfile make functionality.

Tests the core functionality of creating mapfiles from DRS structures
using the esgmapfile make command.
"""

import re
from argparse import Namespace
from pathlib import Path
import pytest

from esgprep.esgmapfile import run as mapfile_run
from esgprep.esgdrs import run as drs_run
from tests.fixtures.generators import (
    create_files_different_variables,
    clean_directory,
)


def get_default_drs_args(incoming_dir, drs_root) -> Namespace:
    """Get default arguments for DRS make command."""
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


def get_default_mapfile_args(drs_root, outdir) -> Namespace:
    """Get default arguments for mapfile make command."""
    return Namespace(
        cmd="make",
        log=None,
        debug=False,
        directory=[str(drs_root)],
        project="cmip6",
        mapfile="{dataset_id}.v{version}.map",
        outdir=str(outdir),
        all_versions=False,
        version=None,
        latest_symlink=False,
        ignore_dir=re.compile("^.*/(files|\\.[\\w]*).*$"),
        include_file=["^.*\\.nc$"],
        exclude_file=["^\\..*$"],
        max_processes=1,
        color=False,
        no_color=False,
        no_checksum=False,
        checksum_type="sha2-256",
        checksums_from=None,
        tech_notes_url=None,
        tech_notes_title=None,
        no_cleanup=False,
        quiet=False,
        prog="esgmapfile",
    )


class TestMapfileMake:
    """Test class for mapfile make functionality."""

    def test_mapfile_creation_basic(self, drs_test_structure):
        """Test basic mapfile creation from DRS structure."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]
        mapfile_outdir = drs_test_structure["tmp_dir"] / "mapfiles"
        mapfile_outdir.mkdir(parents=True)

        # Step 1: Create DRS structure
        create_files_different_variables(incoming_dir, count=2)
        drs_args = get_default_drs_args(incoming_dir, drs_root)
        drs_run(drs_args)

        # Step 2: Generate mapfiles
        mapfile_args = get_default_mapfile_args(drs_root, mapfile_outdir)
        mapfile_run(mapfile_args)

        # Step 3: Verify mapfiles were created
        mapfiles = list(mapfile_outdir.rglob("*.map"))
        assert len(mapfiles) > 0, "No mapfiles were generated"

        # Step 4: Verify mapfile content
        for mapfile in mapfiles:
            assert mapfile.exists(), f"Mapfile does not exist: {mapfile}"

            with open(mapfile, "r") as f:
                content = f.read()

            # Should contain some data lines (not just comments)
            data_lines = [
                line.strip() for line in content.split('\n')
                if line.strip() and not line.startswith('#')
            ]
            assert len(data_lines) > 0, f"Mapfile {mapfile} contains no data entries"

    def test_mapfile_with_multihash(self, drs_test_structure):
        """Test mapfile creation with multihash checksums."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]
        mapfile_outdir = drs_test_structure["tmp_dir"] / "mapfiles"
        mapfile_outdir.mkdir(parents=True)

        # Step 1: Create DRS structure
        create_files_different_variables(incoming_dir, count=1)
        drs_args = get_default_drs_args(incoming_dir, drs_root)
        drs_run(drs_args)

        # Step 2: Generate mapfiles with multihash
        mapfile_args = get_default_mapfile_args(drs_root, mapfile_outdir)
        mapfile_args.checksum_type = "sha2-256"  # Use multihash
        mapfile_run(mapfile_args)

        # Step 3: Verify mapfiles contain multihash checksums
        mapfiles = list(mapfile_outdir.rglob("*.map"))
        assert len(mapfiles) > 0, "No mapfiles were generated"

        for mapfile in mapfiles:
            with open(mapfile, "r") as f:
                content = f.read()

            # Find data lines with checksums
            data_lines = [
                line.strip() for line in content.split('\n')
                if line.strip() and not line.startswith('#')
            ]

            assert len(data_lines) > 0, "No data entries found"

            # Verify checksum format in data lines
            for line in data_lines:
                parts = line.split(" | ")
                assert len(parts) >= 3, f"Invalid mapfile entry format: {line}"

                # Find checksum field
                has_checksum = any("checksum=" in part for part in parts)
                assert has_checksum, f"No checksum found in entry: {line}"

                # Verify NO checksum_type is present (since we removed it)
                has_checksum_type = any("checksum_type=" in part for part in parts)
                assert not has_checksum_type, f"checksum_type should not be present: {line}"

    def test_mapfile_different_checksum_types(self, drs_test_structure):
        """Test mapfile creation with different checksum algorithms."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]
        mapfile_outdir = drs_test_structure["tmp_dir"] / "mapfiles"
        mapfile_outdir.mkdir(parents=True)

        # Create DRS structure once
        create_files_different_variables(incoming_dir, count=1)
        drs_args = get_default_drs_args(incoming_dir, drs_root)
        drs_run(drs_args)

        # Test different checksum algorithms
        algorithms = ["sha2-256", "sha2-512", "sha1"]

        for algo in algorithms:
            algo_outdir = mapfile_outdir / f"test_{algo.replace('-', '_')}"
            algo_outdir.mkdir(parents=True)

            # Generate mapfiles with specific algorithm
            mapfile_args = get_default_mapfile_args(drs_root, algo_outdir)
            mapfile_args.checksum_type = algo
            mapfile_run(mapfile_args)

            # Verify mapfiles were created
            mapfiles = list(algo_outdir.rglob("*.map"))
            assert len(mapfiles) > 0, f"No mapfiles generated for {algo}"

            # Verify content has checksums
            for mapfile in mapfiles:
                with open(mapfile, "r") as f:
                    content = f.read()

                data_lines = [
                    line.strip() for line in content.split('\n')
                    if line.strip() and not line.startswith('#')
                ]

                assert len(data_lines) > 0, f"No data in mapfile for {algo}"

                # Check that all lines have checksums
                for line in data_lines:
                    has_checksum = any("checksum=" in part for part in line.split(" | "))
                    assert has_checksum, f"Missing checksum in {algo} mapfile: {line}"

    def test_mapfile_empty_drs(self, drs_test_structure):
        """Test mapfile creation behavior with empty DRS structure."""
        drs_root = drs_test_structure["root"]
        mapfile_outdir = drs_test_structure["tmp_dir"] / "mapfiles"
        mapfile_outdir.mkdir(parents=True)

        # Try to generate mapfiles from empty DRS
        mapfile_args = get_default_mapfile_args(drs_root, mapfile_outdir)
        mapfile_run(mapfile_args)

        # Should not create any mapfiles or should create empty ones
        mapfiles = list(mapfile_outdir.rglob("*.map"))
        # Either no mapfiles created, or they're empty
        if mapfiles:
            for mapfile in mapfiles:
                with open(mapfile, "r") as f:
                    content = f.read()
                data_lines = [
                    line.strip() for line in content.split('\n')
                    if line.strip() and not line.startswith('#')
                ]
                assert len(data_lines) == 0, f"Unexpected data in mapfile from empty DRS: {mapfile}"

    def test_mapfile_dataset_names(self, drs_test_structure):
        """Test that mapfile names follow correct dataset naming convention."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]
        mapfile_outdir = drs_test_structure["tmp_dir"] / "mapfiles"
        mapfile_outdir.mkdir(parents=True)

        # Create DRS structure
        create_files_different_variables(incoming_dir, count=2)
        drs_args = get_default_drs_args(incoming_dir, drs_root)
        drs_run(drs_args)

        # Generate mapfiles
        mapfile_args = get_default_mapfile_args(drs_root, mapfile_outdir)
        mapfile_run(mapfile_args)

        # Verify mapfile naming convention
        mapfiles = list(mapfile_outdir.rglob("*.map"))
        assert len(mapfiles) > 0, "No mapfiles were generated"

        for mapfile in mapfiles:
            # Mapfile names should follow CMIP6 dataset naming convention
            filename = mapfile.name
            assert filename.endswith('.map'), f"Mapfile should end with .map: {filename}"

            # Should contain project and other DRS elements
            assert 'CMIP6' in filename, f"Mapfile name should contain CMIP6: {filename}"