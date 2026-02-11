"""
Integration tests for multihash functionality across the esgf-prepare workflow.

Tests that multihash checksums work correctly from DRS creation through
mapfile generation, ensuring end-to-end compatibility.
"""

import subprocess
import sys
from pathlib import Path
import pytest

from esgprep.esgdrs import run as drs_run
from esgprep.esgmapfile import run as mapfile_run
from esgprep._utils.checksum import detect_multihash_algo, multihash_hex
from tests.fixtures.generators import create_files_different_variables


def get_default_make_args(incoming_dir, drs_root):
    """Get default arguments for DRS make command."""
    import re
    from argparse import Namespace

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


def get_default_mapfile_args(drs_root, outdir):
    """Get default arguments for mapfile make command."""
    import re
    from argparse import Namespace

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


@pytest.mark.integration
class TestMultihashIntegration:
    """Integration tests for multihash functionality."""

    def test_multihash_end_to_end_workflow(self, drs_test_structure):
        """Test complete workflow with multihash from DRS creation to mapfile generation."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]
        mapfile_outdir = drs_test_structure["tmp_dir"] / "mapfiles"
        mapfile_outdir.mkdir(parents=True)

        # Step 1: Create test NetCDF files
        created_files = create_files_different_variables(incoming_dir, count=2)
        assert len(created_files) > 0, "No test files were created"

        # Step 2: Build DRS structure
        drs_args = get_default_make_args(incoming_dir, drs_root)
        drs_run(drs_args)

        # Verify DRS was created
        drs_nc_files = list(drs_root.rglob("*.nc"))
        assert len(drs_nc_files) > 0, "No NetCDF files found in DRS structure"

        # Step 3: Generate mapfiles with multihash
        mapfile_args = get_default_mapfile_args(drs_root, mapfile_outdir)
        mapfile_run(mapfile_args)

        # Step 4: Verify mapfiles were created with multihash checksums
        mapfiles = list(mapfile_outdir.rglob("*.map"))
        assert len(mapfiles) > 0, "No mapfiles were generated"

        verified_multihash_count = 0
        for mapfile in mapfiles:
            with open(mapfile, "r") as f:
                content = f.read()

            data_lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.startswith("#")
            ]

            for line in data_lines:
                parts = line.split(" | ")
                assert len(parts) >= 3, f"Invalid mapfile format: {line}"

                # Extract checksum
                checksum_part = next((p for p in parts if "checksum=" in p), None)
                assert checksum_part is not None, (
                    f"No checksum in mapfile entry: {line}"
                )

                checksum_value = checksum_part.split("=", 1)[1]

                # Verify it's a valid multihash
                detected_algo = detect_multihash_algo(checksum_value)
                assert detected_algo == "sha2-256", (
                    f"Expected sha2-256, got {detected_algo}"
                )

                verified_multihash_count += 1

        assert verified_multihash_count > 0, "No multihash checksums were verified"
        print(f"✓ Verified {verified_multihash_count} multihash checksums in mapfiles")

    def test_multihash_consistency_across_runs(self, drs_test_structure):
        """Test that multihash checksums are consistent across multiple runs."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]
        mapfile_outdir1 = drs_test_structure["tmp_dir"] / "mapfiles1"
        mapfile_outdir2 = drs_test_structure["tmp_dir"] / "mapfiles2"
        mapfile_outdir1.mkdir(parents=True)
        mapfile_outdir2.mkdir(parents=True)

        # Create test files
        create_files_different_variables(incoming_dir, count=1)

        # Build DRS structure
        drs_args = get_default_make_args(incoming_dir, drs_root)
        drs_run(drs_args)

        # Generate mapfiles twice with same settings
        for outdir in [mapfile_outdir1, mapfile_outdir2]:
            mapfile_args = get_default_mapfile_args(drs_root, outdir)
            mapfile_run(mapfile_args)

        # Compare checksums between the two runs
        mapfiles1 = list(mapfile_outdir1.rglob("*.map"))
        mapfiles2 = list(mapfile_outdir2.rglob("*.map"))

        assert len(mapfiles1) == len(mapfiles2), (
            "Different number of mapfiles generated"
        )

        # Extract checksums from both runs
        checksums1 = self._extract_checksums_from_mapfiles(mapfiles1)
        checksums2 = self._extract_checksums_from_mapfiles(mapfiles2)

        assert checksums1 == checksums2, "Checksums differ between runs"
        print(f"✓ Verified consistency of {len(checksums1)} checksums across runs")

    def test_different_multihash_algorithms(self, drs_test_structure):
        """Test that different multihash algorithms produce different but valid results."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]

        # Create test files and DRS structure
        create_files_different_variables(incoming_dir, count=1)
        drs_args = get_default_make_args(incoming_dir, drs_root)
        drs_run(drs_args)

        algorithms = ["sha2-256", "sha2-512", "sha1"]
        algorithm_checksums = {}

        for algo in algorithms:
            outdir = (
                drs_test_structure["tmp_dir"] / f"mapfiles_{algo.replace('-', '_')}"
            )
            outdir.mkdir(parents=True)

            # Generate mapfiles with specific algorithm
            mapfile_args = get_default_mapfile_args(drs_root, outdir)
            mapfile_args.checksum_type = algo
            mapfile_run(mapfile_args)

            # Extract and verify checksums
            mapfiles = list(outdir.rglob("*.map"))
            assert len(mapfiles) > 0, f"No mapfiles generated for {algo}"

            checksums = self._extract_checksums_from_mapfiles(mapfiles)
            assert len(checksums) > 0, f"No checksums extracted for {algo}"

            # Verify algorithm detection
            for checksum in checksums:
                detected = detect_multihash_algo(checksum)
                assert detected == algo, (
                    f"Wrong algorithm detected for {algo}: {detected}"
                )

            algorithm_checksums[algo] = checksums

        # Verify that different algorithms produce different checksums
        algo_list = list(algorithms)
        for i in range(len(algo_list)):
            for j in range(i + 1, len(algo_list)):
                algo1, algo2 = algo_list[i], algo_list[j]
                checksums1 = set(algorithm_checksums[algo1])
                checksums2 = set(algorithm_checksums[algo2])

                # Should have no overlap (different algorithms, different checksums)
                overlap = checksums1.intersection(checksums2)
                assert len(overlap) == 0, (
                    f"Algorithms {algo1} and {algo2} produced identical checksums"
                )

        print(f"✓ Verified different checksums for {len(algorithms)} algorithms")

    def test_multihash_validation_with_real_files(self, drs_test_structure):
        """Test that multihash checksums can be validated against actual file content."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]
        mapfile_outdir = drs_test_structure["tmp_dir"] / "mapfiles"
        mapfile_outdir.mkdir(parents=True)

        # Create test files
        # created_files = create_files_different_variables(incoming_dir, count=1)

        # Build DRS structure
        drs_args = get_default_make_args(incoming_dir, drs_root)
        drs_run(drs_args)

        # Generate mapfiles
        mapfile_args = get_default_mapfile_args(drs_root, mapfile_outdir)
        mapfile_args.checksum_type = "sha2-256"
        mapfile_run(mapfile_args)

        # Find the actual files in DRS structure
        drs_files = list(drs_root.rglob("*.nc"))
        assert len(drs_files) > 0, "No files found in DRS structure"

        # Extract checksums from mapfiles
        mapfiles = list(mapfile_outdir.rglob("*.map"))
        file_checksums = {}

        for mapfile in mapfiles:
            with open(mapfile, "r") as f:
                content = f.read()

            data_lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.startswith("#")
            ]

            for line in data_lines:
                parts = line.split(" | ")
                file_path = Path(parts[1])
                checksum_part = next((p for p in parts if "checksum=" in p), None)
                if checksum_part:
                    checksum = checksum_part.split("=", 1)[1]
                    file_checksums[file_path] = checksum

        # Validate checksums by recomputing them
        validated_count = 0
        for file_path, expected_checksum in file_checksums.items():
            if file_path.exists():
                # Read file content and compute multihash
                with open(file_path, "rb") as f:
                    file_content = f.read()

                computed_checksum = multihash_hex(file_content, "sha2-256")
                assert computed_checksum == expected_checksum, (
                    f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {computed_checksum}"
                )
                validated_count += 1

        assert validated_count > 0, "No checksums were validated"
        print(f"✓ Validated {validated_count} file checksums against actual content")

    def _extract_checksums_from_mapfiles(self, mapfiles):
        """Helper method to extract checksums from mapfiles."""
        checksums = []
        for mapfile in mapfiles:
            with open(mapfile, "r") as f:
                content = f.read()

            data_lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.startswith("#")
            ]

            for line in data_lines:
                parts = line.split(" | ")
                checksum_part = next((p for p in parts if "checksum=" in p), None)
                if checksum_part:
                    checksum = checksum_part.split("=", 1)[1]
                    checksums.append(checksum)

        return checksums

    def test_command_line_integration(self, drs_test_structure, project_root):
        """Test multihash functionality through command line interface."""
        incoming_dir = drs_test_structure["incoming"]
        drs_root = drs_test_structure["root"]
        mapfile_outdir = drs_test_structure["tmp_dir"] / "mapfiles"
        mapfile_outdir.mkdir(parents=True)

        # Create test files
        create_files_different_variables(incoming_dir, count=1)

        # Run DRS make via command line
        drs_cmd = [
            sys.executable,
            "-m",
            "esgprep.esgdrs",
            "make",
            "--project",
            "cmip6",
            "--root",
            str(drs_root),
            "upgrade",
            str(incoming_dir),
        ]

        result = subprocess.run(
            drs_cmd, capture_output=True, text=True, cwd=project_root
        )
        assert result.returncode == 0, f"DRS command failed: {result.stderr}"

        # Run mapfile make via command line with multihash
        mapfile_cmd = [
            sys.executable,
            "-m",
            "esgprep.esgmapfile",
            "make",
            "--project",
            "cmip6",
            "--directory",
            str(drs_root),
            "--outdir",
            str(mapfile_outdir),
            "--checksum-type",
            "sha2-256",
        ]

        result = subprocess.run(
            mapfile_cmd, capture_output=True, text=True, cwd=project_root
        )
        assert result.returncode == 0, f"Mapfile command failed: {result.stderr}"

        # Verify multihash checksums in output
        mapfiles = list(mapfile_outdir.rglob("*.map"))
        assert len(mapfiles) > 0, "No mapfiles generated via command line"

        multihash_count = 0
        for mapfile in mapfiles:
            with open(mapfile, "r") as f:
                content = f.read()

            data_lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.startswith("#")
            ]

            for line in data_lines:
                if "checksum=" in line:
                    parts = line.split(" | ")
                    checksum_part = next((p for p in parts if "checksum=" in p), None)
                    if checksum_part:
                        checksum = checksum_part.split("=", 1)[1]
                        algo = detect_multihash_algo(checksum)
                        assert algo == "sha2-256", f"Wrong algorithm: {algo}"
                        multihash_count += 1

        assert multihash_count > 0, (
            "No multihash checksums found in command line output"
        )
        print(
            f"✓ Verified {multihash_count} multihash checksums via command line interface"
        )
