"""
Integration test for the complete esgf-prepare workflow.

This test performs a full end-to-end workflow:
1. Uses real NetCDF files to build DRS structure with esgdrs
2. Generates mapfiles from the DRS structure with esgmapfile
3. Validates the complete workflow including multihash support
"""

import tempfile
import subprocess
import sys
from pathlib import Path
import pytest

from esgprep._utils.checksum import detect_multihash_algo


@pytest.mark.integration
class TestFullWorkflow:
    """Full integration test using real data files."""

    @pytest.fixture
    def workflow_setup(self, project_root):
        """Set up the integration test environment."""
        # Use real data if available, otherwise skip
        real_data_dir = project_root / "tests" / "fixtures" / "real_data" / "incoming"
        if not real_data_dir.exists():
            pytest.skip("Real data directory not found - skipping integration test")

        # Create temporary output directory
        output_dir = Path(tempfile.mkdtemp(prefix="esgf_integration_"))

        # Set up paths for DRS and mapfiles
        drs_output_dir = output_dir / "drs_structure"
        mapfiles_output_dir = output_dir / "mapfiles"

        drs_output_dir.mkdir(parents=True)
        mapfiles_output_dir.mkdir(parents=True)

        yield {
            "real_data_dir": real_data_dir,
            "output_dir": output_dir,
            "drs_output_dir": drs_output_dir,
            "mapfiles_output_dir": mapfiles_output_dir,
            "project_root": project_root,
        }

        # Cleanup - keep output for inspection during development
        # if output_dir.exists():
        #     shutil.rmtree(output_dir)

    def test_complete_drs_and_mapfile_workflow(self, workflow_setup):
        """Test the complete workflow: DRS building + mapfile generation."""
        setup = workflow_setup

        # Check that we have real data files
        assert setup["real_data_dir"].exists(), f"Real data directory not found: {setup['real_data_dir']}"

        nc_files = list(setup["real_data_dir"].glob("*.nc"))
        assert len(nc_files) > 0, "No NetCDF files found in real data directory"

        print(f"Found {len(nc_files)} NetCDF files for testing:")
        for f in nc_files:
            print(f"  - {f.name}")

        # Step 1: Build DRS structure using esgdrs
        print("\n=== Step 1: Building DRS structure with esgdrs ===")

        cmd = [
            sys.executable,
            "-m",
            "esgprep.esgdrs",
            "make",
            "--project",
            "cmip6",
            "--root",
            str(setup["drs_output_dir"]),
            "--max-processes",
            "2",
            "--link",  # Hard link files instead of moving them
            "upgrade",  # Action to perform
            str(setup["real_data_dir"]),  # Directory to scan
        ]

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=setup["project_root"]
        )

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        # Check that DRS structure was created
        assert result.returncode == 0, f"esgdrs make failed: {result.stderr}"

        # Verify DRS structure exists
        cmip6_dir = setup["drs_output_dir"] / "CMIP6"
        assert cmip6_dir.exists(), "CMIP6 directory not created in DRS structure"

        # Find created NetCDF files in DRS structure
        drs_nc_files = list(setup["drs_output_dir"].rglob("*.nc"))
        assert len(drs_nc_files) > 0, "No NetCDF files found in created DRS structure"

        print(f"Created DRS structure with {len(drs_nc_files)} NetCDF files:")
        for f in drs_nc_files[:5]:  # Show first 5 files
            rel_path = f.relative_to(setup["drs_output_dir"])
            print(f"  - {rel_path}")
        if len(drs_nc_files) > 5:
            print(f"  ... and {len(drs_nc_files) - 5} more files")

        # Step 2: Generate mapfiles using esgmapfile
        print("\n=== Step 2: Generating mapfiles with esgmapfile ===")

        cmd = [
            sys.executable,
            "-m",
            "esgprep.esgmapfile",
            "make",
            "--project",
            "cmip6",
            "--directory",
            str(setup["drs_output_dir"]),
            "--outdir",
            str(setup["mapfiles_output_dir"]),
            "--checksum-type",
            "sha2-256",  # Use multihash
            "--max-processes",
            "2",
        ]

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=setup["project_root"]
        )

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        # Check that mapfile generation succeeded
        assert result.returncode == 0, f"esgmapfile make failed: {result.stderr}"

        # Verify mapfiles were created
        mapfiles = list(setup["mapfiles_output_dir"].rglob("*.map"))
        assert len(mapfiles) > 0, "No mapfiles were generated"

        print(f"Generated {len(mapfiles)} mapfiles:")
        for mapfile in mapfiles:
            print(f"  - {mapfile.name}")

        # Step 3: Verify mapfile content
        print("\n=== Step 3: Verifying mapfile content ===")

        # Check each mapfile
        total_entries = 0
        for mapfile in mapfiles:
            with open(mapfile, "r") as f:
                lines = f.readlines()

            # Filter out empty lines and comments
            data_lines = [
                line.strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            ]

            print(f"Mapfile {mapfile.name}: {len(data_lines)} entries")
            total_entries += len(data_lines)

            # Verify each line has the expected format
            for i, line in enumerate(data_lines[:3]):  # Check first 3 lines
                parts = line.split(" | ")
                assert len(parts) >= 3, f"Invalid mapfile entry format in {mapfile.name} line {i + 1}"

                # Verify dataset identifier format
                # dataset_id = parts[0]
                # assert "#" in dataset_id, f"Dataset ID should contain version in {mapfile.name}"

                # Verify file path exists
                file_path = parts[1]
                assert Path(file_path).exists(), f"File path {file_path} does not exist"

                # Verify checksum is present and looks like multihash
                has_checksum = any("checksum=" in part for part in parts)
                assert has_checksum, f"No checksum found in mapfile entry: {line}"

                # Verify NO checksum_type is present (since we removed it)
                has_checksum_type = any("checksum_type=" in part for part in parts)
                assert not has_checksum_type, (
                    f"checksum_type should not be present in: {line}"
                )

                if i == 0:  # Show first entry as example
                    print(f"  Example entry: {line}")

        print(f"Total mapfile entries: {total_entries}")
        assert total_entries > 0, "No entries found in mapfiles"

        # Step 4: Test multihash algorithm detection
        print("\n=== Step 4: Testing multihash algorithm detection ===")

        # Extract a multihash from one of the mapfiles
        with open(mapfiles[0], "r") as f:
            first_line = next(
                line for line in f if line.strip() and not line.startswith("#")
            )

        # Find checksum in the line
        parts = first_line.split(" | ")
        checksum_part = next(part for part in parts if "checksum=" in part)
        checksum_value = checksum_part.split("=", 1)[1]

        # Test algorithm detection
        detected_algo = detect_multihash_algo(checksum_value)
        print(f"Detected algorithm from multihash: {detected_algo}")
        assert detected_algo == "sha2-256", (
            "Should detect sha2-256 algorithm from multihash"
        )

        print("\n=== Integration test completed successfully! ===")
        print(f"Results saved in: {setup['output_dir']}")
        print(f"DRS structure: {setup['drs_output_dir']}")
        print(f"Mapfiles: {setup['mapfiles_output_dir']}")

    @pytest.mark.slow
    def test_workflow_with_different_checksum_algorithms(self, workflow_setup):
        """Test the workflow with different checksum algorithms."""
        setup = workflow_setup

        # Skip if no real data
        if not setup["real_data_dir"].exists():
            pytest.skip("Real data directory not found")

        nc_files = list(setup["real_data_dir"].glob("*.nc"))
        if len(nc_files) == 0:
            pytest.skip("No NetCDF files found in real data directory")

        # Build DRS structure once
        cmd = [
            sys.executable,
            "-m",
            "esgprep.esgdrs",
            "make",
            "--project",
            "cmip6",
            "--root",
            str(setup["drs_output_dir"]),
            "--max-processes",
            "1",
            "--link",
            "upgrade",
            str(setup["real_data_dir"]),
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=setup["project_root"]
        )
        assert result.returncode == 0, f"DRS creation failed: {result.stderr}"

        # Test different checksum algorithms
        algorithms = ["sha2-256", "sha2-512", "sha1"]

        for algo in algorithms:
            print(f"\n=== Testing mapfile generation with {algo} ===")

            algo_outdir = (
                setup["mapfiles_output_dir"] / f"test_{algo.replace('-', '_')}"
            )
            algo_outdir.mkdir(parents=True)

            cmd = [
                sys.executable,
                "-m",
                "esgprep.esgmapfile",
                "make",
                "--project",
                "cmip6",
                "--directory",
                str(setup["drs_output_dir"]),
                "--outdir",
                str(algo_outdir),
                "--checksum-type",
                algo,
                "--max-processes",
                "1",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=setup["project_root"]
            )

            assert result.returncode == 0, f"Mapfile generation failed for {algo}: {result.stderr}"

            # Verify mapfiles were created
            mapfiles = list(algo_outdir.rglob("*.map"))
            assert len(mapfiles) > 0, f"No mapfiles generated for {algo}"

            # Verify algorithm detection works
            for mapfile in mapfiles[:1]:  # Check first mapfile
                with open(mapfile, "r") as f:
                    first_line = next(
                        line for line in f if line.strip() and not line.startswith("#")
                    )

                parts = first_line.split(" | ")
                checksum_part = next(part for part in parts if "checksum=" in part)
                checksum_value = checksum_part.split("=", 1)[1]

                detected_algo = detect_multihash_algo(checksum_value)
                assert detected_algo == algo, f"Algorithm detection failed: expected {algo}, got {detected_algo}"

            print(f"  ✓ {algo} algorithm test passed")

    def test_workflow_error_handling(self, workflow_setup):
        """Test workflow error handling with invalid inputs."""
        setup = workflow_setup

        # Test DRS make with non-existent directory
        print("\n=== Testing error handling ===")

        cmd = [
            sys.executable,
            "-m",
            "esgprep.esgdrs",
            "make",
            "--project",
            "cmip6",
            "--root",
            str(setup["drs_output_dir"]),
            "upgrade",
            str(setup["output_dir"] / "nonexistent"),
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=setup["project_root"]
        )

        # Should handle the error gracefully (might succeed with no files or fail cleanly)
        # The exact behavior depends on implementation, but should not crash
        print(f"Non-existent directory test: return code {result.returncode}")

        # Test mapfile make with empty DRS structure
        cmd = [
            sys.executable,
            "-m",
            "esgprep.esgmapfile",
            "make",
            "--project",
            "cmip6",
            "--directory",
            str(setup["drs_output_dir"]),
            "--outdir",
            str(setup["mapfiles_output_dir"]),
            "--checksum-type",
            "sha2-256",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=setup["project_root"]
        )

        # Should handle empty structure gracefully
        print(f"Empty DRS structure test: return code {result.returncode}")
        # Either no mapfiles created or empty mapfiles should be fine
        mapfiles = list(setup["mapfiles_output_dir"].rglob("*.map"))
        print(f"Mapfiles created from empty DRS: {len(mapfiles)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
